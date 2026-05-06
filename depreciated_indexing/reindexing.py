"""Handles re-indexing logic for the AI Codebase Indexer.

This module provides the IndexDiffer class, which is responsible for
determining which work units need to be re-indexed. It compares the
current state of work units with metadata from the previous indexing run
and checks for file modifications since the last run to identify
additions, deletions, and modifications.
"""

from __future__ import annotations

import collections
from collections.abc import Sequence, Set
import dataclasses
import logging
from pathlib import Path
from typing import Protocol

from indexing import work_unit

# Define protocols for change detection and filesystem management.


class ChangeDetectionStrategy(Protocol):
    """Protocol for determining whether a work unit needs re-indexing."""

    def work_unit_needs_reindexing(
        self,
        last_commit_identifier: work_unit.CommitIdentifier,
        wu: work_unit.WorkUnit,
    ) -> bool: ...


class FileSystemManager(Protocol):
    """Minimal protocol for filesystem operations needed by the differ."""

    def dirname(self, path: str) -> str: ...


class AlwaysReindexStrategy:
    """Default strategy that marks every work unit for re-indexing."""

    def work_unit_needs_reindexing(
        self,
        last_commit_identifier: work_unit.CommitIdentifier,
        wu: work_unit.WorkUnit,
    ) -> bool:
        return True


class LocalFileSystemManager:
    """Uses pathlib for dirname."""

    def dirname(self, path: str) -> str:
        return str(Path(path).parent)


@dataclasses.dataclass(frozen=True)
class RawWorkUnitDiff:
    """Holds the difference between two sets of work units.

    Attributes:
      paths_to_reindex: A set of output paths that need to be re-indexed.
      paths_to_delete: A set of output paths that should be deleted from the
        index.
    """

    paths_to_reindex: Set[Path]
    paths_to_delete: Set[Path]

# Define higher-level diff objects for the reindexing pipeline.


@dataclasses.dataclass(frozen=True)
class DiffForReindexing:
    """Holds all the necessary information needed to update the index.

    Attributes:
      to_reindex: A sequence of work units that need to be re-indexed.
      to_delete: A sequence of output paths that should be deleted from the index.
    """

    to_reindex: Sequence[work_unit.WorkUnit]
    to_delete: Sequence[Path]


class IndexDiffer:
    """Determines which work units need to be re-indexed.

    Compares the work units from the previous index run with the newly
    generated work units and file changes to identify which work
    units need to be re-indexed or deleted.
    """

    def __init__(
        self,
        fs_manager: FileSystemManager | None = None,
        work_unit_storage: work_unit.WorkUnitStorage | None = None,
        change_detection_strategy: ChangeDetectionStrategy | None = None,
    ):
        """Initializes the IndexDiffer.

        Args:
          fs_manager: A file system manager to use for file operations.
          work_unit_storage: A work unit storage object for reading manifest files.
          change_detection_strategy: Strategy for detecting file changes.
            If not provided, defaults to AlwaysReindexStrategy.
        """
        self._fs_manager = fs_manager or LocalFileSystemManager()
        self._work_unit_storage = work_unit_storage or work_unit.InMemoryWorkUnitStorage()
        self._change_detection_strategy = change_detection_strategy or AlwaysReindexStrategy()

    def _load_existing_metadata(self) -> work_unit.WorkUnitManifest:
        """Loads metadata from the previous run.

        Returns:
          A WorkUnitManifest object containing the work units from the previous run,
          or a blank WorkUnitManifest object if no previous run is found.
        """
        old_work_units = self._work_unit_storage.read()
        if old_work_units.work_units:
            return old_work_units

        # Logging a warning instead of raising an error to allow a full reindex from scratch.
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
        new_work_units: dict[Path, work_unit.WorkUnit],
    ) -> RawWorkUnitDiff:
        """Compares two sets of work units and returns paths to re-index and delete."""
        old_work_units = {
            wu.output_path: wu for wu in old_work_unit_manifest.work_units
        }
        errored_old_work_units = {
            wu.output_path for wu in old_work_unit_manifest.errored_work_units
        }

        to_reindex: set[Path] = set()
        to_delete: set[Path] = set()
        # Union of all paths from previous and current runs to ensure a complete diff.
        all_paths = set(old_work_units.keys()) | set(new_work_units.keys())

        for path in all_paths:
            in_old = path in old_work_units
            in_new = path in new_work_units
            in_old_errored = path in errored_old_work_units

            if in_new and not in_old:
                to_reindex.add(path)
            elif in_old and not in_new:
                to_delete.add(path)
                # If a directory is removed, we must re-index its parent to update the summary.
                # This ensures that the parent's conceptual map remains accurate.
                parent = Path(self._fs_manager.dirname(str(path)))
                if parent != path:
                    to_reindex.add(parent)
            elif in_old and in_new:
                # Compare the set of files within the work unit to detect internal changes.
                if (
                    old_work_units[path].files_to_index
                    != new_work_units[path].files_to_index
                ):
                    to_reindex.add(path)
                elif in_old_errored:
                    # Always re-attempt units that failed in the previous run.
                    to_reindex.add(path)
                # If the previous verification failed, we must re-process the unit.
                # This catches semantic errors that Pydantic might have missed.
                elif old_work_units[path].last_indexed_info and old_work_units[path].last_indexed_info.verification_state == "FAILED":
                    to_reindex.add(path)
                else:
                    # Delegate to the change detection strategy for content-based checks.
                    if self._change_detection_strategy.work_unit_needs_reindexing(
                        old_work_unit_manifest.last_indexed_info.commit_identifier,
                        new_work_units[path],
                    ):
                        to_reindex.add(path)

        # Propagate changes up the tree.
        # We process paths in reverse order of length (deepest first).
        sorted_new_paths = sorted(
            list(new_work_units.keys()), key=lambda p: len(str(p)), reverse=True
        )

        # Construct a map of parents to their direct child work units.
        children_map: dict[Path, list[Path]] = collections.defaultdict(list)
        for path in new_work_units:
            parent = Path(self._fs_manager.dirname(str(path)))
            if parent != path:
                children_map[parent].append(path)

        # If any child is re-indexed, the parent must also be re-indexed to refresh its summary.
        for path in sorted_new_paths:
            # Re-index a directory if any of its children (files or subdirs) are scheduled for update.
            if any(child in to_reindex for child in children_map.get(path, [])):
                to_reindex.add(path)

        return RawWorkUnitDiff(to_reindex, to_delete)

    def get_work_units_to_reindex(
        self,
        work_units: Sequence[work_unit.WorkUnit],
    ) -> DiffForReindexing:
        """Gets the list of work units to reindex and paths to delete.

        This is the main entry point for the diffing logic.

        Args:
          work_units: The current list of work units generated for this run.

        Returns:
          A DiffForReindexing object containing the work units to re-index and
          paths to delete.
        """
        new_work_units = {wu.output_path: wu for wu in work_units}
        old_work_unit_manifest = self._load_existing_metadata()

        changes = self._diff_work_units(old_work_unit_manifest, new_work_units)
        reindex_list = [
            wu for wu in work_units if wu.output_path in changes.paths_to_reindex
        ]
        # Finalize the list of paths to be purged from the index.
        delete_list = sorted(list(changes.paths_to_delete))
        return DiffForReindexing(reindex_list, delete_list)
