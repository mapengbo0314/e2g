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


# Template for the final user prompt used during the LLM merge phase.
USER_PROMPT_TEMPLATE_MERGE = (
    "Please merge the partial summaries above into a single, coherent"
    " document for the directory {directory_path}."
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
    """Best-effort local stand-in for file_utils.get_subdirectory_indexes(...)."""
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return {}

    child_dirs = sorted(child for child in path.iterdir() if child.is_dir())
    child_paths = [str(child) for child in child_dirs]
    if not child_paths:
        return {}

    try:
        return index_state.read_summaries(child_paths, 0)
    except Exception:
        # Fallback to an empty dictionary if the state read fails.
        return {}


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
    def merge(self, docs: list[Any], directory_path: str, error_prompt: str = "") -> Any:
        """Merges multiple markdown indexes into one using an LLM.

        Args:
            docs: The list of markdown indexes to merge.
            directory_path: The path to the directory being indexed.
            error_prompt: Optional verification error prompt to pass to the LLM.

        Returns:
            The merged markdown index.

        Raises:
            ValueError: If no indexes are provided.
        """
        self._stats.increment_counter("merges.started")
        if not docs:
            # Avoid processing empty document lists.
            raise ValueError("No indexes to merge.")

        if len(docs) == 1:
            # Optimization: Skip LLM call if only a single document exists.
            self._stats.increment_counter("merges.skipped_single_index")
            return docs[0]

        # Construct the context-heavy system prompt for the merge task.
        system_prompt = (
            prompt_templates.create_merger_prompt()
            + "\n Partial summaries: \n"
            + "\n\n---\n\n".join(_serialize_doc(doc) for doc in docs)
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

        # Prepare the final user prompt directing the LLM to unify the provided docs.
        initial_user_prompt = USER_PROMPT_TEMPLATE_MERGE.format(
            directory_path=directory_path
        )
        if error_prompt:
            initial_user_prompt += "\n\n" + error_prompt

        logging.info(
            "Merging index for %s with prompt: %s",
            directory_path,
            initial_user_prompt,
        )

        # Delegate the final synthesis to the LLM prompter.
        return self._llm_prompter.prompt_for_merging(
            directory_path=directory_path,
            system_prompt=system_prompt,
            initial_user_prompt=initial_user_prompt,
            error_prompt_generator_instance=ErrorPromptGenerator(),
        )
