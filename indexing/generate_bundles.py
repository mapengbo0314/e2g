"""Main entrypoint for running the AI Codebase Indexer on project bundles.

This is the local equivalent of the upstream generate_bundles.py. It provides
a CLI-free programmatic API for running the indexing pipeline against local
directories.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
import concurrent.futures
import contextlib
import dataclasses
import logging
import os
import random
import shutil
import string
# Continuation of processing logic.
import tempfile
import threading
# Base types for defining structured data in the indexing pipeline.
from typing import Any

# Internal project module imports for the indexing pipeline components.
from indexing import chunker
from indexing import llm_indexer
from indexing import orchestrator
from indexing import reindexing
from indexing import sequential_llm_prompter
from indexing import shared_flags
from indexing import state
from indexing import summary_merger
from indexing import work_unit
from indexing import verification


# ---------------------------------------------------------------------------
# Lightweight bundle / config types (replace upstream protos)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class BundleConfig:
    """Lightweight replacement for bundle_pb2.ProjectBundle."""

    bundle_name: str = "default"
    input_dirs: list[str] = dataclasses.field(default_factory=list)
    output_dir: str = ""
    exclude_patterns: list[str] = dataclasses.field(default_factory=list)
    include_patterns: list[str] = dataclasses.field(default_factory=list)
    additional_extensions: list[str] = dataclasses.field(default_factory=list)
    custom_sections: list[Any] = dataclasses.field(default_factory=list)
    codebase_specific_context: str | None = None


@dataclasses.dataclass
class IndexerConfig:
    """Lightweight replacement for indexer_config.IndexerConfig."""

    max_dir_size: int | None = None
    max_work_unit_size_bytes: int | None = None
    input_prefix_to_strip: str | None = None


# ---------------------------------------------------------------------------
# Throttling
# ---------------------------------------------------------------------------


class _SemaphoreThrottleContext:
    def __init__(self, sem: threading.Semaphore) -> None:
        self._sem = sem

    def __enter__(self) -> _SemaphoreThrottleContext:
        self._sem.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self._sem.release()
        return False

    def report_output(self, _output: str) -> None:
        # Standard no-op implementation for the basic throttling reporter.
        return None


class SemaphoreThrottlingStrategy:
    """Simple semaphore-based throttling."""

    def __init__(self, max_parallel: int = 8) -> None:
        self._sem = threading.Semaphore(max_parallel)

    def acquire(self, _system_prompt: str, _user_prompt: str) -> _SemaphoreThrottleContext:
        return _SemaphoreThrottleContext(self._sem)


# ---------------------------------------------------------------------------
# Temporary directory utility
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def custom_temporary_directory(prefix: str = "") -> Iterator[str]:
    """Creates a temporary directory with a 2-character random suffix."""
    temp_dir_root = tempfile.gettempdir()
    chars = string.ascii_letters + string.digits
    for _ in range(1000):
        suffix = "".join(random.choice(chars) for _ in range(2))
        dir_name = os.path.join(temp_dir_root, prefix + suffix)
        try:
            os.mkdir(dir_name)
            try:
                # Provide the temporary directory path to the caller context.
                yield dir_name
            finally:
                shutil.rmtree(dir_name)
            return
        except FileExistsError:
            # Suffix collision detected; retry with a different random seed.
            continue
    raise FileExistsError(
        "Could not create temporary directory with 2-char suffix."
    )


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------


def create_llm_prompter(
    bundle: BundleConfig,
    throttling_strategy: Any = None,
    fs_manager: Any = None,
) -> sequential_llm_prompter.LlmPrompter:
    """Creates an LLM prompter for a bundle."""
    llm_cfg = shared_flags.config.llm
    # Return the configured prompter instance for the indexing lifecycle.
    return sequential_llm_prompter.GeminiLlmPrompter(
        sequential_llm_prompter.GeminiLlmPrompterConfig(
            bundle_name=bundle.bundle_name,
            throttling_strategy=throttling_strategy,
            # Retry limits and conversation thresholds.
            max_attempts=llm_cfg.max_retries,
            max_attempts_per_conversation=llm_cfg.max_attempts_per_conversation,
            # Model selection and platform configuration.
            synthesis_gemini_model=llm_cfg.model,
            research_gemini_model=llm_cfg.model,
            use_vertex_ai=llm_cfg.use_vertex_ai,
            vertex_ai_project_id=llm_cfg.vertex_project_id,
            google_api_key=llm_cfg.google_api_key,
            # Dry run and mock fallback flags.
            dry_run=shared_flags.config.pipeline.dry_run,
            allow_mock_fallback=llm_cfg.allow_mock_fallback,
        ),
        fs_manager=fs_manager,
    )


def execute_indexing(
    bundle: BundleConfig,
    indexer_config: IndexerConfig | None = None,
    fs_manager: Any = None,
    llm_prompter: sequential_llm_prompter.LlmPrompter | None = None,
    # Continuation of processing logic.
    reindex: bool = False,
) -> None:
    """Runs one iteration of indexing against a local directory bundle.

    Args:
        bundle: The bundle configuration describing input/output dirs.
        indexer_config: Optional indexer configuration overrides.
        fs_manager: File system manager (defaults to LocalFileSystemManager).
        llm_prompter: The LLM prompter instance.
        reindex: Whether to perform incremental reindexing.
    """
    config = indexer_config or IndexerConfig()
    input_prefix = config.input_prefix_to_strip
    if not input_prefix and len(bundle.input_dirs) == 1:
        input_prefix = bundle.input_dirs[0]

    # Ensure a file system manager is available for local or remote operations.
    fs_mgr = fs_manager or orchestrator.LocalFileSystemManager()
    output_dir = bundle.output_dir or os.path.join(bundle.input_dirs[0], ".index_output")

    index_state = state.LocalState(
        state_dir=output_dir,
        fs_manager=fs_mgr,
        input_prefix_to_strip=input_prefix,
    )

    # Initialize storage for work unit manifests (in-memory for the local reference).
    work_unit_storage = work_unit.InMemoryWorkUnitStorage()

    throttling = SemaphoreThrottlingStrategy(
        max_parallel=shared_flags.config.llm.max_parallelization
    )
    prompter = llm_prompter or create_llm_prompter(
        bundle, throttling_strategy=throttling, fs_manager=fs_mgr
    )

    index_differ = None
    if reindex:
        # Initialize the index differ to identify which files have changed since the last run.
        index_differ = reindexing.IndexDiffer(
            fs_manager=fs_mgr,
            work_unit_storage=work_unit_storage,
        )

    chunker_instance = chunker.Chunker()
    summary_merger_instance = summary_merger.SummaryMerger(
        llm_prompter_instance=prompter,
        index_state=index_state,
        fs_manager=fs_mgr,
    )

    # Configure the core LLM Indexer with necessary prompts and summary tools.
    llm_indexer_config = llm_indexer.LlmIndexerConfig(
        llm_prompter=prompter,
        index_state=index_state,
        chunker=chunker_instance,
        # Summary merger for combining chunked LLM outputs.
        summary_merger=summary_merger_instance,
        max_dir_size=config.max_dir_size,
        # Pass codebase-specific instructions for customized index generation.
        codebase_specific_context=bundle.codebase_specific_context,
        # Custom section definitions from the bundle blueprint.
        custom_sections=bundle.custom_sections,
    )

    indexer_instance = llm_indexer.LlmIndexer(llm_indexer_config, fs_mgr)

    from pathlib import Path
    verifier = None
    if shared_flags.config.trust.enabled:
        verifier = verification.ArtifactVerifier(
            llm_prompter=prompter,
            cache_dir=Path(fs_mgr.join(output_dir, "verification_cache"))
        )

    # Initialize the Orchestrator to manage the multi-epoch indexing process.
    indexer_orchestrator = orchestrator.Orchestrator(
        planner_instance=_SimplePlanner(
            input_dirs=bundle.input_dirs,
            fs_manager=fs_mgr,
        ),
        indexer=indexer_instance,
        num_epochs=shared_flags.config.pipeline.num_epochs,
        root_map_dir=output_dir,
        index_state=index_state,
        work_unit_storage=work_unit_storage,
        # Continuation of processing logic.
        max_workers=shared_flags.config.pipeline.max_workers,
        bundle_name=bundle.bundle_name,
        fs_manager=fs_mgr,
        input_prefix_to_strip=input_prefix,
        verifier=verifier,
    )

    indexer_orchestrator.run()


# ---------------------------------------------------------------------------
# Simple planner (replaces the upstream planner)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class _PlanResult:
    all_work_units: list[work_unit.WorkUnit]
    work_units_to_process: list[work_unit.WorkUnit]
    paths_to_delete: list[str] = dataclasses.field(default_factory=list)


class _SimplePlanner:
    """Walks input directories and creates one WorkUnit per subdirectory."""

    def __init__(
        self,
        input_dirs: list[str],
        fs_manager: Any = None,
    ) -> None:
        self._input_dirs = input_dirs
        self._fs_manager = fs_manager

    def plan(self) -> _PlanResult:
        from pathlib import Path

        units: list[work_unit.WorkUnit] = []
        # Continuation of processing logic.
        for input_dir in self._input_dirs:
            root = Path(input_dir)
            if not root.is_dir():
                logging.warning("Input dir %s is not a directory, skipping.", input_dir)
                continue
            for dirpath, dirnames, filenames in os.walk(input_dir):
                # Skip hidden directories
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                dp = Path(dirpath)
                files = [dp / f for f in filenames if not f.startswith(".")]
                if files:
                    units.append(
                        work_unit.WorkUnit(
                            output_path=dp,
                            files_to_index=[str(f) for f in files],
                        )
                    )

        # Return the finalized plan result for the orchestrator to execute.
        return _PlanResult(
            all_work_units=units,
            work_units_to_process=units,
        )


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Run the AI Codebase Indexer")
    parser.add_argument(
        # Continuation of processing logic.
        "--input_dir", type=str, required=True, help="Path to the source code to index"
    )
    parser.add_argument(
        "--output_dir", type=str, required=True, help="Path to write the generated index"
    )
    parser.add_argument(
        "--bundle_name", type=str, default="local_project", help="Name of the bundle"
    )
    parser.add_argument(
        "--dry_run", action="store_true", help="Perform a dry run with mocked LLM responses"
    # Continuation of processing logic.
    )
    # Continuation of processing logic.
    parser.add_argument(
        "--reindex", action="store_true", help="Perform an incremental re-indexing run"
    )

    # Parse command line arguments to configure the execution environment.
    args = parser.parse_args()

    # Apply CLI flags to shared_flags to control global pipeline behavior.
    shared_flags.config.pipeline.dry_run = args.dry_run
    if args.dry_run:
        # Enable mock fallback if dry run is requested.
        shared_flags.config.llm.allow_mock_fallback = True
        
    # Pick up API key from environment for local execution.
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        shared_flags.config.llm.google_api_key = api_key
        # We also need to set use_vertex_ai to False to use the direct API instead.
        shared_flags.config.llm.use_vertex_ai = False
        
    # Validate that an API key is provided for real execution runs.
    if not args.dry_run and not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is required when not performing a dry run.")
        sys.exit(1)
    
    config = BundleConfig(
        bundle_name=args.bundle_name,
        input_dirs=[args.input_dir],
        output_dir=args.output_dir,
    )

    try:
        # Launch the main indexing execution flow.
        execute_indexing(config, reindex=args.reindex)
        print("Indexing completed successfully.")
    except Exception as e:
        print(f"Indexing failed: {e}")
        sys.exit(1)
