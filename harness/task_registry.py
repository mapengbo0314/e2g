"""Global Task Registry for the Unified Harness.

Persists task metadata in a global SQLite database at ~/.harness/task_registry.sqlite,
separate from the per-repo LangGraph checkpointer. This ensures task discoverability
across repos and process restarts.

Thread-safety: The connection is opened with check_same_thread=False and WAL journal
mode. Background threads (_run_orchestrator_sync) should create their own short-lived
TaskRegistry instances for writes, not share the event-loop-owned instance.
"""

import os
import sqlite3
import json
import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional, List


# Default global location for the registry database.
DEFAULT_REGISTRY_DIR = os.path.expanduser("~/.harness")
DEFAULT_REGISTRY_PATH = os.path.join(DEFAULT_REGISTRY_DIR, "task_registry.sqlite")


@dataclass
class TaskRecord:
    """Represents a single harness task's metadata."""
    thread_id: str
    index_dir: str
    status: str                           # running | completed | failed | suspended | cancelled
    started_at: str                       # ISO 8601 timestamp
    updated_at: str                       # ISO 8601 timestamp
    current_step: str = ""
    step_history: list = field(default_factory=list)
    error: str = ""
    escalation_reason: str = ""
    artifacts_produced: str = ""


class TaskRegistry:
    """Persistent, global task registry backed by SQLite.

    Supports composite (index_dir, thread_id) keys for multi-repo isolation.
    The Ollama parallelism guard queries this registry across all repos.
    """

    # Only these columns may be updated via update(). Prevents accidental
    # overwrites of primary key fields (thread_id, index_dir, started_at).
    UPDATABLE_FIELDS = frozenset({
        "status", "current_step", "step_history",
        "error", "escalation_reason", "artifacts_produced"
    })

    def __init__(self, db_path: str = DEFAULT_REGISTRY_PATH):
        """Opens (or creates) the registry database.

        Args:
            db_path: Absolute path to the SQLite file. Defaults to
                     ~/.harness/task_registry.sqlite. Parent directory is
                     created automatically.
        """
        # Ensure the parent directory exists. expanduser is already applied
        # in the default, but callers may pass custom paths.
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # WAL mode: allows concurrent readers while a writer is active,
        # unlike the default rollback journal which blocks all readers
        # during writes. busy_timeout retries for up to 5s on lock contention.
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self._create_table()

    def _create_table(self):
        """Creates the harness_tasks table if it doesn't exist."""
        # Try to add the column if it doesn't exist (for existing DBs)
        try:
            self.conn.execute("ALTER TABLE harness_tasks ADD COLUMN artifacts_produced TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass # Column likely already exists

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS harness_tasks (
                thread_id     TEXT NOT NULL,
                index_dir     TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'running',
                started_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                current_step  TEXT DEFAULT '',
                step_history  TEXT DEFAULT '[]',
                error         TEXT DEFAULT '',
                escalation_reason TEXT DEFAULT '',
                artifacts_produced TEXT DEFAULT '',
                PRIMARY KEY (index_dir, thread_id)
            )
        """)
        self.conn.commit()

    def register(self, thread_id: str, index_dir: str, force: bool = False) -> TaskRecord:
        """Inserts a new task record and returns it.

        If a record with the same (index_dir, thread_id) already exists:
          - If it is 'suspended' and force=False, raises ValueError to
            prevent accidental loss of escalation state.
          - Otherwise, replaces the existing record.
        """
        # Guard against silently nuking a suspended task's state
        if not force:
            existing = self.get(thread_id, index_dir)
            if existing and existing.status == "suspended":
                raise ValueError(
                    f"Task {thread_id} is suspended. Use force=True to override."
                )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.conn.execute("""
            INSERT OR REPLACE INTO harness_tasks
                (thread_id, index_dir, status, started_at, updated_at)
            VALUES (?, ?, 'running', ?, ?)
        """, (thread_id, index_dir, now, now))
        self.conn.commit()
        return TaskRecord(
            thread_id=thread_id, index_dir=index_dir,
            status="running", started_at=now, updated_at=now
        )

    def update(self, thread_id: str, index_dir: str, **kwargs) -> None:
        """Updates fields on an existing task record.

        Automatically sets `updated_at` to now. Accepted kwargs are
        restricted to UPDATABLE_FIELDS to prevent accidental PK overwrites.
        """
        if not kwargs:
            return

        # Validate against whitelist to prevent PK corruption
        invalid = set(kwargs) - self.UPDATABLE_FIELDS
        if invalid:
            raise ValueError(f"Cannot update non-whitelisted fields: {invalid}")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        kwargs["updated_at"] = now

        # step_history is stored as JSON text in SQLite
        if "step_history" in kwargs and isinstance(kwargs["step_history"], list):
            kwargs["step_history"] = json.dumps(kwargs["step_history"])

        set_clauses = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [index_dir, thread_id]
        self.conn.execute(
            f"UPDATE harness_tasks SET {set_clauses} WHERE index_dir = ? AND thread_id = ?",
            values
        )
        self.conn.commit()

    def get(self, thread_id: str, index_dir: str) -> Optional[TaskRecord]:
        """Returns a single TaskRecord or None if not found."""
        row = self.conn.execute(
            "SELECT * FROM harness_tasks WHERE index_dir = ? AND thread_id = ?",
            (index_dir, thread_id)
        ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def list(self, index_dir: str = None, status_filter: str = None) -> List[TaskRecord]:
        """Returns filtered task records. Read-only, no side effects.

        Args:
            index_dir: If provided, only return tasks for this repo.
            status_filter: If provided, only return tasks with this status.
        """
        query = "SELECT * FROM harness_tasks WHERE 1=1"
        params: list = []

        if index_dir is not None:
            query += " AND index_dir = ?"
            params.append(index_dir)
        if status_filter is not None:
            query += " AND status = ?"
            params.append(status_filter)

        query += " ORDER BY updated_at DESC"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def cancel(self, thread_id: str, index_dir: str) -> None:
        """Sets a task's status to cancelled."""
        self.update(thread_id, index_dir, status="cancelled")

    def prune(self, max_age_hours: int = 24) -> int:
        """Removes terminal records (completed, failed, cancelled) older than max_age_hours.

        Returns the number of rows deleted. Called during initialize or via --prune,
        never implicitly during reads.
        """
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=max_age_hours)
        ).isoformat()
        cursor = self.conn.execute(
            "DELETE FROM harness_tasks WHERE status IN ('completed', 'failed', 'cancelled') AND updated_at < ?",
            (cutoff,)
        )
        self.conn.commit()
        return cursor.rowcount

    def close(self):
        """Closes the SQLite connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _row_to_record(self, row: sqlite3.Row) -> TaskRecord:
        """Converts a sqlite3.Row to a TaskRecord dataclass."""
        step_history_raw = row["step_history"]
        try:
            step_history = json.loads(step_history_raw) if step_history_raw else []
        except (json.JSONDecodeError, TypeError):
            step_history = []

        return TaskRecord(
            thread_id=row["thread_id"],
            index_dir=row["index_dir"],
            status=row["status"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            current_step=row["current_step"] or "",
            step_history=step_history,
            error=row["error"] or "",
            escalation_reason=row["escalation_reason"] or "",
            artifacts_produced=row["artifacts_produced"] or "",
        )

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def update_registry_from_result(
    thread_id: str, index_dir: str, result: dict
) -> None:
    """Writes a RunResult's status to the global TaskRegistry.

    Consolidates the suspended/completed/failed branching that was
    previously duplicated across cli.py and mcp_server.py. Opens
    a short-lived registry connection for thread-safe writes.
    """
    # Map RunResult status to registry update kwargs
    status = result.get("status", "failed")
    fields: dict = {"current_step": result.get("final_step", "")}

    artifacts = result.get("artifacts_produced", [])
    if artifacts:
        fields["artifacts_produced"] = json.dumps(artifacts)

    if status == "suspended":
        fields["status"] = "suspended"
        fields["escalation_reason"] = result.get("escalation_reason", "")
    elif status == "completed":
        fields["status"] = "completed"
    elif status == "failed":
        fields["status"] = "failed"
        fields["error"] = result.get("escalation_reason", "unknown error")
    else:
        # Unexpected status — record it as-is
        fields["status"] = status

    with TaskRegistry() as registry:
        registry.update(thread_id, index_dir, **fields)
