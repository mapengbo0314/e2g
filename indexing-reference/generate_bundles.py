"""Main file for running the AI Codebase Indexer on project configured bundles."""

from collections.abc import Iterator, Sequence
import concurrent.futures
import contextlib
import dataclasses
import os
import random
import re
import shutil
import string
import tempfile
import threading
from typing import cast

from absl import app
from absl import flags
from absl import logging
from google.genai import types

from mono.coresystems.data.excellence.applications.indexing import bundle_storage
from mono.coresystems.data.excellence.applications.indexing import chunker
from mono.coresystems.data.excellence.applications.indexing import github_cloner
from mono.coresystems.data.excellence.applications.indexing import llm_indexer
from mono.coresystems.data.excellence.applications.indexing import orchestrator
from mono.coresystems.data.excellence.applications.indexing import reindexing
from mono.coresystems.data.excellence.applications.indexing import sequential_llm_prompter
from mono.coresystems.data.excellence.applications.indexing import shared_flags
from mono.coresystems.data.excellence.applications.indexing import state
from mono.coresystems.data.excellence.applications.indexing import summary_merger
from mono.coresystems.data.excellence.applications.indexing import work_unit
from mono.coresystems.data.excellence.applications.indexing.change_detection import change_detection_strategy as change_detection_strategy_lib
from mono.coresystems.data.excellence.applications.indexing.change_detection import git_change_detection_strategy
from mono.coresystems.data.excellence.applications.indexing.change_detection import monorepo_change_detection_strategy
from mono.coresystems.data.excellence.applications.indexing.config import bundle_pb2
from mono.coresystems.data.excellence.applications.indexing.config import indexer_config as indexer_config_lib
from mono.coresystems.data.excellence.applications.indexing.filesystem import factory
from mono.coresystems.data.excellence.applications.indexing.filesystem import file_system_manager_base
from mono.coresystems.data.excellence.applications.indexing.index_expert import billing_labels
from mono.coresystems.data.excellence.applications.indexing.index_expert import util as index_expert_util
from mono.coresystems.data.excellence.applications.indexing.indexer import metrics
from mono.coresystems.data.excellence.applications.indexing.indexer import path_filtering_config
from mono.coresystems.data.excellence.applications.indexing.planner import planner as planner_lib
from mono.coresystems.data.excellence.infra.utils import llm_throttler
from mono.coresystems.data.excellence.infra.utils import stat_recorder


_REINDEX = shared_flags.REINDEX
_NUM_EPOCHS = shared_flags.NUM_EPOCHS
_GEMINI_MODEL = shared_flags.GEMINI_MODEL
_MAX_LLM_RETRIES = shared_flags.MAX_LLM_RETRIES
_MAX_ATTEMPTS_PER_CONVERSATION = shared_flags.MAX_ATTEMPTS_PER_CONVERSATION
_MAX_WORKERS = shared_flags.MAX_WORKERS
_MAX_CHUNK_PARALLELIZATION = shared_flags.MAX_CHUNK_PARALLELIZATION
_MAX_LLM_PARALLELIZATION = shared_flags.MAX_LLM_PARALLELIZATION
_MAX_PARALLEL_BUNDLES = shared_flags.MAX_PARALLEL_BUNDLES
_BUNDLE_NAMES = shared_flags.BUNDLE_NAMES
_UNINDEXED_BUNDLES_ONLY = flags.DEFINE_boolean(
    "unindexed_bundles_only",
    default=False,
    help="If true, only generate bundles that have not been indexed before.",
)
_BUNDLE_CONFIG_DIR = shared_flags.BUNDLE_CONFIG_DIR
_BUNDLE_OUTPUT_DIR = shared_flags.BUNDLE_OUTPUT_DIR


@contextlib.contextmanager
def custom_temporary_directory(prefix: str = "") -> Iterator[str]:
    """Creates a temporary directory with a 2-character random suffix."""
    temp_dir_root = tempfile.gettempdir()
    chars = string.ascii_letters + string.digits
    for _ in range(1000):  # Limit attempts to avoid infinite loop
        suffix = "".join(random.choice(chars) for _ in range(2))
        dir_name = os.path.join(temp_dir_root, prefix + suffix)
        try:
            os.mkdir(dir_name)
            try:
                yield dir_name
            finally:
                shutil.rmtree(dir_name)
            return
        except FileExistsError:
            continue
    raise FileExistsError(
        "Could not create temporary directory with 2-char suffix."
    )


def _execute_indexing(
    bundle: bundle_pb2.ProjectBundle,
    fs_manager: file_system_manager_base.FileSystemManagerBase,
    reindex: bool,
    config: indexer_config_lib.IndexerConfig,
    input_directories: Sequence[str],
    output_dir: str,
    llm_prompter: sequential_llm_prompter.LlmPrompter,
    work_unit_storage: work_unit.WorkUnitStorage,
    commit_shas: Sequence[str] | None = None,
    codebase_specific_context: str | None = None,
    change_detection_strategy: (
        change_detection_strategy_lib.ChangeDetectionStrategy | None
    ) = None,
    state_impl: state.State | None = None,
) -> None:
    """Runs one iteration of indexing."""
    if state_impl is not None:
        index_state = state_impl
    else:
        index_state = state.LocalState(
            state_dir=output_dir,
            fs_manager=fs_manager,
            input_prefix_to_strip=config.input_prefix_to_strip,
        )

    if change_detection_strategy is not None:
        effective_change_detection_strategy = change_detection_strategy
    else:
        last_indexed_info = work_unit_storage.read().last_indexed_info
        if bundle.HasField("git_input"):
            if commit_shas is None:
                raise ValueError(
                    f"Bundle {bundle.bundle_name} has git_input but no commit shas."
                )
            new_shas = [
                git_change_detection_strategy.CommitSha(s) for s in commit_shas
            ]
            if last_indexed_info.is_empty():
                old_shas = []
            elif last_indexed_info.is_commit_based():
                old_shas = [
                    git_change_detection_strategy.CommitSha(s)
                    for s in cast(Sequence[str], last_indexed_info.commit_identifier)
                ]
            else:
                # Fallback if the identifier type is unexpected for a git bundle.
                old_shas = []
            effective_change_detection_strategy = (
                git_change_detection_strategy.GitChangeDetectionStrategy(
                    bundle, new_shas, old_shas
                )
            )
        else:
            cl_string = fs_manager.get_cl_number()
            if cl_string is None or not cl_string.isdigit():
                cl_number = monorepo_change_detection_strategy.DEFAULT_CL_NUMBER
            else:
                cl_number = int(fs_manager.get_cl_number())
            effective_change_detection_strategy = (
                monorepo_change_detection_strategy.monorepoChangeDetectionStrategy(
                    cl_number
                )
            )

    if not reindex:
        index_differ_instance = None
    else:
        index_differ_instance = reindexing.IndexDiffer(
            fs_manager=fs_manager,
            work_unit_storage=work_unit_storage,
            change_detection_strategy=effective_change_detection_strategy,
        )

    exclude_patterns = []
    for exclude_pattern in bundle.exclude_patterns:
        exclude_patterns.append(re.compile(exclude_pattern))
    include_patterns = []
    for include_pattern in bundle.include_patterns:
        include_patterns.append(re.compile(include_pattern))
    filtering_config = path_filtering_config.PathFilteringConfig(
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        additional_extensions=list(bundle.additional_extensions),
    )

    chunker_instance = chunker.Chunker()
    summary_merger_instance = summary_merger.SummaryMerger(
        llm_prompter_instance=llm_prompter,
        index_state=index_state,
        fs_manager=fs_manager,
        filtering_config=filtering_config,
    )

    indexer_config = llm_indexer.LlmIndexerConfig(
        llm_prompter=llm_prompter,
        index_state=index_state,
        chunker=chunker_instance,
        summary_merger=summary_merger_instance,
        max_dir_size=config.max_dir_size,
        config=config,
        include_search_tool=(not bundle.HasField("git_input")),
        codebase_specific_context=codebase_specific_context,
        filtering_config=filtering_config,
        custom_sections=bundle.custom_sections,
    )

    indexer = llm_indexer.LlmIndexer(indexer_config, fs_manager)

    planner_instance = planner_lib.Planner(
        fs_manager=fs_manager,
        root_dirs=input_directories,
        filtering_config=filtering_config,
        index_differ=index_differ_instance,
        bundle_name=bundle.bundle_name,
        input_prefix_to_strip=config.input_prefix_to_strip,
        max_work_unit_size_bytes=config.max_work_unit_size_bytes,
    )

    indexer_orchestrator = orchestrator.Orchestrator(
        planner_instance=planner_instance,
        indexer=indexer,
        num_epochs=_NUM_EPOCHS.value,
        root_map_dir=output_dir,
        index_state=index_state,
        work_unit_storage=work_unit_storage,
        max_workers=_MAX_WORKERS.value,
        bundle_name=bundle.bundle_name,
        max_chunk_parallelization=_MAX_CHUNK_PARALLELIZATION.value,
        fs_manager=fs_manager,
        input_prefix_to_strip=config.input_prefix_to_strip,
        change_detection_strategy=effective_change_detection_strategy,
        indexer_type=metrics.IndexerType.REGULAR,
    )

    indexer_orchestrator.run()


def _generate_github_bundle(
    bundle: bundle_pb2.ProjectBundle,
    fs_manager: file_system_manager_base.FileSystemManagerBase,
    reindex: bool,
    config: indexer_config_lib.IndexerConfig,
    bundle_storage_impl: bundle_storage.BundleStorageBase,
    llm_prompter: sequential_llm_prompter.LlmPrompter,
    work_unit_storage: work_unit.WorkUnitStorage,
    codebase_specific_context: str | None = None,
    change_detection_strategy: (
        change_detection_strategy_lib.ChangeDetectionStrategy | None
    ) = None,
    state_impl: state.State | None = None,
):
    """Runs indexing for a single github bundle."""
    use_subdirs = len(bundle.git_input.repository_input) > 1
    if bundle.git_input.versioning.commit_shas:
        if len(bundle.git_input.versioning.commit_shas) > 1:
            raise ValueError(f"Bundle {bundle.bundle_name} has multiple commit shas.")
        commit_sha = bundle.git_input.versioning.commit_shas[0]
    else:
        commit_sha = None

    print(f"Indexing repositories for commit: {commit_sha or 'HEAD'}")
    with custom_temporary_directory(prefix=f"{bundle.bundle_name}_") as tmpdir:
        cloned_repo_dirs = []
        actual_commit_shas = []
        for repo in bundle.git_input.repository_input:
            repo_subdir = os.path.join(tmpdir, repo.name) if use_subdirs else tmpdir
            repo_path, repo_sha = github_cloner.clone_repository(
                repo, repo_subdir, commit_sha=commit_sha
            )
            cloned_repo_dirs.append(repo_path)
            actual_commit_shas.append(repo_sha)

        commit_config = config
        commit_config = dataclasses.replace(
            commit_config, input_prefix_to_strip=tmpdir
        )

        _execute_indexing(
            bundle=bundle,
            fs_manager=fs_manager,
            reindex=reindex,
            config=commit_config,
            input_directories=cloned_repo_dirs,
            output_dir=bundle_storage_impl.get_bundle_output_dir(bundle),
            llm_prompter=llm_prompter,
            work_unit_storage=work_unit_storage,
            commit_shas=actual_commit_shas,
            codebase_specific_context=codebase_specific_context,
            change_detection_strategy=change_detection_strategy,
            state_impl=state_impl,
        )


def _generate_regular_bundle(
    bundle: bundle_pb2.ProjectBundle,
    fs_manager: file_system_manager_base.FileSystemManagerBase,
    reindex: bool,
    config: indexer_config_lib.IndexerConfig,
    bundle_storage_impl: bundle_storage.BundleStorageBase,
    llm_prompter: sequential_llm_prompter.LlmPrompter,
    work_unit_storage: work_unit.WorkUnitStorage,
    codebase_specific_context: str | None = None,
    change_detection_strategy: (
        change_detection_strategy_lib.ChangeDetectionStrategy | None
    ) = None,
    state_impl: state.State | None = None,
):
    """Runs indexing for a single regular bundle."""
    effective_config = config
    _execute_indexing(
        bundle=bundle,
        fs_manager=fs_manager,
        reindex=reindex,
        config=effective_config,
        input_directories=bundle_storage_impl.get_bundle_input_dirs(bundle),
        output_dir=bundle_storage_impl.get_bundle_output_dir(bundle),
        llm_prompter=llm_prompter,
        work_unit_storage=work_unit_storage,
        codebase_specific_context=codebase_specific_context,
        change_detection_strategy=change_detection_strategy,
        state_impl=state_impl,
    )


def generate_bundle(
    bundle: bundle_pb2.ProjectBundle,
    fs_manager: file_system_manager_base.FileSystemManagerBase,
    llm_prompter: sequential_llm_prompter.LlmPrompter,
    work_unit_storage: work_unit.WorkUnitStorage,
    reindex: bool | None = None,
    codebase_specific_context: str | None = None,
    change_detection_strategy: (
        change_detection_strategy_lib.ChangeDetectionStrategy | None
    ) = None,
    bundle_storage_impl: bundle_storage.BundleStorageBase | None = None,
    state_impl: state.State | None = None,
):
    """Runs indexing for a single bundle."""
    try:
        if reindex is None:
            reindex = _REINDEX.value

        if bundle_storage_impl is None:
            bundle_storage_impl = bundle_storage.BundleStorage(
                fs_manager, _BUNDLE_CONFIG_DIR.value, _BUNDLE_OUTPUT_DIR.value
            )

        if bundle.HasField("git_input"):
            if bundle.inputs:
                raise ValueError(
                    f"Bundle {bundle.bundle_name} has git_input and input set."
                )

        print(f"Bundle generation starting for {bundle.bundle_name}.")
        stats = stat_recorder.get_instance()
        stats.set_gauge("bundle_name", bundle.bundle_name)

        indexer_configs = indexer_config_lib.get_configs()
        default_config = indexer_configs["default_config"]
        if bundle.HasField("indexer_config"):
            override_config = indexer_config_lib.IndexerConfig.from_proto(
                bundle.indexer_config
            )
            config = default_config.merge_with_override(override_config)
        else:
            config = default_config

        if bundle.HasField("git_input"):
            _generate_github_bundle(
                bundle,
                fs_manager,
                reindex,
                config,
                bundle_storage_impl,
                llm_prompter,
                work_unit_storage,
                codebase_specific_context,
                change_detection_strategy,
                state_impl,
            )
        else:
            _generate_regular_bundle(
                bundle,
                fs_manager,
                reindex,
                config,
                bundle_storage_impl,
                llm_prompter,
                work_unit_storage,
                codebase_specific_context,
                change_detection_strategy,
                state_impl,
            )

        print(f"Bundle generation complete for {bundle.bundle_name}.")
        metrics.BUNDLE_PROCESSED.Increment(
            metrics.IndexerType.REGULAR.value,
            bundle.bundle_name,
            metrics.Status.SUCCESS.value,
        )
    except Exception as e:
        metrics.BUNDLE_PROCESSED.Increment(
            metrics.IndexerType.REGULAR.value,
            bundle.bundle_name,
            metrics.Status.FAILURE.value,
        )
        metrics.GENERAL_FAILURES.Increment(
            metrics.IndexerType.REGULAR.value,
            bundle.bundle_name,
            type(e).__name__,
            str(getattr(e, "code", "UNKNOWN")) or "UNKNOWN",
        )
        print(f"Bundle generation failed for {bundle.bundle_name}: {e}")
        raise


def create_llm_prompter(
    bundle: bundle_pb2.ProjectBundle,
    throttling_strategy: llm_throttler.ThrottlingStrategy,
    fs_manager: file_system_manager_base.FileSystemManagerBase,
    generate_content_config: types.GenerateContentConfig | None = None,
) -> sequential_llm_prompter.LlmPrompter:
    """Creates an LLM prompter for a bundle."""
    include_search_tool = not bundle.HasField("git_input")
    return sequential_llm_prompter.GeminiLlmPrompter(
        sequential_llm_prompter.GeminiLlmPrompterConfig(
            bundle_name=bundle.bundle_name,
            indexer_type=metrics.IndexerType.REGULAR,
            throttling_strategy=throttling_strategy,
            max_attempts=_MAX_LLM_RETRIES.value,
            max_attempts_per_conversation=_MAX_ATTEMPTS_PER_CONVERSATION.value,
            synthesis_gemini_model=_GEMINI_MODEL.value,
            research_gemini_model=_GEMINI_MODEL.value,
            include_search_tool=include_search_tool,
            generate_content_config=generate_content_config,
        ),
        fs_manager=fs_manager,
    )


def create_throttling_strategy() -> llm_throttler.ThrottlingStrategy:
    """Creates a throttling strategy based on flag values."""
    if shared_flags.LLM_THROTTLING_STRATEGY.value == "semaphore":
        logging.info(
            "Using semaphore throttling strategy with max parallelization %d.",
            shared_flags.MAX_LLM_PARALLELIZATION.value,
        )
        return llm_throttler.SemaphoreAdapter(
            threading.Semaphore(shared_flags.MAX_LLM_PARALLELIZATION.value)
        )
    elif shared_flags.LLM_THROTTLING_STRATEGY.value == "token_bucket":
        logging.info(
            "Using token bucket throttling strategy with token limit %d.",
            shared_flags.LLM_TOKEN_LIMIT_PER_MINUTE.value,
        )
        return llm_throttler.TokenCountThrottler(
            max_tokens_per_minute=shared_flags.LLM_TOKEN_LIMIT_PER_MINUTE.value
        )
    else:
        raise ValueError(
            "Unknown throttling strategy:"
            f" {shared_flags.LLM_THROTTLING_STRATEGY.value}"
        )


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    if shared_flags.QUIET.value:
        logging.set_verbosity(logging.WARNING)
    if shared_flags.DEBUG_MODE.value:
        logging.set_verbosity(logging.DEBUG)

    with stat_recorder.get_instance() as stats:
        fs_manager = factory.make_fs_manager()
        bundle_storage_impl = bundle_storage.BundleStorage(
            fs_manager, _BUNDLE_CONFIG_DIR.value, _BUNDLE_OUTPUT_DIR.value
        )
        try:
            included_bundle_names = set(_BUNDLE_NAMES.value)
            bundle_configs = bundle_storage_impl.get_bundles(
                included_bundle_names
            )
            if _UNINDEXED_BUNDLES_ONLY.value:
                bundle_configs = [
                    b
                    for b in bundle_configs
                    if not bundle_storage_impl.is_bundle_indexed(b)
                ]
            stats.set_gauge(
                "bundles_to_process", [b.bundle_name for b in bundle_configs]
            )

            print(f"Beginning bundle generation for {len(bundle_configs)} bundles.")
            throttling_strategy = create_throttling_strategy()
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=_MAX_PARALLEL_BUNDLES.value
            ) as executor:
                futures = {
                    executor.submit(
                        generate_bundle,
                        bundle=bundle_config,
                        fs_manager=fs_manager,
                        llm_prompter=create_llm_prompter(
                            bundle_config,
                            throttling_strategy,
                            fs_manager=fs_manager,
                            generate_content_config=index_expert_util.get_billing_config(
                                billing_labels.Recursive-IndexBillingLabel.GENERATE_BUNDLES,
                            ),
                        ),
                        work_unit_storage=work_unit.FsWorkUnitStorage(
                            fs_manager,
                            bundle_storage_impl.get_bundle_output_dir(bundle_config),
                        ),
                        bundle_storage_impl=bundle_storage_impl,
                    ): bundle_config
                    for bundle_config in bundle_configs
                }
                for future in concurrent.futures.as_completed(futures):
                    bundle_config = futures[future]
                    try:
                        future.result()
                    except Exception as exc:  # pylint: disable=broad-except
                        print(
                            f"Bundle {bundle_config.bundle_name} generated an exception:"
                            f" {exc}"
                        )
                        logging.exception(
                            "Bundle %s generated an exception: %s",
                            bundle_config.bundle_name,
                            exc,
                        )
        finally:
            print(stats.get_report())


if __name__ == "__main__":
    app.run(main)
