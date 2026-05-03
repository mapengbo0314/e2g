"""LangGraph orchestrator for the Unified Harness."""

import sqlite3
import sys
import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver

from harness.state import HarnessState
from harness.prompter import UnifiedPrompter, AgentConfigLoader
from harness.nodes import HarnessNodes

def route_adversary(state: HarnessState) -> Literal["implementer", "planner"]:
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
    """Configures and runs the LangGraph topology."""
    
    def __init__(
        self, 
        index_dir: str = ".index_state",
        agents_dir: str = "_agents/agents", 
        db_path: str = ".harness_checkpoints.sqlite"
    ):
        from harness.state import OverlayState
        from harness.tools import ContextTools
        from indexing.fs_manager import RealFsManager
        
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
        
        self.nodes = HarnessNodes(self.prompter, self.tools)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(self.conn)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(HarnessState)
        
        # Add nodes
        workflow.add_node("planner", self.nodes.planner_node)
        workflow.add_node("architect", self.nodes.architect_node)
        workflow.add_node("adversary", self.nodes.adversarial_verifier_node)
        workflow.add_node("implementer", self.nodes.implementer_node)
        workflow.add_node("reviewer", self.nodes.reviewer_node)
        workflow.add_node("verifier", self.nodes.verifier_node)
        workflow.add_node("human", lambda state: {"status": "awaiting_human"})

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
        
        workflow.add_edge("human", "implementer") # Resume path

        return workflow.compile(checkpointer=self.checkpointer)

    def run(self, user_prompt: str, thread_id: str):
        """Executes the workflow for a given user prompt."""
        initial_state = {
            "user_prompt": user_prompt,
            "max_retries": 3,
            "review_retry_count": 0,
            "verify_retry_count": 0,
            "status": "initialized",
            "verified_context": [],
            "messages": []
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        logging.info(f"Starting workflow for thread {thread_id}...")
        for event in self.graph.stream(initial_state, config=config):
            for k, v in event.items():
                logging.info(f"[{k}] Status: {v.get('status', 'unknown')}")
                
        final_state = self.graph.get_state(config).values
        if final_state.get("status") == "verification_passed":
            logging.info("Workflow complete and verified!")
