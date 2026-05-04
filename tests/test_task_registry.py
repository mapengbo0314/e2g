"""Tests for the TaskRegistry (SM-202, SM-203 coverage).

Proves:
  1. Multi-repo isolation with composite keys
  2. Persistence across connection close/reopen
  3. Pruning of old terminal records
  4. Cancel status transition
  5. Context manager lifecycle
  6. Stale task detection support (updated_at tracking)
"""

import os
import tempfile
import time
import datetime
import pytest

from harness.task_registry import TaskRegistry, TaskRecord


@pytest.fixture
def registry_path(tmp_path):
    """Creates a temp path for a test registry database."""
    return str(tmp_path / "test_registry.sqlite")


@pytest.fixture
def registry(registry_path):
    """Creates a fresh TaskRegistry for each test."""
    reg = TaskRegistry(db_path=registry_path)
    yield reg
    reg.close()


class TestTaskRegistryBasic:
    """Basic CRUD operations."""

    def test_register_and_get(self, registry):
        """Register a task and retrieve it by composite key."""
        record = registry.register("thread-1", "/repo/a")
        assert record.thread_id == "thread-1"
        assert record.index_dir == "/repo/a"
        assert record.status == "running"

        fetched = registry.get("thread-1", "/repo/a")
        assert fetched is not None
        assert fetched.thread_id == "thread-1"
        assert fetched.status == "running"

    def test_get_nonexistent_returns_none(self, registry):
        """Querying a nonexistent task returns None, not an exception."""
        assert registry.get("nonexistent", "/repo/x") is None

    def test_update_status(self, registry):
        """Update a task's status and verify the change persists."""
        registry.register("thread-1", "/repo/a")
        registry.update("thread-1", "/repo/a", status="completed", current_step="verifier:passed")

        fetched = registry.get("thread-1", "/repo/a")
        assert fetched.status == "completed"
        assert fetched.current_step == "verifier:passed"

    def test_update_step_history(self, registry):
        """Step history is stored as JSON and round-trips correctly."""
        registry.register("thread-1", "/repo/a")
        history = ["planner:planned", "architect:architected", "reviewer:review_failed"]
        registry.update("thread-1", "/repo/a", step_history=history)

        fetched = registry.get("thread-1", "/repo/a")
        assert fetched.step_history == history

    def test_updated_at_changes_on_update(self, registry):
        """updated_at timestamp advances with each update call."""
        registry.register("thread-1", "/repo/a")
        r1 = registry.get("thread-1", "/repo/a")

        time.sleep(0.05)  # Small delay to ensure timestamp differs
        registry.update("thread-1", "/repo/a", status="suspended")
        r2 = registry.get("thread-1", "/repo/a")

        assert r2.updated_at > r1.updated_at


class TestMultiRepoIsolation:
    """Composite key isolation across repos."""

    def test_two_repos_same_thread_id(self, registry):
        """Same thread_id on different repos are independent records."""
        registry.register("thread-1", "/repo/a")
        registry.register("thread-1", "/repo/b")

        a = registry.get("thread-1", "/repo/a")
        b = registry.get("thread-1", "/repo/b")
        assert a is not None
        assert b is not None
        assert a.index_dir == "/repo/a"
        assert b.index_dir == "/repo/b"

    def test_list_all_repos(self, registry):
        """list() without index_dir returns tasks from all repos."""
        registry.register("t1", "/repo/a")
        registry.register("t2", "/repo/b")

        all_tasks = registry.list()
        thread_ids = {t.thread_id for t in all_tasks}
        assert thread_ids == {"t1", "t2"}

    def test_list_filtered_by_repo(self, registry):
        """list() with index_dir returns only that repo's tasks."""
        registry.register("t1", "/repo/a")
        registry.register("t2", "/repo/b")

        a_tasks = registry.list(index_dir="/repo/a")
        assert len(a_tasks) == 1
        assert a_tasks[0].thread_id == "t1"

    def test_list_filtered_by_status(self, registry):
        """list() with status_filter returns only matching tasks."""
        registry.register("t1", "/repo/a")
        registry.register("t2", "/repo/a")
        registry.update("t1", "/repo/a", status="suspended")

        suspended = registry.list(status_filter="suspended")
        assert len(suspended) == 1
        assert suspended[0].thread_id == "t1"


class TestPersistence:
    """Data survives connection close/reopen."""

    def test_persistence_across_restart(self, registry_path):
        """Register a task, close the registry, reopen, and verify data survives."""
        # First connection: register
        reg1 = TaskRegistry(db_path=registry_path)
        reg1.register("persist-thread", "/repo/persist")
        reg1.update("persist-thread", "/repo/persist", status="suspended", escalation_reason="test reason")
        reg1.close()

        # Second connection: query
        reg2 = TaskRegistry(db_path=registry_path)
        fetched = reg2.get("persist-thread", "/repo/persist")
        reg2.close()

        assert fetched is not None
        assert fetched.status == "suspended"
        assert fetched.escalation_reason == "test reason"


class TestCancelAndPrune:
    """Cancel and prune operations."""

    def test_cancel_sets_status(self, registry):
        """cancel() transitions status to 'cancelled'."""
        registry.register("t1", "/repo/a")
        registry.cancel("t1", "/repo/a")

        fetched = registry.get("t1", "/repo/a")
        assert fetched.status == "cancelled"

    def test_prune_removes_old_terminal_records(self, registry):
        """prune() deletes completed/failed/cancelled records older than max_age."""
        registry.register("old-task", "/repo/a")
        registry.update("old-task", "/repo/a", status="completed")

        # Manually backdate the updated_at to 2 days ago
        two_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=48)).isoformat()
        registry.conn.execute(
            "UPDATE harness_tasks SET updated_at = ? WHERE thread_id = ?",
            (two_days_ago, "old-task")
        )
        registry.conn.commit()

        # Register a fresh task that should NOT be pruned
        registry.register("new-task", "/repo/a")

        deleted = registry.prune(max_age_hours=24)
        assert deleted == 1

        assert registry.get("old-task", "/repo/a") is None
        assert registry.get("new-task", "/repo/a") is not None

    def test_prune_preserves_running_and_suspended(self, registry):
        """prune() does NOT remove running or suspended tasks regardless of age."""
        registry.register("running-task", "/repo/a")
        registry.register("suspended-task", "/repo/a2")
        registry.update("suspended-task", "/repo/a2", status="suspended")

        # Backdate both
        old_time = (datetime.datetime.utcnow() - datetime.timedelta(hours=48)).isoformat()
        registry.conn.execute("UPDATE harness_tasks SET updated_at = ?", (old_time,))
        registry.conn.commit()

        deleted = registry.prune(max_age_hours=1)
        assert deleted == 0  # Neither should be pruned


class TestContextManager:
    """Context manager lifecycle."""

    def test_context_manager_closes_connection(self, registry_path):
        """Using 'with' closes the connection on exit."""
        with TaskRegistry(db_path=registry_path) as reg:
            reg.register("cm-thread", "/repo/cm")
            fetched = reg.get("cm-thread", "/repo/cm")
            assert fetched is not None

        # After exit, connection should be None
        assert reg.conn is None

    def test_context_manager_persists_data(self, registry_path):
        """Data written inside 'with' block persists after exit."""
        with TaskRegistry(db_path=registry_path) as reg:
            reg.register("cm-persist", "/repo/cm")

        # Reopen and verify
        with TaskRegistry(db_path=registry_path) as reg2:
            fetched = reg2.get("cm-persist", "/repo/cm")
            assert fetched is not None
            assert fetched.status == "running"
