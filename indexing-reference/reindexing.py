"""Handles re-indexing logic for the AI Codebase Indexer.

This module provides the IndexDiffer class, which is responsible for
determining which work units need to be re-indexed. It compares the
current state of work units with metadata from the previous indexing run
and checks monorepo for file modifications since the last run to identify
additions, deletions, and modifications.
"""

import collections
from collections.abc import Sequence, Set
import dataclasses

from absl import logging
from mono.coresystems.data.excellence.applications.indexing import work_unit
from mono.coresystems.data.excellence.applications.indexing.change_detection import change_detection_strategy as change_detection_strategy_lib
from mono.coresystems.data.excellence.applications.indexing.filesystem import file_system_manager_base
from mono.pyglib.pathutil import gpath


# The deadline for monorepo API RPCs is in seconds.
_monorepo_RPC_DEADLINE_SECONDS = 60
# The timeout for git commands in seconds.
_GIT_COMMAND_TIMEOUT_SECONDS = 300


@dataclasses.dataclass(frozen=True)
class RawWorkUnitDiff:
    """Holds the difference between two sets of work units.

    This is used internally by IndexDiffer to hold the result of comparing
    two sets of work units; it will later be converted to a DiffForReindexing
    object before being used to update the index.

    Attributes:
      paths_to_reindex: A set of output paths that need to be re-indexed.
      paths_to_delete: A set of output paths that should be deleted from the
        index.
    """

    paths_to_reindex: Set[gpath.GPath]
    paths_to_delete: Set[gpath.GPath]


@dataclasses.dataclass(frozen=True)
class DiffForReindexing:
    """Holds all the necessary information needed to update the index.

    Attributes:
      to_reindex: A sequence of work units that need to be re-indexed.
      to_delete: A sequence of output paths that should be deleted from the index.
    """

    to_reindex: Sequence[work_unit.WorkUnit]
    to_delete: Sequence[gpath.GPath]


class IndexDiffer:
    """Determines which work units need to be re-indexed.

    Compares the work units from the previous index run with the newly
    generated work units and file changes in monorepo to identify which work
    units need to be re-indexed or deleted.
    """

    def __init__(
        self,
        fs_manager: file_system_manager_base.FileSystemManagerBase,
        work_unit_storage: work_unit.WorkUnitStorage,
        change_detection_strategy: (
            change_detection_strategy_lib.ChangeDetectionStrategy
        ),
    ):
        """Initializes the IndexDiffer.

        Args:
          fs_manager: A file system manager to use for file operations.
          work_unit_storage: A work unit storage object for reading manifest files.
          change_detection_strategy: Optional strategy for detecting file changes.
            If provided, this will be used instead of the default monorepo/Git logic.
        """
        self._fs_manager = fs_manager
        self._work_unit_storage = work_unit_storage
        self._change_detection_strategy = change_detection_strategy

    def _load_existing_metadata(self) -> work_unit.WorkUnitManifest:
        """Loads metadata from the previous run.

        Returns:
          A WorkUnitManifest object containing the work units from the previous run,
          or a blank WorkUnitManifest object if no previous run is found.
        """
        # Try to read the work units from the metadata file first.
        old_work_units = self._work_unit_storage.read()
        if old_work_units.work_units:
            return old_work_units

        logging.warning(
            "Metadata file not found, creating a blank metadata object, which will"
            " trigger re-indexing of all paths in the bundle."
        )
        return work_unit.WorkUnitManifest(
            work_units=[],
            last_indexed_info=work_unit.LastIndexedInfo.empty(),
            errored_work_units=[],
        )

    def _diff_work_units(
        self,
        old_work_unit_manifest: work_unit.WorkUnitManifest,
        new_work_units: dict[gpath.GPath, work_unit.WorkUnit],
    ) -> RawWorkUnitDiff:
        """Compares two sets of work units and returns the sets of paths to re-index and delete.

        This function compares the work units from the previous index run
        (old_work_unit_manifest) with the newly generated work units
        (new_work_units)
        to identify changes. It determines which paths need to be re-indexed
        and which paths should be deleted from the index.

        Re-indexing is triggered under several conditions:
          - A new work unit is introduced in new_work_units that was not in
            old_work_unit_manifest.
          - A work unit present in old_work_unit_manifest is no longer in
            new_work_units; in this case, the work unit is marked for deletion, and
            its parent is marked for re-indexing.
          - The list of files to index for a given work unit has changed between
            old_work_unit_manifest and new_work_units.
          - The work unit errored in a previous run, and is still present in
            new_work_units.
          - Any file path in a work unit's files_to_index list has been modified
            since the last indexed CL recorded in old_work_unit_manifest. Note that
            if fetching CL changes fails or if last_indexed_cl is None, all paths
            are re-indexed.
          - If any child path of a given path is marked for re-indexing, the
            parent path is also marked for re-indexing to ensure index consistency.

        Args:
          old_work_unit_manifest: Metadata from the previous index run, including
            old work units and the last indexed CL number.
          new_work_units: A dictionary of newly generated work units, keyed by
            output_path.

        Returns:
          A RawWorkUnitDiff object containing sets of paths to re-index and paths to
          delete.
        """
        old_work_units = {
            wu.output_path: wu for wu in old_work_unit_manifest.work_units
        }
        errored_old_work_units = {
            wu.output_path for wu in old_work_unit_manifest.errored_work_units
        }

        to_reindex = set()
        to_delete = set()
        all_paths = set(old_work_units.keys()) | set(new_work_units.keys())

        for path in all_paths:
            in_old = path in old_work_units
            in_new = path in new_work_units
            in_old_errored = path in errored_old_work_units

            if in_new and not in_old:  # New path, add to reindex.
                to_reindex.add(path)
            elif in_old and not in_new:  # Old path, add to delete and reindex parent.
                to_delete.add(path)
                parent = gpath.GPath(self._fs_manager.dirname(str(path)))
                if parent != path:
                    to_reindex.add(parent)  # Reindex parent if it's not a root.
            elif in_old and in_new:  # Check if contents have changed.
                if (
                    old_work_units[path].files_to_index
                    != new_work_units[path].files_to_index
                ):
                    to_reindex.add(path)
                elif in_old_errored:  # Check if work unit for path errored before.
                    to_reindex.add(path)
                else:
                    if self._change_detection_strategy.work_unit_needs_reindexing(
                        old_work_unit_manifest.last_indexed_info.commit_identifier,
                        new_work_units[path],
                    ):
                        to_reindex.add(path)

        # Propagate changes up the tree.
        sorted_new_paths = sorted(
            list(new_work_units.keys()), key=lambda p: len(str(p)), reverse=True
        )

        # Build a map of parent to children.
        children_map = collections.defaultdict(list)
        for path in new_work_units:
            parent = gpath.GPath(self._fs_manager.dirname(str(path)))
            if parent != path:
                children_map[parent].append(path)

        # For each new path, check if any of its children are marked for re-index.
        # If so, add the new path to the re-index list.
        for path in sorted_new_paths:
            if any(child in to_reindex for child in children_map.get(path, [])):
                to_reindex.add(path)

        return RawWorkUnitDiff(to_reindex, to_delete)

    def get_work_units_to_reindex(
        self,
        work_units: Sequence[work_unit.WorkUnit],
    ) -> DiffForReindexing:
        """Gets the list of work units to reindex and paths to delete.

        This is the main entry point for the diffing logic. It compares the
        provided work units with the state of the last index run and returns
        the set of work units that need to be re-indexed and paths that
        should be deleted.

        Args:
          work_units: The current list of work units generated for this run.

        Returns:
          A DiffForReindexing object containing the work units to re-index and
          paths to delete.

        Raises:
          ValueError: If the specified bundle_name is not found.
        """
        new_work_units = {wu.output_path: wu for wu in work_units}
        old_work_unit_manifest = self._load_existing_metadata()

        changes = self._diff_work_units(old_work_unit_manifest, new_work_units)
        reindex_list = [
            wu for wu in work_units if wu.output_path in changes.paths_to_reindex
        ]
        delete_list = sorted(list(changes.paths_to_delete))
        return DiffForReindexing(reindex_list, delete_list)
