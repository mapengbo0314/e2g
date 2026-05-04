"""LangGraph orchestrator for the Unified Harness.

Manages the agentic workflow graph with interrupt-based human escalation,
connection lifecycle via context manager, and structured RunResult returns.
"""

import os
import sqlite3
import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver

from harness.state import HarnessState, RunResult
from harness.prompter import UnifiedPrompter, AgentConfigLoader
from harness.nodes import HarnessNodes


def route_adversary(state: HarnessState) -> Literal["implementer", "planner"]:
    """Routes from Adversary: high risk loops back to planner, otherwise proceeds."""
    if state.get("risk_level") == "high":
        return "planner"
    return "implementer"

def route_reviewer(state: HarnessState) -> Literal["verifier", "implementer", "human"]:
    """
    Routes from Reviewer:
    - On success: proceed to Verifier
    - On failure: retry implementation up to max_retries, then fail-open to Human
    """
    if state.get("status") == "review_failed":
        if state.get("review_retry_count", 0) >= state.get("max_retries", 3):
            return "human"
        return "implementer"
    return "verifier"

def route_verifier(state: HarnessState) -> Literal["end", "implementer", "human"]:
    """
    Routes from Verifier:
    - On success: terminate (END)
    - On failure: retry implementation up to max_retries, then fail-open to Human
    """
    if state.get("status") == "verification_failed":
        if state.get("verify_retry_count", 0) >= state.get("max_retries", 3):
            return "human"
        return "implementer"
    return "end"


class HarnessOrchestrator:
    """Configures and runs the LangGraph topology.
    
    Supports interrupt-based human escalation and context manager lifecycle.
    Use as:
        with HarnessOrchestrator(index_dir=...) as orch:
            result = orch.run(user_prompt=..., thread_id=...)
    """
    
    def __init__(
        self, 
        index_dir: str = ".index_state",
        agents_dir: str = None, 
        db_path: str = None,
        sampling_callback=None
    ):
        from harness.state import OverlayState
        from harness.tools import ContextTools
        from indexing.fs_manager import RealFsManager
        
        self.index_dir = index_dir
        
        # Resolve agents_dir relative to the package if not provided
        if agents_dir is None:
            # harness/orchestrator.py -> harness/ -> root/
            harness_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            agents_dir = os.path.join(harness_root, "_agents", "agents")
            
        self.config_loader = AgentConfigLoader(agents_dir=agents_dir)
        self.prompter = UnifiedPrompter(self.config_loader)
        
        # Initialize the virtual overlay and tools
        self.overlay_state = OverlayState(
            state_dir=index_dir,
            current_diffs={},
            provisional_summaries={},
            fs_manager=RealFsManager()
        )
        self.tools = ContextTools(self.overlay_state, workspace_root=".")
        
        self.nodes = HarnessNodes(self.prompter, self.tools, sampling_callback=sampling_callback)
        
        # Checkpointer: per-repo SQLite under {index_dir}/checkpoints/
        if db_path is None:
            checkpoints_dir = os.path.join(index_dir, "checkpoints")
            os.makedirs(checkpoints_dir, exist_ok=True)
            db_path = os.path.join(checkpoints_dir, "langgraph.sqlite")
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(self.conn)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds the LangGraph workflow with interrupt_before on the human node.
        
        The human→implementer edge STAYS. interrupt_before fires BEFORE the
        human node on every visit (not just the first). On resume, the human
        node runs, then the edge routes back to implementer.
        """
        workflow = StateGraph(HarnessState)
        
        # Add nodes — human is now a proper method, not a lambda
        workflow.add_node("planner", self.nodes.planner_node)
        workflow.add_node("architect", self.nodes.architect_node)
        workflow.add_node("adversary", self.nodes.adversarial_verifier_node)
        workflow.add_node("implementer", self.nodes.implementer_node)
        workflow.add_node("reviewer", self.nodes.reviewer_node)
        workflow.add_node("verifier", self.nodes.verifier_node)
        workflow.add_node("human", self.nodes.human_node)

        # Add edges
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "architect")
        workflow.add_edge("architect", "adversary")
        
        # Conditional Edges
        workflow.add_conditional_edges("adversary", route_adversary, {
            "implementer": "implementer",
            "planner": "planner"
        })
        
        workflow.add_edge("implementer", "reviewer")
        
        workflow.add_conditional_edges("reviewer", route_reviewer, {
            "verifier": "verifier",
            "implementer": "implementer",
            "human": "human"
        })
        
        workflow.add_conditional_edges("verifier", route_verifier, {
            "end": END,
            "implementer": "implementer",
            "human": "human"
        })
        
        # Keep this edge: defines post-resume flow. The interrupt fires
        # BEFORE the human node, pausing execution. On resume, human runs,
        # then this edge routes to implementer.
        workflow.add_edge("human", "implementer")

        # interrupt_before fires on EVERY visit to the human node
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human"]
        )

    def run(self, user_prompt: str, thread_id: str) -> RunResult:
        """Executes the workflow for a given user prompt.
        
        Returns a RunResult indicating completion, suspension, or failure.
        """
        # Initial state hydration — all fields must match HarnessState TypedDict
        initial_state = {
            "user_prompt": user_prompt,
            "max_retries": 3,
            # Retry counters start at zero; incremented by reviewer/verifier nodes
            "review_retry_count": 0,
            "verify_retry_count": 0,
            "status": "initialized",
            "verified_context": [],
            "messages": [],
            # Observability: nodes append "node:outcome" on each execution
            "step_history": [],
            "human_feedback": "",
            "escalation_reason": ""
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        logging.info(f"Starting workflow for thread {thread_id}...")
        try:
            for event in self.graph.stream(initial_state, config=config):
                if isinstance(event, dict):
                    for k, v in event.items():
                        if isinstance(v, dict):
                            logging.info(f"[{k}] Status: {v.get('status', 'unknown')}")
        except Exception as e:
            logging.error(f"Workflow failed for thread {thread_id}: {e}")
            return RunResult(
                status="failed",
                thread_id=thread_id,
                escalation_reason="",
                final_step="unknown",
                human_prompt=""
            )
                
        return self._build_run_result(thread_id, config)

    def resume(self, thread_id: str, human_feedback: str) -> RunResult:
        """Resumes a suspended workflow after human input.
        
        Injects human_feedback into the graph state, then streams
        from the checkpoint. The human node will run, reset counters,
        and route back to implementer.
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Inject human feedback into state before the human node runs
        self.graph.update_state(
            config, 
            {"human_feedback": human_feedback}
        )
        
        logging.info(f"Resuming workflow for thread {thread_id} with human feedback...")
        try:
            for event in self.graph.stream(None, config=config):
                if isinstance(event, dict):
                    for k, v in event.items():
                        if isinstance(v, dict):
                            logging.info(f"[{k}] Status: {v.get('status', 'unknown')}")
        except Exception as e:
            logging.error(f"Resume failed for thread {thread_id}: {e}")
            return RunResult(
                status="failed",
                thread_id=thread_id,
                escalation_reason="",
                final_step="unknown",
                human_prompt=""
            )
        
        return self._build_run_result(thread_id, config)

    def _build_run_result(self, thread_id: str, config: dict) -> RunResult:
        """Inspects graph state and constructs a RunResult."""
        state_snapshot = self.graph.get_state(config)
        values = state_snapshot.values or {}
        next_nodes = state_snapshot.next or ()
        
        step_history = values.get("step_history") or []
        final_step = step_history[-1] if step_history else "unknown"
        escalation_reason = values.get("escalation_reason", "")
        
        artifacts = []
        if "implementation_strategy" in values and values["implementation_strategy"]:
            artifacts.append({
                "type": "implementation_strategy",
                "content": values["implementation_strategy"]
            })
        
        if "generated_diffs" in values and values["generated_diffs"]:
            import json
            artifacts.append({
                "type": "generated_diffs",
                "content": json.dumps(values["generated_diffs"])
            })

        if "human" in next_nodes:
            # Graph is suspended at the human interrupt
            return RunResult(
                status="suspended",
                thread_id=thread_id,
                escalation_reason=escalation_reason,
                final_step=final_step,
                human_prompt=escalation_reason,  # Show the escalation as prompt
                artifacts_produced=artifacts
            )
        
        # Graph finished — either verification_passed or terminated otherwise
        return RunResult(
            status="completed",
            thread_id=thread_id,
            escalation_reason="",
            final_step=final_step,
            human_prompt="",
            artifacts_produced=artifacts
        )

    def close(self):
        """Closes the SQLite checkpointer connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
