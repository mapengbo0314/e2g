"""Harness state definition and virtual overlay system."""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import fcntl
import json
import os
import datetime

from pydantic import ValidationError
from langgraph.graph import add_messages
from indexing.state import LocalState
from indexing.schema import IndexDocument, Overview, KeyIndividualComponents, KeyInterfaces, KeyDependencies

class VerifiedContextItem(TypedDict):
    path: str
    summary: str

class RunResult(TypedDict):
    """Structured return type for orchestrator.run() and resume().

    Gives callers (CLI, MCP server) a deterministic way to detect
    whether the graph completed, suspended at human, or failed.
    """
    status: str              # "completed" | "suspended" | "failed"
    thread_id: str
    escalation_reason: str   # empty string if not suspended
    final_step: str          # last node that ran
    human_prompt: str        # prompt to show the human (empty if N/A)
    artifacts_produced: list # list of generated artifacts or strategies

class HarnessState(TypedDict):
    # Input
    user_prompt: str

    # Planning phase
    milestones: list[dict]               # From Planner: [{"id": int, "task": "str"}]
    logical_flaws: list[str]             # From Adversary
    risk_level: str                      # From Adversary: "high" | "low"

    # Context phase
    implementation_strategy: str         # From Architect
    verified_context: list[VerifiedContextItem]  # From Architect
    stale_paths: list[str]               # From ContextTools

    # Implementation phase
    generated_diffs: dict[str, str]      # From Implementer: {path: unified_diff_str}
    provisional_summaries: dict[str, str]  # From Implementer: {path: summary_str}
    implementation_notes: list[str]

    # Review phase
    review_findings: list[dict]          # From Reviewer
    verification_verdict: dict           # From Verifier
    verification_citations: list[str]    # From Verifier
    status: str

    # Safeguards
    review_retry_count: int
    verify_retry_count: int
    max_retries: int
    escalation_reason: str

    # Human-in-the-loop fields (v3.0 scalability fix)
    human_feedback: str                  # Injected by resume() after human input
    step_history: list[str]              # Observability: ["planner:planned", "reviewer:review_failed", ...]
    
    # LangGraph messages
    messages: Annotated[list, add_messages]

class OverlayState(LocalState):
    """A lazy-loading overlay that intercepts disk reads and injects session-specific diffs."""
    
    def __init__(
        self, 
        state_dir: str, 
        current_diffs: dict[str, str], 
        provisional_summaries: dict[str, str], 
        fs_manager: Any = None, 
        input_prefix_to_strip: str = None
    ):
        """Initializes the virtual overlay for the indexing system.
        
        The overlay intercepts reads and writes to disk, serving in-memory 
        modifications (`current_diffs`) and temporary generated summaries 
        (`provisional_summaries`) to agents before they are permanently committed.
        """
        super().__init__(state_dir, fs_manager=fs_manager, input_prefix_to_strip=input_prefix_to_strip)
        self._current_diffs = current_diffs or {}
        self._provisional_summaries = provisional_summaries or {}

    @property
    def active_diffs(self) -> dict[str, str]:
        """Publicly exposes the current session diffs for tool usage."""
        return self._current_diffs

    def _read_locked_file(self, file_path: str) -> str:
        """Safely reads a file with an exclusive shared fcntl lock."""
        with open(file_path, "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return f.read()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def read_artifact(self, path: str, epoch: int = 0) -> str:
        """Fetch base index from disk and apply overlay, returning JSON."""
        file_path = self._get_path(path, epoch, extension="json")
        base_json = ""
        
        try:
            base_json = self._read_locked_file(file_path)
        except FileNotFoundError:
            # Handling New Files (Synthetic Stubs)
            if path in self._current_diffs:
                summary = self._provisional_summaries.get(path)
                stub = IndexDocument.synthetic_stub(path, self._current_diffs[path], summary)
                return stub.model_dump_json()
            else:
                raise

        # Parse base JSON securely
        try:
            doc = IndexDocument.model_validate_json(base_json)
        except (ValueError, ValidationError):
            # Fallback to standard dict initialization if Pydantic strict parsing fails
            doc_dict = json.loads(base_json)
            doc = IndexDocument(**doc_dict)
            
        # Identify Change and Apply Override
        if path in self._current_diffs:
            new_content = self._current_diffs[path]
            # Wipe Semantic fields
            summary = self._provisional_summaries.get(path, "[WIPED: SESSION BUFFER ACTIVE]")
            doc.overview = Overview(content=summary)
            
            # Stale Mark
            stale_mark = "STALE: Local modifications exist"
            if stale_mark not in doc.verification_notes:
                # We create a new list and update the model to prevent 
                # unsafe in-place mutation of the Pydantic instance.
                updated_notes = list(doc.verification_notes) + [stale_mark]
                doc = doc.model_copy(update={"verification_notes": updated_notes})

        return doc.model_dump_json()

    def read_summary(self, path: str, epoch: int = 0) -> str:
        """Fetch summary from overlay."""
        if path in self._current_diffs:
            return self._provisional_summaries.get(path, "[WIPED: SESSION BUFFER ACTIVE]")
        return super().read_summary(path, epoch)
