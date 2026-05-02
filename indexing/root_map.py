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


def regenerate_root_map(
    work_units: Sequence[WorkUnit],
    output_dir: str,
    index_state: StateProtocol,
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
    collected_data = collect_overviews(
        index_state, work_units, epoch, log_warnings=True
    )

    # Calculate global project health using the new weighted confidence logic.
    project_health = calculate_project_health(collected_data)
    health_bar = get_health_bar(project_health)

    overviews_list = [
        f"## {item['display_path']}\n\n{item['content']}\n" 
        for item in collected_data
    ]
    overviews_text = "\n".join(overviews_list)
    
    # Truncate overviews_text safely to prevent Context Window Exceeded errors 
    # on local LLMs. We slice at the nearest newline to avoid cutting mid-word or
    # breaking markdown structures abruptly.
    prompt_text = overviews_text
    if len(prompt_text) > 30000:
        logging.warning("Overviews text truncated for RootMap LLM synthesis to prevent context overflow.")
        cut_index = prompt_text.rfind('\n', 0, 30000)
        if cut_index == -1:
            cut_index = 30000
        prompt_text = prompt_text[:cut_index] + "\n\n...[Truncated]..."
        
    # Generate the top-level summary using the aggregated overviews.
    summary = llm_prompter.prompt_for_root_map_summary(prompt_text)
    
    # Extract verification issues for the global report.
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

    # Assemble the final markdown document for the current indexing epoch.
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

    # Persist the final root map to the specified output directory.
    root_map_file.parent.mkdir(parents=True, exist_ok=True)
    root_map_file.write_text(content, encoding="utf-8")
    # Logging instead of printing for cleaner production logs.
    logging.info("Successfully wrote root map to %s", root_map_file)
