"""Orchestrates the AI Codebase Indexer.

This module is responsible for actually walking the directory, handling parallel
processing, and calling the LlmIndexer to generate the index for each
directory.
"""

import collections
from collections.abc import Sequence
import concurrent.futures
import datetime

from mono.coresystems.data.excellence.applications.indexing import file_utils
from mono.coresystems.data.excellence.applications.indexing import llm_indexer
from mono.coresystems.data.excellence.applications.indexing import root_map
from mono.coresystems.data.excellence.applications.indexing import state
from mono.coresystems.data.excellence.applications.indexing import work_unit as work_unit_lib
from mono.coresystems.data.excellence.applications.indexing.change_detection import change_detection_strategy as change_detection_strategy_lib
from mono.coresystems.data.excellence.applications.indexing.filesystem import file_system_manager
from mono.coresystems.data.excellence.applications.indexing.filesystem import file_system_manager_base
from mono.coresystems.data.excellence.applications.indexing.indexer import metrics
from mono.coresystems.data.excellence.applications.indexing.indexer import progress_manager as progress_manager_lib
from mono.coresystems.data.excellence.applications.indexing.planner import planner as planner_lib
from mono.coresystems.data.excellence.infra.utils import stat_recorder


DirectoryStats = file_utils.DirectoryStats
WorkUnit = work_unit_lib.WorkUnit

# Maximum number of work units to process in a single epoch. This cutoff is to
# prevent large bundles from taking too long to index. Moreover, we wouldn't
# be able to check them into monorepo anyway.
_MAX_WORK_UNITS_TO_PROCESS = 5000


class Orchestrator:
    """Class to orchestrate the multi-epoch indexing process."""
    
    def __init__(
        self,
        *,
        planner_instance: planner_lib.PlannerBase,
        indexer: llm_indexer.LlmIndexer,
        num_epochs: int,
        root_map_dir: str,
        index_state: state.State,
        work_unit_storage: work_unit_lib.WorkUnitStorage,
        max_workers: int = 16,
        fs_manager: file_system_manager_base.FileSystemManagerBase = file_system_manager.FileSystemManager(),
        bundle_name: str | None = None,
        max_chunk_parallelization: int | None = None,
        input_prefix_to_strip: str | None = None,
        change_detection_strategy: change_detection_strategy_lib.ChangeDetectionStrategy | None = None,
        generate_root_map: bool = True,
        perform_fs_checkpointing: bool = True,
        indexer_type: metrics.IndexerType = metrics.IndexerType.REGULAR,
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
                paths in the work units. This is useful for work unit comparison during
                re-indexing, when input paths may differ but relative paths remain
                consistent.
            change_detection_strategy: An optional change detection strategy to use
                for reindexing. If provided, the orchestrator will use this strategy to
                determine the latest commit identifier for the bundle.
            generate_root_map: Whether to generate the root map after each epoch.
            perform_fs_checkpointing: Whether to perform checkpointing to file system.
            indexer_type: The type of indexer being used (regular or G3).
        """
        self._planner = planner_instance
        self._num_epochs = num_epochs
        self._index_state = index_state
        self._work_unit_storage = work_unit_storage
        self._max_workers = max_workers
        self._fs_manager = fs_manager
        self._bundle_name = bundle_name or "unknown_bundle"
        self._input_prefix_to_strip = input_prefix_to_strip
        self._change_detection_strategy = change_detection_strategy
        self._generate_root_map = generate_root_map
        self._perform_fs_checkpointing = perform_fs_checkpointing
        self._indexer_type = indexer_type
        
        self._root_map_dir = fs_manager.normpath(root_map_dir)

        if self._perform_fs_checkpointing or self._generate_root_map:
            self._fs_manager.make_dirs(self._root_map_dir)

        if self._perform_fs_checkpointing:
            self._progress_manager = progress_manager_lib.ProgressManager(
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
           and moving upwards. This allows parent directories to incorporate
           index information from their children in later epochs.
        3. For each work unit, it calls an LlmIndexer to generate an index file.
           For epochs > 0, the indexer uses the root map from the previous epoch
           as context.
        4. After processing all work units in an epoch, it regenerates the root
           map, which summarizes the indexes generated in that epoch.

        After all epochs are completed, progress files are cleaned up, and
        metadata about the indexed work units and the CL number at which indexing
        was performed is written to the index state.

        Args:
            work_units: A sequence of WorkUnits objects to be processed in this epoch.
            epoch: the current epoc number (0-indexed).

        Returns:
            A dictionary of work unit paths to whether the work unit was processed
            succesfully.
        """
        stat_recorder.get_instance().set_gauge(
            f"{self._bundle_name}.current_epoch", f"{epoch + 1}/{self._num_epochs}"
        )
        stat_recorder.get_instance().reset_counter(
            f"{self._bundle_name}.epoch.dirs.processed"
        )
        stat_recorder.get_instance().reset_counter(
            f"{self._bundle_name}.epoch.work_units.processed"
        )
        
        # Process all work units and take care of progress tracker later.
        work_units_to_process = list(work_units)

        if self._perform_fs_checkpointing:
            progress_file = self._progress_manager.get_progress_file(epoch)
            if self._fs_manager.exists(progress_file):
                print(f"Epoch {epoch}: Progress file exists, loading progress file.")
                epoch_progress = self._progress_manager.read_progress(epoch)
                initial_count = len(work_units_to_process)
                work_units_to_process = [
                    wu 
                    for wu in work_units_to_process
                    if epoch_progress.get(str(wu.output_path)) != "COMPLETED"
                ]
                print(
                    f"Epoch {epoch}: Loaded progress,"
                    f"{initial_count - len(work_units_to_process)}"
                    f" work units already completed."
                )
            else:
                epoch_progress_to_write = {
                    str(wu.output_path): "PENDING" for wu in work_units_to_process
                }
                self._progress_manager.write_progress(epoch, epoch_progress_to_write)

        stat_recorder.get_instance().set_gauge(
            f"{self._bundle_name}.epoch.work_units.total", len(work_units)
        )
        
        if not work_units_to_process:
            print(f"Epoch {epoch}: No work units to index.")
            return {}

        print(f"Epoch {epoch}: Found {len(work_units_to_process)} work units to process.")
        
        # Group work units by path depth to process deepest first.
        work_units_by_depth = collections.defaultdict(list)
        for wu in work_units_to_process:
            depth = len([
                part 
                for part in self._fs_manager.normpath(str(wu.output_path)).split(self._fs_manager.sep())
                if part and part != "."
                ])
            work_units_by_depth[depth].append(wu)
            
        sorted_depths = sorted(work_units_by_depth.keys(), reverse=True)
        results: dict[str, bool] = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            for depth in sorted_depths:
                units_to_process = work_units_by_depth[depth]
                print(f"Epoch {epoch}: Processing {len(units_to_process)} work units of depth {depth}.")
                
                futures: dict[str, concurrent.futures.Future[bool]] = {
                    str(wu.output_path): executor.submit(
                        self._process_work_unit, wu, epoch
                    ) for wu in units_to_process
                }
                
                # Cancel all other futures if any exception is raised.
                # However, we still need to loop to ensure they all complete before exiting.
                exceptions_raised = []
                for work_unit_path, future in futures.items():
                    try:
                        results[work_unit_path] = future.result()
                    except Exception as e:
                        print(f"Error processing {work_unit_path} in epoch {epoch}: {e}")
                        exceptions_raised.append(e)
                        for f in futures.values():
                            f.cancel()
                
                if exceptions_raised:
                    raise exceptions_raised[0]
                    
        return results

    def _process_work_unit(self, work_unit: WorkUnit, epoch: int) -> bool:
        """Processes a single work unit for the given epoch."""
        stat_recorder.get_instance().increment_counter(
            f"{self._bundle_name}.work_units.processed"
        )
        stat_recorder.get_instance().increment_counter(
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
                print(f"Warning: Previous root map not found: {previous_root_map_file}")
        print(f"Generating Index for {work_unit.output_path} epoch {epoch}...")

        bundle_name = self._bundle_name or "unknown_bundle"

        try:  
            work_unit_result = self._indexer.generate_index_for_work_unit(
                work_unit,
                epoch,
                previous_root_map_content,
                self._max_chunk_parallelization,
                self._input_prefix_to_strip,
            )
            
            status = (
                metrics.Status.SUCCESS if work_unit_result.success else metrics.Status.FAILURE
            )
            metrics.WORK_UNITS_PROCESSED.increment(
                self._indexer_type.value, bundle_name, status.value
            )

            if not work_unit_result.success:
                metrics.GENERAL_FAILURE.Increment(
                    self._indexer_type.value, bundle_name, "work_unit_failed", "UNKNOWN"
                )
        except Exception as e:
            metrics.WORK_UNITS_PROCESSED.Increment(
                self._indexer_type.value, bundle_name, metrics.Status.FAILURE.value
            )
            metrics.GENERAL_FAILURES.Increment(
                self._indexer_type.value,
                bundle_name,
                type(e).__name__,
                str(getattr(e, "code", "UNKNOWN")) or "UNKNOWN"
            )
            print(
                f"Error generating index for {work_unit.output_path} epoch"
                f" {epoch}: {e}"
            )
            raise
        
        self._index_state.write_summary(
            str(work_unit.output_path),
            epoch,
            work_unit_result.markdown_results,
        )
        print(f"Successfully wrote index for {work_unit.output_path} epoch {epoch}")

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
        
        print(
            f"Plan generated: {len(work_units_to_process)} units to process,"
            f"  {len(plan.paths_to_delete)} to delete"
        )

        bundle_name = self._bundle_name or "unknown_bundle"
        metrics.WORK_UNITS_TO_PROCESS.Set(
            len(work_units_to_process), self._indexer_type.value, bundle_name
        )

        if plan.paths_to_delete:
            print(f"Deleting {len(plan.paths_to_delete)} index files.")
            for path in plan.paths_to_delete:
                for epoch in range(self._num_epochs):
                    self._index_state.delete_summary(str(path), epoch)

        errored_work_units: list[WorkUnit] = []
        for epoch in range(self._num_epochs):
            print(f"Starting Epoch {epoch}...")
            results = self._run_epoch(work_units_to_process, epoch) 
            errored_work_unit_paths = [
                path for path, success in results.items() if not success
            ]
            errored_work_units.extend(
                wu
                for wu in work_units_to_process
                if str(wu.output_path) in errored_work_unit_paths
            )
            print(f"Finished Epoch {epoch}, writing root map...")
            if self._generate_root_map:
                root_map.regenerate_root_map(
                    all_work_units,
                    self._root_map_dir,
                    self._index_state,
                    epoch,
                    self._fs_manager,
                    self._indexer.llm_prompter
                )
            print(f"Finished root map for epoch {epoch}")

        #delete progress files after all epochs are complete
        if self._perform_fs_checkpointing:
            for epoch in range(self._num_epochs):
                self._progress_manager.delete_progress_file(epoch)
        #only dump the work after all reindexing is done
        commit_identifier = self._change_detection_strategy.get_current_commit_id()

        work_unit_manifest = work_unit_lib.WorkUnitManifest(
            work_units = all_work_units,
            last_indexed_info = work_unit_lib.lastIndexedInfo(
                commit_identifier=commit_identifier,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            ),
            errored_work_units = errored_work_units,
        )
        self._work_unit_storage.write(work_unit_manifest)