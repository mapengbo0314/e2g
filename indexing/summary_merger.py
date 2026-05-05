"""Merges multiple markdown indexes into one using an LLM.

This is a local, reference-oriented reconstruction of the screenshot-backed
`summary_merger.py`. It preserves the important behavior:

- accept multiple partial index documents
- short-circuit when there is only one document
- build a system prompt from partial summaries plus subdirectory indexes
- delegate the final merge to the LLM prompter
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol
import tenacity
import httpx

from indexing import prompt_templates
from indexing import schema
from indexing import section_registry


# Template for the final user prompt used during the LLM merge phase.
USER_PROMPT_TEMPLATE_MERGE = (
    "Please merge the partial summaries above into a single, coherent"
    " document for the directory {directory_path}. "
    "Use the 'PROGRAMMATICALLY MERGED SECTIONS' as the ground truth for structural data."
)


class LlmPrompterProtocol(Protocol):
    """Minimal interface used by the merger reference."""

    def prompt_for_merging(
        self,
        directory_path: str,
        system_prompt: str,
        initial_user_prompt: str,
        error_prompt_generator_instance: Any,
    ) -> Any: ...


class IndexStateProtocol(Protocol):
    """Minimal index-state interface used by this file."""

    def read_summaries(
        self, path_strs: list[str], epoch: int
    ) -> dict[str, str]: ...
    
    def read_latest_summary(self, path: str) -> str: ...


class ErrorPromptGenerator:
    """Local fallback until the richer reference type is populated."""

    pass





def _serialize_doc(doc: Any) -> str:
    """Serializes a document in the most useful available way."""
    if hasattr(doc, "model_dump_json"):
        return doc.model_dump_json(indent=2)
    if hasattr(doc, "model_dump"):
        return json.dumps(doc.model_dump(), indent=2)
    if hasattr(doc, "__dict__"):
        return json.dumps(doc.__dict__, indent=2, default=str)
    return json.dumps(doc, indent=2, default=str)


def _get_subdirectory_indexes(
    index_state: IndexStateProtocol,
    directory_path: str,
    # Filtering configuration for selecting relevant subdirectory data.
    filtering_config: object | None = None,
) -> dict[str, str]:
    """Reads latest available summaries for all immediate subdirectories."""
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return {}

    child_dirs = sorted(child for child in path.iterdir() if child.is_dir())
    child_paths = [str(child) for child in child_dirs]
    if not child_paths:
        return {}

    results = {}
    for cp in child_paths:
        try:
            # Always use the latest available summary to ensure reindex parity.
            results[cp] = index_state.read_latest_summary(cp)
        except Exception:
            # Skip if no summary exists yet for this child.
            pass
    return results


class _StatsRecorder:
    """Very small local replacement for stat_recorder."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def add_to_counter(self, name: str, value: int) -> None:
        self.increment_counter(name, value)

    def record_latency(self, name: str, value: float) -> None:
        pass


class SummaryMerger:
    """Merges multiple markdown indexes into one using an LLM."""

    def __init__(
        self,
        llm_prompter_instance: LlmPrompterProtocol,
        index_state: IndexStateProtocol,
        fs_manager: object | None,
        filtering_config: object | None = None,
    ):
        """Initializes the SummaryMerger."""
        self._llm_prompter = llm_prompter_instance
        self._index_state = index_state
        self._fs_manager = fs_manager
        self._filtering_config = filtering_config
        self._stats = _StatsRecorder()

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        reraise=True
    )
    def merge(self, docs: list[Any], directory_path: str, epoch: int = 0, error_prompt: str = "", directory_files: list[str] | None = None) -> Any:
        """Merges multiple markdown indexes into one using a hybrid programmatic/LLM approach.

        This performs programmatic union/accumulation for deterministic sections 
        (blueprints, interfaces) to ensure zero-loss fidelity, while delegating 
        synthesis of text-heavy sections (overviews, deep dives) to the LLM.
        """
        self._stats.increment_counter("merges.started")
        if not docs:
            # Avoid processing empty document lists.
            raise ValueError("No indexes to merge.")

        if len(docs) == 1:
            # Optimization: Skip LLM call if only a single document exists.
            self._stats.increment_counter("merges.skipped_single_index")
            return docs[0]

        # --- Phase 1: Programmatic Merge (Deterministic) ---
        deterministic_sections = {}
        for section_id in section_registry.get_deterministic_section_ids():
            section_instances = []
            for doc in docs:
                # Handle both object and dict forms of partial summaries.
                inst = getattr(doc, section_id, None) if hasattr(doc, section_id) else doc.get(section_id)
                if inst:
                    section_instances.append(inst)
            
            if section_instances:
                merged = section_registry.merge_sections(section_id, section_instances)
                if merged:
                    deterministic_sections[section_id] = merged
        
        # --- Phase 2: LLM Synthesis (Non-deterministic) ---
        # Construct the context-heavy system prompt. We include the deterministic 
        # merges as explicit 'Ground Truth' to guide the LLM's synthesis.
        evidence_str = ""
        if deterministic_sections:
            evidence_str = "\n\n### PROGRAMMATICALLY MERGED SECTIONS (GROUND TRUTH)\n"
            for sid, inst in deterministic_sections.items():
                evidence_str += f"\n--- {sid} ---\n{_serialize_doc(inst)}"

        system_prompt = (
            prompt_templates.create_merger_prompt()
            + "\n Partial summaries: \n"
            + "\n\n---\n\n".join(_serialize_doc(doc) for doc in docs)
            + evidence_str
            + "\n Subdirectory Indexes: "
            + json.dumps(
                # Include nested indexes to help the LLM maintain hierarchical context.
                _get_subdirectory_indexes(
                    self._index_state,
                    directory_path,
                    filtering_config=self._filtering_config,
                ),
                indent=2,
                default=str,
            )
        )

        # Prepare the final user prompt.
        initial_user_prompt = USER_PROMPT_TEMPLATE_MERGE.format(
            directory_path=directory_path
        )
        if error_prompt:
            initial_user_prompt += "\n\n" + error_prompt

        logging.info(
            "Merging index for %s with programmatic help.",
            directory_path,
        )

        # Delegate the synthesis of text-heavy sections to the LLM.
        merged_doc = self._llm_prompter.prompt_for_merging(
            directory_path=directory_path,
            system_prompt=system_prompt,
            initial_user_prompt=initial_user_prompt,
            error_prompt_generator_instance=ErrorPromptGenerator(),
            directory_files=directory_files,
        )

        # --- Phase 3: Final Assembly & Fidelity Patching ---
        # We overwrite the deterministic fields in the LLM output with our 
        # programmatically merged data to ensure 100% structural fidelity.
        if hasattr(merged_doc, "model_copy"): # Pydantic v2
             for section_id, merged_inst in deterministic_sections.items():
                 setattr(merged_doc, section_id, merged_inst)
        elif isinstance(merged_doc, dict):
             for section_id, merged_inst in deterministic_sections.items():
                 merged_doc[section_id] = merged_inst

        return merged_doc
