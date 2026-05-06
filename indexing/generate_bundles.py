"""Main entrypoint for running the AI Codebase Indexer on project bundles.

This script provides a programmatic API for running the indexing pipeline
against local directories and Git repositories.
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
import tempfile
import threading
# Base types for defining structured data in the indexing pipeline.
from typing import Any

# Internal project module imports for the indexing pipeline components.
from indexing import chunker
from indexing import github_cloner
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
    repo_root: str | None = None,
) -> sequential_llm_prompter.LlmPrompter:
    """Creates an LLM prompter for a bundle."""
    llm_cfg = shared_flags.config.llm
    # Return the configured prompter instance for the indexing lifecycle.
    return sequential_llm_prompter.UniversalLlmPrompter(
        sequential_llm_prompter.UniversalLlmConfig(
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
            provider=llm_cfg.provider.value,
            api_key=llm_cfg.api_key,
            # Dry run and mock fallback flags.
            dry_run=shared_flags.config.pipeline.dry_run,
            allow_mock_fallback=llm_cfg.allow_mock_fallback,
            repo_root=repo_root,
        ),
        fs_manager=fs_manager,
    )


def execute_indexing(
    bundle: BundleConfig,
    indexer_config: IndexerConfig | None = None,
    fs_manager: Any = None,
    llm_prompter: sequential_llm_prompter.LlmPrompter | None = None,
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
        bundle, throttling_strategy=throttling, fs_manager=fs_mgr, repo_root=input_prefix
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
            output_dir=output_dir,
            fs_manager=fs_mgr,
        ),
        indexer=indexer_instance,
        num_epochs=shared_flags.config.pipeline.num_epochs,
        root_map_dir=output_dir,
        index_state=index_state,
        work_unit_storage=work_unit_storage,
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
        output_dir: str | None = None,
        fs_manager: Any = None,
    ) -> None:
        self._input_dirs = input_dirs
        self._output_dir = output_dir
        self._fs_manager = fs_manager

    def plan(self) -> _PlanResult:
        from pathlib import Path

        units: list[work_unit.WorkUnit] = []
        for input_dir in self._input_dirs:
            root = Path(input_dir)
            if not root.is_dir():
                logging.warning("Input dir %s is not a directory, skipping.", input_dir)
                continue
            for dirpath, dirnames, filenames in os.walk(input_dir):
                # Skip hidden directories and directories that only contain
                # binary or vendored content (these always fail semantic
                # verification because no readable source context exists).
                _SKIP_DIRS = {
                    "__pycache__",
                    "node_modules",
                    ".tox",
                    ".mypy_cache",
                    ".pytest_cache",
                    ".ruff_cache",
                    # Common virtual environment directory names.
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                }
                # Skip the output directory if it's nested within the input directory
                # to avoid indexing our own generated artifacts.
                if self._output_dir:
                    out_path = Path(self._output_dir).resolve()
                    dirnames[:] = [
                        d for d in dirnames
                        if Path(os.path.join(dirpath, d)).resolve() != out_path
                    ]

                dirnames[:] = [
                    d for d in dirnames
                    if not d.startswith(".")
                    and d not in _SKIP_DIRS
                    and not d.endswith(".venv")  # e.g. _generate_bundles.venv
                ]
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
        "--config", type=str, required=False, help="Path to a .textproto bundle configuration file"
    )
    parser.add_argument(
        "--output_dir", type=str, required=False, help="Optional override for the output directory"
    )
    parser.add_argument(
        "--dry_run", action="store_true", help="Perform a dry run with mocked LLM responses"
    )
    parser.add_argument(
        "--reindex", action="store_true", help="Perform an incremental re-indexing run"
    )
    parser.add_argument(
        "--llm_provider", type=str, choices=["gemini", "openai", "anthropic", "ollama"], default="gemini",
        help="The LLM provider to use for indexing"
    )
    parser.add_argument(
        "--model_name", type=str, help="The specific model to use for the selected provider"
    )
    parser.add_argument(
        "--repo_url", type=str, required=False, help="Optional override for the repository URL"
    )

    # Parse command line arguments to configure the execution environment.
    args = parser.parse_args()

    # Resolve absolute paths if running under Bazel to ensure outputs land in the workspace.
    workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if workspace_dir:
        if args.config and not os.path.isabs(args.config):
            args.config = os.path.normpath(os.path.join(workspace_dir, args.config))
        if args.output_dir and not os.path.isabs(args.output_dir):
            args.output_dir = os.path.normpath(os.path.join(workspace_dir, args.output_dir))
            # Ensure the output directory exists in the workspace if provided.
            os.makedirs(args.output_dir, exist_ok=True)

    # Load bundle from config if provided, otherwise create a transient one.
    if args.config:
        try:
            from indexing.scripts import bundle_verifier
            bundle_from_proto = bundle_verifier.parse_config(args.config)
            print(f"Loaded configuration from {args.config}")
        except Exception as e:
            print(f"ERROR: Failed to parse config {args.config}: {e}")
            sys.exit(1)
    else:
        # Create a default bundle if no config is provided but we have other inputs.
        from indexing.config import bundle_pb2
        bundle_from_proto = bundle_pb2.ProjectBundle()
        bundle_from_proto.bundle_name = "transient_bundle"
        print("Using transient bundle configuration.")

    # Apply CLI flags to shared_flags to control global pipeline behavior.
    shared_flags.config.pipeline.dry_run = args.dry_run
    if args.dry_run:
        # Enable mock fallback if dry run is requested.
        shared_flags.config.llm.allow_mock_fallback = True
        
    # Configure the provider globally.
    shared_flags.config.llm.provider = shared_flags.LlmProvider(args.llm_provider)

    # Ensure the user has explicitly specified a model name.
    if not args.model_name:
        print("ERROR: --model_name must be explicitly provided.")
        sys.exit(1)
    shared_flags.config.llm.model = args.model_name

    # Resolve API key environment variable based on provider.
    if args.llm_provider == "gemini":
        env_var = "GEMINI_API_KEY"
    elif args.llm_provider == "openai":
        env_var = "OPENAI_API_KEY"
    elif args.llm_provider == "anthropic":
        env_var = "ANTHROPIC_API_KEY"
    elif args.llm_provider == "ollama":
        env_var = None  # Ollama operates locally and does not require an API key.
    else:
        env_var = "LLM_API_KEY"

    # Default api_key state to None and fetch from environment if needed.
    api_key = None
    if env_var:
        # Pick up API key from environment for local execution.
        api_key = os.environ.get(env_var)
        if api_key:
            shared_flags.config.llm.api_key = api_key
            
    # Validate that an API key is provided for real execution runs (except for local providers).
    if not args.dry_run and env_var and not api_key:
        print(f"ERROR: {env_var} environment variable is required when not performing a dry run.")
        sys.exit(1)
    
    def run_with_config(input_paths: list[str], bundle_name: str, output_dir: str, exclude_patterns: list[str] = None, include_patterns: list[str] = None, custom_sections: list[Any] = None):
        config = BundleConfig(
            bundle_name=bundle_name,
            input_dirs=input_paths,
            output_dir=output_dir,
            exclude_patterns=exclude_patterns or [],
            include_patterns=include_patterns or [],
            custom_sections=custom_sections or [],
        )
        try:
            # Launch the main indexing execution flow.
            execute_indexing(config, reindex=args.reindex)
            print("Indexing completed successfully.")
        except Exception as e:
            print(f"Indexing failed: {e}")
            sys.exit(1)

    # Resolve the output directory.
    # Prioritize CLI flag, then custom_output from proto, then default.
    final_output_dir = args.output_dir
    if not final_output_dir and bundle_from_proto.custom_output:
        final_output_dir = bundle_from_proto.custom_output.output_directory
    
    if not final_output_dir:
        # Fallback if neither CLI nor proto specifies an output directory.
        final_output_dir = "./index_out"
    
    # Ensure absolute path for output dir.
    if not os.path.isabs(final_output_dir) and workspace_dir:
        final_output_dir = os.path.normpath(os.path.join(workspace_dir, final_output_dir))
    os.makedirs(final_output_dir, exist_ok=True)

    # Resolve the repository URL (CLI flag overrides config).
    repo_url = args.repo_url
    if not repo_url and bundle_from_proto.git_input and bundle_from_proto.git_input.repository_input:
        repo_url = bundle_from_proto.git_input.repository_input[0].repository_url

    # Process based on the resolved input source.
    if repo_url:
        # Handle git input (cloning).
        with custom_temporary_directory(prefix="repo_clone_") as temp_dir:
            cloner = github_cloner.GithubCloner()
            if cloner.clone(repo_url, temp_dir):
                run_with_config(
                    [temp_dir], 
                    bundle_from_proto.bundle_name, 
                    final_output_dir,
                    bundle_from_proto.exclude_pattern, 
                    bundle_from_proto.include_pattern, 
                    bundle_from_proto.custom_sections
                )
            else:
                print(f"ERROR: Failed to clone repository {repo_url}")
                sys.exit(1)
    elif bundle_from_proto.input:
        # Handle local inputs from proto.
        input_paths = []
        for inp in bundle_from_proto.input:
            path = inp.directory
            if workspace_dir and not os.path.isabs(path):
                path = os.path.normpath(os.path.join(workspace_dir, path))
            input_paths.append(path)
            
        run_with_config(
            input_paths, 
            bundle_from_proto.bundle_name, 
            final_output_dir,
            bundle_from_proto.exclude_pattern, 
            bundle_from_proto.include_pattern, 
            bundle_from_proto.custom_sections
        )
    else:
        print(f"ERROR: Bundle {bundle_from_proto.bundle_name} has no valid input sources.")
        sys.exit(1)
