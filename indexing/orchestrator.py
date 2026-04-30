"""Orchestrates the AI Codebase Indexer.

This module is responsible for actually walking the directory, handling parallel
processing, and calling the LlmIndexer to generate the index for each
directory.
"""

import collections
from collections.abc import Sequence
import concurrent.futures
import datetime
import logging
from typing import Any, Protocol

from indexing import file_utils
from indexing import llm_indexer
from indexing import reindexing
from indexing import root_map
from indexing import schema
from indexing import state
from indexing import verification
from indexing import work_unit as work_unit_lib
import tenacity


WorkUnit = work_unit_lib.WorkUnit

# Maximum number of work units to process in a single epoch. This cutoff is to
# prevent large bundles from taking too long to index. Moreover, we wouldn't
# be able to check them into monorepo anyway.
_MAX_WORK_UNITS_TO_PROCESS = 5000


# ---------- Minimal stubs for removed upstream deps ----------

class _NoOpCounter:
    def increment(self, *args: Any, **kwargs: Any) -> None:
        return None

    def Increment(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        return None

    def Set(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        return None


class _Metrics:
    WORK_UNITS_PROCESSED = _NoOpCounter()
    GENERAL_FAILURE = _NoOpCounter()
    GENERAL_FAILURES = _NoOpCounter()
    WORK_UNITS_TO_PROCESS = _NoOpCounter()

    class Status:
        SUCCESS = type("Status", (), {"value": "SUCCESS"})()
        FAILURE = type("Status", (), {"value": "FAILURE"})()

    class IndexerType:
        REGULAR = type("IndexerType", (), {"value": "REGULAR"})()


metrics = _Metrics()


class _SimpleStatsRecorder:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, Any] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def reset_counter(self, name: str) -> None:
        self._counters[name] = 0

    def set_gauge(self, name: str, value: Any) -> None:
        self._gauges[name] = value


_stats_instance = _SimpleStatsRecorder()


class _SimpleProgressManager:
    """Stand-in for the upstream ProgressManager."""

    def __init__(self, root_map_dir: str, fs_manager: Any) -> None:
        self._root_map_dir = root_map_dir
        self._fs_manager = fs_manager

    def get_progress_file(self, epoch: int) -> str:
        return f"{self._root_map_dir}/progress_epoch_{epoch}.json"

    def read_progress(self, epoch: int) -> dict[str, str]:
        import json
        path = self.get_progress_file(epoch)
        try:
            return json.loads(self._fs_manager.read(path))
        except Exception:
            return {}

    def write_progress(self, epoch: int, data: dict[str, str]) -> None:
        import json
        path = self.get_progress_file(epoch)
        self._fs_manager.write(path, json.dumps(data))

    def mark_work_unit_completed(self, output_path: str, epoch: int) -> None:
        progress = self.read_progress(epoch)
        progress[output_path] = "COMPLETED"
        self.write_progress(epoch, progress)

    def delete_progress_file(self, epoch: int) -> None:
        path = self.get_progress_file(epoch)
        try:
            self._fs_manager.delete(path)
        except Exception:
            pass


class PlannerBase(Protocol):
    """Protocol for planner implementations."""

    def plan(self) -> Any: ...


class FileSystemManagerProtocol(Protocol):
    """Minimal protocol for the filesystem manager used by the orchestrator."""

    def normpath(self, path: str) -> str: ...
    def sep(self) -> str: ...
    def make_dirs(self, path: str) -> None: ...
    def exists(self, path: str) -> bool: ...
    def read(self, path: str) -> str: ...
    def write(self, path: str, content: str) -> None: ...
    def join(self, *parts: str) -> str: ...
    def delete(self, path: str) -> None: ...


class LocalFileSystemManager:
    """A simple local filesystem manager."""

    import os as _os
    import pathlib as _pathlib

    def normpath(self, path: str) -> str:
        return self._os.path.normpath(path)

    def sep(self) -> str:
        return self._os.sep

    def make_dirs(self, path: str) -> None:
        self._os.makedirs(path, exist_ok=True)

    def exists(self, path: str) -> bool:
        return self._os.path.exists(path)

    def read(self, path: str) -> str:
        return self._pathlib.Path(path).read_text()

    def write(self, path: str, content: str) -> None:
        self._pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._pathlib.Path(path).write_text(content)

    def join(self, *parts: str) -> str:
        return self._os.path.join(*parts)

    def delete(self, path: str) -> None:
        try:
            self._os.remove(path)
        except FileNotFoundError:
            pass


class ChangeDetectionStrategy(Protocol):
    """Protocol for change detection."""

    def get_current_commit_id(self) -> work_unit_lib.CommitIdentifier: ...


class Orchestrator:
    """Class to orchestrate the multi-epoch indexing process."""

    def __init__(
        self,
        *,
        planner_instance: Any,
        indexer: llm_indexer.LlmIndexer,
        num_epochs: int,
        root_map_dir: str,
        index_state: state.State,
        work_unit_storage: work_unit_lib.WorkUnitStorage,
        max_workers: int = 16,
        fs_manager: Any = None,
        bundle_name: str | None = None,
        max_chunk_parallelization: int | None = None,
        input_prefix_to_strip: str | None = None,
        change_detection_strategy: Any = None,
        generate_root_map: bool = True,
        perform_fs_checkpointing: bool = True,
        indexer_type: Any = None,
    ):
        """Initializes the Orchestrator.

        Args:
            planner_instance: The planner instance to determine work units and
                subsequent epochs.
            indexer: LlmIndexer instance for the first and subsequent epochs.
            num_epochs: The total number of indexing passes to run.
            root_map_dir: The directory to write the root map files to.
            index_state: The state object for reading and writing index files.
            work_unit_storage: The work unit storage object for reading and writing
                work unit manifests.
            max_workers: Number of threads for parallel execution.
            fs_manager: A file system manager to use for file operations.
            bundle_name: The name of the bundle being indexed.
            max_chunk_parallelization: The maximum number of chunks to process in
                parallel. If None, defaults to max_workers.
            input_prefix_to_strip: If provided, this prefix will be stripped from
                paths in the work units.
            change_detection_strategy: An optional change detection strategy to use
                for reindexing.
            generate_root_map: Whether to generate the root map after each epoch.
            perform_fs_checkpointing: Whether to perform checkpointing to file system.
            indexer_type: The type of indexer being used.
        """
        self._planner = planner_instance
        self._num_epochs = num_epochs
        self._index_state = index_state
        self._work_unit_storage = work_unit_storage
        self._max_workers = max_workers
        self._fs_manager = fs_manager or LocalFileSystemManager()
        self._bundle_name = bundle_name or "unknown_bundle"
        self._input_prefix_to_strip = input_prefix_to_strip
        self._change_detection_strategy = change_detection_strategy
        self._generate_root_map = generate_root_map
        self._perform_fs_checkpointing = perform_fs_checkpointing
        self._indexer_type = indexer_type or metrics.IndexerType.REGULAR

        self._root_map_dir = self._fs_manager.normpath(root_map_dir)

        if self._perform_fs_checkpointing or self._generate_root_map:
            self._fs_manager.make_dirs(self._root_map_dir)

        if self._perform_fs_checkpointing:
            self._progress_manager = _SimpleProgressManager(
                self._root_map_dir, self._fs_manager
            )

        self._indexer = indexer
        self._max_chunk_parallelization = (
            max_chunk_parallelization if max_chunk_parallelization else max_workers
        )

    def _run_epoch(
        self, work_units: Sequence[WorkUnit], epoch: int
    ) -> dict[str, bool]:
        """Runs a single indexing epoch, aggregating small directories.

        The indexing process is iterative. In each epoch, the orchestrator:
        1. Determines which work units require indexing or reindexing based on file
           changes, if reindexing is enabled.
        2. Processes work units in parallel, starting from the deepest directories
           and moving upwards.
        3. For each work unit, it calls an LlmIndexer to generate an index file.
        4. After processing all work units in an epoch, it regenerates the root
           map, which summarizes the indexes generated in that epoch.

        Args:
            work_units: A sequence of WorkUnits objects to be processed in this epoch.
            epoch: the current epoch number (0-indexed).

        Returns:
            A dictionary of work unit paths to whether the work unit was processed
            successfully.
        """
        _stats_instance.set_gauge(
            f"{self._bundle_name}.current_epoch", f"{epoch + 1}/{self._num_epochs}"
        )
        _stats_instance.reset_counter(f"{self._bundle_name}.epoch.dirs.processed")
        _stats_instance.reset_counter(
            f"{self._bundle_name}.epoch.work_units.processed"
        )

        # Process all work units and take care of progress tracker later.
        work_units_to_process = list(work_units)

        if self._change_detection_strategy and epoch == 0:
            differ = reindexing.IndexDiffer(
                fs_manager=self._fs_manager,
                work_unit_storage=self._work_unit_storage,
                change_detection_strategy=self._change_detection_strategy
            )
            diff = differ.get_work_units_to_reindex(work_units)
            work_units_to_process = list(diff.to_reindex)
            logging.info(
                "Epoch %d: Incremental indexing filtered %d -> %d work units.",
                epoch, len(work_units), len(work_units_to_process)
            )

        if self._perform_fs_checkpointing:
            progress_file = self._progress_manager.get_progress_file(epoch)
            if self._fs_manager.exists(progress_file):
                logging.info(
                    "Epoch %d: Progress file exists, loading progress file.", epoch
                )
                epoch_progress = self._progress_manager.read_progress(epoch)
                initial_count = len(work_units_to_process)
                work_units_to_process = [
                    wu
                    for wu in work_units_to_process
                    if epoch_progress.get(str(wu.output_path)) != "COMPLETED"
                ]
                logging.info(
                    "Epoch %d: Loaded progress, %d work units already completed.",
                    epoch,
                    initial_count - len(work_units_to_process),
                )
            else:
                epoch_progress_to_write = {
                    str(wu.output_path): "PENDING" for wu in work_units_to_process
                }
                self._progress_manager.write_progress(epoch, epoch_progress_to_write)

        _stats_instance.set_gauge(
            f"{self._bundle_name}.epoch.work_units.total", len(work_units)
        )

        if not work_units_to_process:
            logging.info("Epoch %d: No work units to index.", epoch)
            return {}

        logging.info(
            "Epoch %d: Found %d work units to process.",
            epoch,
            len(work_units_to_process),
        )

        # Group work units by path depth to process deepest first.
        work_units_by_depth: dict[int, list[WorkUnit]] = collections.defaultdict(list)
        for wu in work_units_to_process:
            depth = len([
                part
                for part in self._fs_manager.normpath(str(wu.output_path)).split(
                    self._fs_manager.sep()
                )
                if part and part != "."
            ])
            work_units_by_depth[depth].append(wu)

        sorted_depths = sorted(work_units_by_depth.keys(), reverse=True)
        results: dict[str, bool] = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers
        ) as executor:
            for depth in sorted_depths:
                units_to_process = work_units_by_depth[depth]
                logging.info(
                    "Epoch %d: Processing %d work units of depth %d.",
                    epoch,
                    len(units_to_process),
                    depth,
                )

                futures: dict[str, concurrent.futures.Future[bool]] = {
                    str(wu.output_path): executor.submit(
                        self._process_work_unit, wu, epoch
                    )
                    for wu in units_to_process
                }

                exceptions_raised: list[Exception] = []
                for work_unit_path, future in futures.items():
                    try:
                        results[work_unit_path] = future.result()
                    except Exception as e:
                        logging.error(
                            "Error processing %s in epoch %d: %s",
                            work_unit_path,
                            epoch,
                            e,
                        )
                        exceptions_raised.append(e)
                        for f in futures.values():
                            f.cancel()

                if exceptions_raised:
                    raise exceptions_raised[0]

        return results

    def _process_work_unit(self, work_unit: WorkUnit, epoch: int) -> bool:
        """Processes a single work unit for the given epoch."""
        _stats_instance.increment_counter(
            f"{self._bundle_name}.work_units.processed"
        )
        _stats_instance.increment_counter(
            f"{self._bundle_name}.epoch.work_units.processed"
        )

        previous_root_map_content = ""
        if epoch > 0:
            previous_root_map_file = self._fs_manager.join(
                self._root_map_dir, f"root_map_v{epoch - 1}.md"
            )
            try:
                previous_root_map_content = self._fs_manager.read(
                    previous_root_map_file
                )
            except FileNotFoundError:
                logging.warning(
                    "Previous root map not found: %s", previous_root_map_file
                )
        logging.info(
            "Generating Index for %s epoch %d...", work_unit.output_path, epoch
        )

        from pathlib import Path
        verifier = verification.ArtifactVerifier(
            llm_prompter=self._indexer._config.llm_prompter,
            cache_dir=Path(self._fs_manager.join(self._root_map_dir, "verification_cache"))
        )

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
        )
        def _generate_and_verify():
            result = self._indexer.generate_index_for_work_unit(
                work_unit,
                epoch,
                previous_root_map_content,
                self._max_chunk_parallelization,
                self._input_prefix_to_strip,
                verifier=verifier,
            )
            
            if not result.success or not result.artifact:
                return result
                
            artifact_json = result.artifact.model_dump_json(indent=2)
            verdict = verifier.verify(artifact_json, result.source_context)
            
            if not verdict.passed:
                self._indexer._config.verification_issues = verdict.issues
                raise Exception(f"Verification failed: {verdict.issues}")
                
            self._indexer._config.verification_issues = []
            return result

        try:
            work_unit_result = _generate_and_verify()
        except Exception as e:
            logging.error(
                "Error generating index for %s epoch %d: %s",
                work_unit.output_path,
                epoch,
                e,
            )
            raise

        self._index_state.write_summary(
            str(work_unit.output_path),
            epoch,
            work_unit_result.markdown_result,
        )
        if work_unit_result.artifact:
            self._index_state.write_artifact(
                str(work_unit.output_path),
                epoch,
                work_unit_result.artifact.model_dump_json(indent=2),
            )
        logging.info(
            "Successfully wrote index for %s epoch %d",
            work_unit.output_path,
            epoch,
        )
        
        # Update verification state for persistence in manifest
        work_unit.last_indexed_info = work_unit_lib.LastIndexedInfo(
            commit_identifier=self._change_detection_strategy.get_current_commit_id() if self._change_detection_strategy else ["unknown"],
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            verification_state="PASSED" if work_unit_result.success else "FAILED"
        )

        if self._perform_fs_checkpointing:
            self._progress_manager.mark_work_unit_completed(
                str(work_unit.output_path), epoch
            )

        return work_unit_result.success

    def run(self) -> None:
        """Runs the multi-epoch indexing process."""
        plan = self._planner.plan()
        all_work_units = plan.all_work_units
        work_units_to_process = plan.work_units_to_process

        if len(work_units_to_process) > _MAX_WORK_UNITS_TO_PROCESS:
            return

        logging.info(
            "Plan generated: %d units to process, %d to delete",
            len(work_units_to_process),
            len(plan.paths_to_delete),
        )

        if plan.paths_to_delete:
            logging.info("Deleting %d index files.", len(plan.paths_to_delete))
            for path in plan.paths_to_delete:
                for epoch in range(self._num_epochs):
                    self._index_state.delete_summary(str(path), epoch)

        errored_work_units: list[WorkUnit] = []
        for epoch in range(self._num_epochs):
            logging.info("Starting Epoch %d...", epoch)
            results = self._run_epoch(work_units_to_process, epoch)
            errored_work_unit_paths = [
                path for path, success in results.items() if not success
            ]
            errored_work_units.extend(
                wu
                for wu in work_units_to_process
                if str(wu.output_path) in errored_work_unit_paths
            )
            logging.info("Finished Epoch %d, writing root map...", epoch)
            if self._generate_root_map:
                root_map.regenerate_root_map(
                    all_work_units,
                    self._root_map_dir,
                    self._index_state,
                    epoch,
                    self._fs_manager,
                    self._indexer.llm_prompter,
                )
            logging.info("Finished root map for epoch %d", epoch)

        # Delete progress files after all epochs are complete
        if self._perform_fs_checkpointing:
            for epoch in range(self._num_epochs):
                self._progress_manager.delete_progress_file(epoch)

        # Only dump the work after all reindexing is done
        commit_identifier = (
            self._change_detection_strategy.get_current_commit_id()
            if self._change_detection_strategy
            else ["unknown"]
        )

        work_unit_manifest = work_unit_lib.WorkUnitManifest(
            work_units=all_work_units,
            last_indexed_info=work_unit_lib.LastIndexedInfo(
                commit_identifier=commit_identifier,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            ),
            errored_work_units=errored_work_units,
        )
        self._work_unit_storage.write(work_unit_manifest)