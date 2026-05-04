"""Tests for interrupt-based human escalation (SM-201, SM-206 coverage).

Proves:
  1. interrupt_before pauses the graph at the human node
  2. Resume continues the graph after human input
  3. Reviewer-fail path triggers suspension with escalation_reason
  4. Verifier-fail path triggers suspension with escalation_reason
  5. Resume after verifier failure resets verify_retry_count to 0
"""

import sqlite3
import pytest
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from typing_extensions import TypedDict


# ── Minimal State for Unit Tests ──────────────────────────────────

class MinimalState(TypedDict):
    value: str
    retry_count: int
    max_retries: int
    escalation_reason: str
    status: str


# ── Test 1 & 2: Pure interrupt/resume with minimal graph ─────────

class TestInterruptMechanism:
    """Proves interrupt_before works with our version of LangGraph."""

    @pytest.fixture
    def minimal_graph(self, tmp_path):
        """Builds a minimal 3-node graph: start → fail_node → human."""
        db_path = str(tmp_path / "test_checkpoints.sqlite")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        def fail_node(state: MinimalState) -> Dict[str, Any]:
            return {
                "status": "failed",
                "retry_count": state.get("retry_count", 0) + 1,
                "escalation_reason": "Test escalation reason"
            }

        def human_node(state: MinimalState) -> Dict[str, Any]:
            return {
                "status": "human_reviewed",
                "retry_count": 0
            }

        def route_after_fail(state: MinimalState) -> Literal["human", "end"]:
            if state.get("retry_count", 0) >= state.get("max_retries", 1):
                return "human"
            return "end"

        workflow = StateGraph(MinimalState)
        workflow.add_node("fail_node", fail_node)
        workflow.add_node("human", human_node)

        workflow.add_edge(START, "fail_node")
        workflow.add_conditional_edges("fail_node", route_after_fail, {
            "human": "human",
            "end": END
        })
        workflow.add_edge("human", END)

        graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human"]
        )

        yield graph, conn
        conn.close()

    def test_interrupt_pauses_at_human(self, minimal_graph):
        """Graph pauses BEFORE the human node when interrupt_before is set."""
        graph, _ = minimal_graph
        config = {"configurable": {"thread_id": "test-interrupt-1"}}

        initial = {"value": "test", "retry_count": 0, "max_retries": 1, "escalation_reason": "", "status": ""}

        # Stream should stop at human node
        events = list(graph.stream(initial, config=config))

        # Verify the graph is suspended
        state = graph.get_state(config)
        assert "human" in state.next, f"Expected 'human' in next, got {state.next}"
        assert state.values.get("escalation_reason") == "Test escalation reason"

    def test_resume_continues_after_interrupt(self, minimal_graph):
        """Resuming a suspended graph runs the human node and continues."""
        graph, _ = minimal_graph
        config = {"configurable": {"thread_id": "test-resume-1"}}

        initial = {"value": "test", "retry_count": 0, "max_retries": 1, "escalation_reason": "", "status": ""}

        # First run: should suspend
        list(graph.stream(initial, config=config))
        state = graph.get_state(config)
        assert "human" in state.next

        # Resume: stream None to continue from checkpoint
        resume_events = list(graph.stream(None, config=config))

        # After resume, graph should be complete (no more next nodes)
        final_state = graph.get_state(config)
        assert final_state.next == () or final_state.next is None or len(final_state.next) == 0
        assert final_state.values.get("status") == "human_reviewed"
        assert final_state.values.get("retry_count") == 0  # Reset by human node


# ── Test 3, 4, 5: Full harness paths ────────────────────────────

class TestHarnessEscalationPaths:
    """Tests using the actual HarnessState and node implementations.

    These tests use mock LLMs that always return failure to force the
    escalation paths without requiring real API keys.
    """

    @pytest.fixture
    def mock_nodes_orchestrator(self, tmp_path):
        """Builds a harness orchestrator with mock LLM that always fails review/verify."""
        import os
        from unittest.mock import patch, MagicMock
        from harness.state import HarnessState, RunResult
        from harness.orchestrator import HarnessOrchestrator

        # Create a minimal index_dir structure
        index_dir = str(tmp_path / "test_index")
        os.makedirs(index_dir, exist_ok=True)

        # Create minimal agents config
        agents_dir = str(tmp_path / "agents")
        os.makedirs(agents_dir, exist_ok=True)

        # Patch the LLM call to always return review failure JSON
        with patch("harness.nodes.HarnessNodes._call_llm") as mock_llm:
            # Default: always return failed review
            mock_llm.return_value = '{"passed": false, "review_findings": [{"issue": "mock failure"}]}'

            orchestrator = HarnessOrchestrator(
                index_dir=index_dir,
                agents_dir=agents_dir
            )
            yield orchestrator, mock_llm, index_dir

        orchestrator.close()

    def test_reviewer_fail_suspends_with_escalation_reason(self, mock_nodes_orchestrator):
        """When reviewer fails max_retries times, graph suspends with escalation_reason."""
        orchestrator, mock_llm, _ = mock_nodes_orchestrator

        # Mock LLM: all nodes succeed quickly except reviewer which always fails
        def mock_response(agent_name, state):
            if agent_name == "reviewer":
                return '{"passed": false, "review_findings": [{"issue": "mock code quality issue"}]}'
            elif agent_name == "verifier":
                return '{"passed": true, "issues": []}'
            return "OK"

        mock_llm.side_effect = mock_response

        result = orchestrator.run(user_prompt="test prompt", thread_id="reviewer-fail-test")

        assert result["status"] == "suspended", f"Expected suspended, got {result['status']}"
        assert "Review loop exhausted" in result["escalation_reason"]
        assert result["thread_id"] == "reviewer-fail-test"

    def test_verifier_fail_suspends_with_escalation_reason(self, mock_nodes_orchestrator):
        """When verifier fails max_retries times, graph suspends with escalation_reason."""
        orchestrator, mock_llm, _ = mock_nodes_orchestrator

        call_count = {"verify": 0}

        def mock_response(agent_name, state):
            if agent_name == "reviewer":
                return '{"passed": true, "review_findings": []}'
            elif agent_name == "verifier":
                call_count["verify"] += 1
                return '{"passed": false, "issues": ["mock verification failure"]}'
            return "OK"

        mock_llm.side_effect = mock_response

        result = orchestrator.run(user_prompt="test prompt", thread_id="verifier-fail-test")

        assert result["status"] == "suspended", f"Expected suspended, got {result['status']}"
        assert "Verification loop exhausted" in result["escalation_reason"]

    def test_resume_after_verifier_failure_resets_counters(self, mock_nodes_orchestrator):
        """After human resumes a verifier failure, verify_retry_count resets to 0."""
        orchestrator, mock_llm, _ = mock_nodes_orchestrator

        resume_count = {"calls": 0}

        def mock_response_fail(agent_name, state):
            if agent_name == "reviewer":
                return '{"passed": true, "review_findings": []}'
            elif agent_name == "verifier":
                return '{"passed": false, "issues": ["mock failure"]}'
            return "OK"

        def mock_response_pass(agent_name, state):
            if agent_name == "reviewer":
                return '{"passed": true, "review_findings": []}'
            elif agent_name == "verifier":
                return '{"passed": true, "issues": []}'
            return "OK"

        # First run: fail until suspension
        mock_llm.side_effect = mock_response_fail
        result = orchestrator.run(user_prompt="test prompt", thread_id="resume-reset-test")
        assert result["status"] == "suspended"

        # Check counters are at max before resume
        config = {"configurable": {"thread_id": "resume-reset-test"}}
        pre_state = orchestrator.graph.get_state(config)
        assert pre_state.values.get("verify_retry_count", 0) >= pre_state.values.get("max_retries", 3)

        # Resume: now everything passes
        mock_llm.side_effect = mock_response_pass
        result = orchestrator.resume(thread_id="resume-reset-test", human_feedback="approved, try again")

        # After resume, the human node should have reset counters
        post_state = orchestrator.graph.get_state(config)
        # If it completed, verify_retry_count should be 0 (reset by human, then verifier passed)
        assert post_state.values.get("verify_retry_count") == 0
        assert result["status"] == "completed"

    def test_interrupt_fires_on_every_visit(self, mock_nodes_orchestrator):
        """The interrupt fires on EVERY visit to human, not just the first."""
        orchestrator, mock_llm, _ = mock_nodes_orchestrator

        visit_count = {"human_visits": 0}

        def mock_response_always_fail(agent_name, state):
            if agent_name == "reviewer":
                return '{"passed": false, "review_findings": [{"issue": "always fails"}]}'
            elif agent_name == "verifier":
                return '{"passed": true, "issues": []}'
            return "OK"

        mock_llm.side_effect = mock_response_always_fail

        # First run: fails 3 times, suspends
        result = orchestrator.run(user_prompt="test", thread_id="multi-interrupt-test")
        assert result["status"] == "suspended"

        # Resume: will fail 3 more times, should suspend AGAIN
        result = orchestrator.resume(thread_id="multi-interrupt-test", human_feedback="try again")
        assert result["status"] == "suspended", "Second suspension should occur on second visit to human node"
