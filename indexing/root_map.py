"""Utilities for creating and summarizing root maps.

This module is a local, reference-oriented reconstruction of the screenshot
backed `root_map.py`. The key responsibilities preserved here are:

- collect `Overview` sections from indexed directory summaries
- generate a top-level root map summary through the LLM prompter
- write `root_map_v{epoch}.md` artifacts to disk
"""

# Core library and typing imports for root map generation.
from __future__ import annotations
from collections.abc import Sequence
import logging
from pathlib import Path
from typing import Protocol

# Dependency imports with local fallback support.
try:
    from indexing.work_unit import WorkUnit
    from indexing import schema
except ImportError:
    # Handle environment where indexing package is not installed as a library.
    from work_unit import WorkUnit
    import schema


class StateProtocol(Protocol):
    """Minimal protocol used by the root-map reference."""

    def read_summaries(
        self, path_strs: Sequence[str], epoch: int
    ) -> dict[str, str]: ...

    def read_artifact(self, path_str: str, epoch: int) -> str: ...

    def get_display_path(self, path_str: str) -> str: ...


class LlmPrompterProtocol(Protocol):
    """Minimal protocol for top-level root map synthesis."""

    def prompt_for_root_map_summary(self, overviews: str) -> str: ...
# Core functionality for collecting and consolidating codebase overviews.

def collect_overviews(
    index_state: StateProtocol,
    paths: Sequence[Path],
    epoch: int,
    log_warnings: bool = False,
) -> list[str]:
    """Collects overviews for the given paths."""
    collected_overviews = []
    path_strs = [str(path) for path in paths]

    summaries = index_state.read_summaries(path_strs, epoch)

    for path_str in path_strs:
        try:
            artifact_json = index_state.read_artifact(path_str, epoch)
            doc = schema.IndexDocument.model_validate_json(artifact_json)
            overview = doc.overview.content
            if overview:
                # Format the display path for clear markdown section headers.
                display_path = index_state.get_display_path(path_str)
                display_path = display_path.removeprefix("//depot/mono/")
                collected_overviews.append(f"## {display_path}\n\n{overview}\n")
            elif log_warnings:
                # Log cases where a summary exists but is missing its overview section.
                logging.warning(
                    "No Overview section found in index for %s epoch %s.",
                    path_str,
                    epoch,
                )
        except Exception:
            if log_warnings:
                # We don't distinguish between exist_summary=False and
                # FileNotFoundError here because read_summaries abstracts that away.
                # If a summary is missing, we log a warning for troubleshooting.
                logging.warning(
                    "Index file not found or could not be read for %s epoch %s.",
                    path_str,
                    epoch,
                )

    return collected_overviews


def regenerate_root_map(
    work_units: Sequence[WorkUnit],
    output_dir: str,
    index_state: StateProtocol,
    # Continuation of processing logic.
    epoch: int,
    fs_manager: object | None,
    llm_prompter: LlmPrompterProtocol,
) -> None:
    """Writes a root map file consolidating overviews from all index files."""
    # Define the output file path for the specific indexing epoch.
    root_map_file = Path(output_dir) / f"root_map_v{epoch}.md"

    # Extract directory paths from work units and sort for consistent output.
    all_index_paths = sorted(
        [
            Path(getattr(work_unit, "output_path", getattr(work_unit, "unit_id", "")))
            for work_unit in work_units
        ]
    )
    logging.info(
        "Regenerating root map for %d directories.", len(all_index_paths)
    )

    # Aggregate all overviews into a single context for LLM summarization.
    collected_overviews = collect_overviews(
        index_state, all_index_paths, epoch, log_warnings=True
    )

    overviews = "\n".join(collected_overviews)
    summary = llm_prompter.prompt_for_root_map_summary(overviews)
    # Assemble the final markdown document for the current indexing epoch.
    content = "\n".join(
        [
            f"# Root Map - Epoch {epoch}\n",
            f"## Summary\n\n{summary}\n",
            overviews,
        ]
    )

    # Persist the final root map to the specified output directory.
    root_map_file.parent.mkdir(parents=True, exist_ok=True)
    root_map_file.write_text(content, encoding="utf-8")
    # Logging instead of printing for cleaner production logs.
    logging.info("Successfully wrote root map to %s", root_map_file)
