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
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Protocol, TypedDict


class OverviewData(TypedDict):
    """Holds overview content along with confidence and size metadata."""
    display_path: str
    content: str
    confidence: float
    size_bytes: int
    is_verified: bool
    issues: list[str]
    is_empty_bypass: bool

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
    work_units: Sequence[WorkUnit],
    epoch: int,
    log_warnings: bool = False,
) -> list[OverviewData]:
    """Collects overviews and metadata for the given work units."""
    collected_data = []
    
    # Create a mapping for quick lookup of work unit metadata by path.
    wu_map = {str(wu.output_path): wu for wu in work_units}

    path_strs = [str(wu.output_path) for wu in work_units]
    summaries = index_state.read_summaries(path_strs, epoch)

    for path_str in path_strs:
        try:
            artifact_json = index_state.read_artifact(path_str, epoch)
            doc = schema.IndexDocument.model_validate_json(artifact_json)
            
            overview = doc.overview.content
            confidence = 1.0
            is_verified = True
            issues = []
            is_empty_bypass = False
            
            if doc.verification_state:
                confidence = doc.verification_state.confidence
                is_verified = doc.verification_state.verified
                issues = doc.verification_state.issues
                is_empty_bypass = getattr(doc.verification_state, "is_empty_bypass", False)

            # Get the actual size from the work unit to ensure 'fair' weighting.
            wu = wu_map.get(path_str)
            size_bytes = wu.size_bytes if wu else 0

            if overview:
                display_path = index_state.get_display_path(path_str)
                display_path = display_path.removeprefix("//depot/mono/")
                
                collected_data.append({
                    "display_path": display_path,
                    "content": overview,
                    "confidence": confidence,
                    "size_bytes": size_bytes,
                    "is_verified": is_verified,
                    "issues": issues,
                    "is_empty_bypass": is_empty_bypass
                })
            elif log_warnings:
                logging.warning(
                    "No Overview section found in index for %s epoch %s.",
                    path_str,
                    epoch,
                )
        except Exception:
            if log_warnings:
                logging.warning(
                    "Index file not found or could not be read for %s epoch %s.",
                    path_str,
                    epoch,
                )

    return collected_data


def calculate_project_health(data: list[OverviewData]) -> float:
    """Calculates the weighted average confidence score for the project."""
    total_weighted_confidence = 0.0
    total_size = 0
    
    for item in data:
        if item.get("is_empty_bypass"):
            continue
        size = item["size_bytes"]
        # Treat directories with no files as having minimal weight to avoid division by zero.
        effective_size = max(size, 1) 
        total_weighted_confidence += item["confidence"] * effective_size
        total_size += effective_size
        
    if total_size == 0:
        return 0.0
    return total_weighted_confidence / total_size


def get_health_bar(confidence: float) -> str:
    """Generates a visual health bar for the markdown report."""
    percentage = int(confidence * 100)
    filled_blocks = int(confidence * 20)
    bar = "█" * filled_blocks + "░" * (20 - filled_blocks)
    
    emoji = "🟢" if confidence > 0.9 else "🟡" if confidence > 0.7 else "🔴"
    return f"{emoji} **{bar} {percentage}%**"


def _recursive_summarize(
    items: list[str],
    llm_prompter: LlmPrompterProtocol,
    chunk_size: int = 10,
    max_item_chars: int = 24000,
) -> str:
    """Recursively summarizes a list of content items using Map-Reduce.
    
    Args:
        items: List of text items to summarize.
        llm_prompter: The LLM prompter for synthesis calls.
        chunk_size: Number of items per batch.
        max_item_chars: Maximum characters per individual item before forced
            truncation. Prevents infinite loops when a single item exceeds
            the LLM context window (Review Finding #7).
    """
    if not items:
        return "No content to summarize."
    if len(items) == 1:
        return items[0]

    # Force-truncate oversized individual items to prevent batching deadlocks
    safe_items = []
    for item in items:
        if len(item) > max_item_chars:
            logging.warning(
                "[RootMap] Truncating oversized summary item (%d chars > %d limit).",
                len(item), max_item_chars,
            )
            safe_items.append(item[:max_item_chars] + "\n...[TRUNCATED]")
        else:
            safe_items.append(item)

    logging.info(f"[RootMap] Map-Reduce: Processing {len(safe_items)} items in {len(range(0, len(safe_items), chunk_size))} chunks.")
    
    summaries = []
    for i in range(0, len(safe_items), chunk_size):
        chunk = safe_items[i:i + chunk_size]
        chunk_text = "\n\n".join(chunk)
        # We use the same prompter method; the prompter should handle the synthesis logic.
        summary = llm_prompter.prompt_for_root_map_summary(chunk_text)
        summaries.append(summary)
    
    if len(summaries) == 1:
        return summaries[0]
        
    return _recursive_summarize(summaries, llm_prompter, chunk_size, max_item_chars)


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

    all_index_paths = sorted(
        [
            Path(getattr(work_unit, "output_path", getattr(work_unit, "unit_id", "")))
            for work_unit in work_units
        ]
    )
    logging.info(
        "Regenerating root map for %d directories.", len(all_index_paths)
    )

    collected_data = collect_overviews(
        index_state, work_units, epoch, log_warnings=True
    )

    project_health = calculate_project_health(collected_data)
    health_bar = get_health_bar(project_health)

    overviews_list = [
        f"## {item['display_path']}\n\n{item['content']}\n" 
        for item in collected_data
    ]
    
    # --- Recursive Map-Reduce Synthesis ---
    # Instead of naive truncation, we recursively summarize chunks of overviews.
    summary = _recursive_summarize(overviews_list, llm_prompter)
    
    unverified_sections = [
        item for item in collected_data if not item["is_verified"]
    ]
    
    issues_report = ""
    if unverified_sections:
        issues_report = "### ⚠️ Verification Observations\n"
        issues_report += "The following directories contain unverified claims or grounding issues:\n\n"
        for item in unverified_sections:
            issues_report += f"- **{item['display_path']}**: {len(item['issues'])} issues noted.\n"
        issues_report += "\n"

    overviews_text = "\n".join(overviews_list)
    content = "\n".join(
        [
            f"# Root Map - Epoch {epoch}\n",
            f"### Project Index Health\n{health_bar}\n",
            f"## Summary\n\n{summary}\n",
            issues_report,
            "## Directory Overviews\n",
            overviews_text,
        ]
    )

    root_map_file.parent.mkdir(parents=True, exist_ok=True)

    # Task 4: Metadata JSON
    total_tokens = 0
    total_files = 0
    for work_unit in work_units:
        unit_id = str(getattr(work_unit, "output_path", getattr(work_unit, "unit_id", "")))
        files = getattr(work_unit, "files_to_index", [])
        total_files += len(files) if files else 1 # fallback to 1 if not available
        try:
            artifact_json = index_state.read_artifact(unit_id, epoch)
            doc = schema.IndexDocument.model_validate_json(artifact_json)
            if doc.generation_metadata and doc.generation_metadata.cost_report:
                total_tokens += doc.generation_metadata.cost_report.total_tokens
        except Exception as e:
            logging.debug("Could not read token usage for %s: %s", unit_id, e)

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "total_tokens": total_tokens,
        "total_files_indexed": total_files,
        "total_directories_indexed": len(work_units),
    }
    metadata_file = Path(output_dir) / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    root_map_file.write_text(content, encoding="utf-8")
    logging.info("Successfully wrote root map to %s", root_map_file)
