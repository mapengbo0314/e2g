"""Utilities for creating and summarizing root maps.

This module is a local, reference-oriented reconstruction of the screenshot
backed `root_map.py`. The key responsibilities preserved here are:

- collect `Overview` sections from indexed directory summaries
- generate a top-level root map summary through the LLM prompter
- write `root_map_v{epoch}.md` artifacts to disk
"""

from __future__ import annotations

from collections.abc import Sequence
import logging
from pathlib import Path
from typing import Protocol

try:
    from indexing.work_unit import WorkUnit
except ImportError:
    from work_unit import WorkUnit


class StateProtocol(Protocol):
    """Minimal protocol used by the root-map reference."""

    def read_summaries(
        self, path_strs: Sequence[str], epoch: int
    ) -> dict[str, str]: ...

    def get_display_path(self, path_str: str) -> str: ...


class LlmPrompterProtocol(Protocol):
    """Minimal protocol for top-level root map synthesis."""

    def prompt_for_root_map_summary(self, overviews: str) -> str: ...


def _extract_markdown_section(content: str, heading: str) -> str:
    """Extracts a markdown section body by heading name."""
    lines = content.splitlines()
    target = heading.strip().lower()
    in_section = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            if in_section:
                break
            if title == target:
                in_section = True
                continue
        elif in_section:
            collected.append(line)

    return "\n".join(collected).strip()


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
        if path_str in summaries:
            content = summaries[path_str]
            overview = _extract_markdown_section(content, "Overview")
            if overview:
                display_path = index_state.get_display_path(path_str)
                display_path = display_path.removeprefix("//depot/mono/")
                collected_overviews.append(f"## {display_path}\n\n{overview}\n")
            elif log_warnings:
                logging.warning(
                    "No Overview section found in index for %s epoch %s.",
                    path_str,
                    epoch,
                )
        else:
            if log_warnings:
                # We don't distinguish between exist_summary=False and
                # FileNotFoundError here because read_summaries abstracts that away.
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
    epoch: int,
    fs_manager: object | None,
    llm_prompter: LlmPrompterProtocol,
) -> None:
    """Writes a root map file consolidating overviews from all index files."""
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

    collected_overviews = collect_overviews(
        index_state, all_index_paths, epoch, log_warnings=True
    )

    overviews = "\n".join(collected_overviews)
    summary = llm_prompter.prompt_for_root_map_summary(overviews)
    content = "\n".join(
        [
            f"# Root Map - Epoch {epoch}\n",
            f"## Summary\n\n{summary}\n",
            overviews,
        ]
    )

    root_map_file.parent.mkdir(parents=True, exist_ok=True)
    root_map_file.write_text(content, encoding="utf-8")
    print(f"Successfully wrote root map to {root_map_file}")
