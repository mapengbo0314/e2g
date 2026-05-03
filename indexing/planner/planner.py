"""Planner reference for Recursive-Index indexing.

This file is a local, reference-oriented reconstruction of the planner shown in
the provided screenshots. It keeps the same core responsibilities:

- scan the filesystem and collect per-directory statistics
- aggregate small directories into larger work units
- canonicalize paths before diffing
- produce an IndexPlan with all work units, work units to process, and paths to
  delete

It is intentionally lightweight and uses local Python/pathlib substitutes for
the production enterprise-grade dependencies.
"""

# Standard library and third-party imports for filesystem operations and typing.
from __future__ import annotations
import abc
from collections.abc import Sequence
import dataclasses
import logging
from pathlib import Path
from typing import Protocol

# Fallback imports for environment compatibility.
try:
    from indexing.reindexing import DiffForReindexing
except ImportError:
    try:
        from reindexing import DiffForReindexing
    except ImportError:
        DiffForReindexing = None  # type: ignore[assignment]

try:
    from indexing.work_unit import WorkUnit
except ImportError:
    # Final attempt to resolve WorkUnit from the local directory structure.
    from work_unit import WorkUnit


_MAX_INDEX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MiB


@dataclasses.dataclass(slots=True)
class DirectoryStats:
    """Holds statistics for a single directory."""

    path: Path
    files: list[Path]
    size_bytes: int
    file_sizes: dict[Path, int] = dataclasses.field(default_factory=dict)
    has_subdirs: bool = False


@dataclasses.dataclass(frozen=True)
class IndexPlan:
    """A container for the results of the planning phase."""

    all_work_units: Sequence[WorkUnit]
    work_units_to_process: Sequence[WorkUnit]
    paths_to_delete: Sequence[Path]


class IndexDifferProtocol(Protocol):
    """Minimal protocol for plugging in the local reindexing reference."""

    def get_work_units_to_reindex(
        self, work_units: Sequence[WorkUnit]
    ) -> DiffForReindexing: ...


@dataclasses.dataclass(slots=True)
class PathFilteringConfig:
    """Small local stand-in for the production-ready filtering config."""

    exclude_patterns: Sequence[object] = ()
    include_patterns: Sequence[object] = ()
    additional_extensions: Sequence[str] = ()


class PlannerBase(abc.ABC):
    """Defines the contract for planning the indexing process."""

    @abc.abstractmethod
    def plan(self) -> IndexPlan:
        """Generates an indexing plan."""


class Planner(PlannerBase):
    """Implementation of the planning logic for Recursive-Index indexing."""

    def __init__(
        self,
        *,
        fs_manager: object | None = None,
        root_dirs: Sequence[str | Path],
        filtering_config: PathFilteringConfig,
        max_work_unit_size_bytes: int = 500_000,
        index_differ: IndexDifferProtocol | None = None,
        bundle_name: str | None = None,
        input_prefix_to_strip: str | Path | None = None,
        allowed_silos: frozenset[str] | None = None,
    ) -> None:
        """Initializes the planner."""
        self._fs_manager = fs_manager
        self._root_dirs = [Path(root_dir) for root_dir in root_dirs]
        self._filtering_config = filtering_config
        self._max_work_unit_size_bytes = max_work_unit_size_bytes
        self._index_differ = index_differ
        self._bundle_name = bundle_name
        self._input_prefix_to_strip = (
            Path(input_prefix_to_strip) if input_prefix_to_strip else None
        )
        # Filter the silos to ensure only allowed paths are scanned.
        self._allowed_silos = frozenset(str(Path(s)) for s in allowed_silos or [])

    def _canonicalize_path(self, path: Path) -> Path:
        """Strips the input prefix from the path if it exists."""
        # Check if we have a prefix to strip.
        if not self._input_prefix_to_strip:
            return path
        try:
            # Attempt to strip the prefix.
            return path.relative_to(self._input_prefix_to_strip)
        except ValueError:
            # Fall back to the original path if it's not under the prefix.
            return path

    def _canonicalize_work_unit(self, work_unit: WorkUnit) -> WorkUnit:
        """Returns a new WorkUnit with canonicalized paths when supported."""
        if not hasattr(work_unit, "output_path") or not hasattr(
            work_unit, "files_to_index"
        ):
            return work_unit

        # Calculate the total size of files within this work unit aggregation.
        size_bytes = getattr(work_unit, "size_bytes", 0)
        return WorkUnit(
            output_path=self._canonicalize_path(work_unit.output_path),
            files_to_index={
                self._canonicalize_path(path) for path in work_unit.files_to_index
            },
            size_bytes=size_bytes,
        )

    def _is_file_allowed(self, file_path: Path) -> bool:
        """Applies a lightweight extension-based filter for local reference use."""
        if self._allowed_silos and not any(
            str(file_path).startswith(silo) for silo in self._allowed_silos
        ):
            # Explicitly exclude files that fall outside the configured allowed silos.
            return False

        # Check if additional extension filtering is required.
        if self._filtering_config.additional_extensions:
            suffixes = {ext if ext.startswith(".") else f".{ext}" for ext in self._filtering_config.additional_extensions}
            # Verify the file has an allowed extension.
            if file_path.suffix and file_path.suffix not in suffixes:
                return False

        return True

    def _get_indexable_directories(self) -> list[DirectoryStats]:
        """Scans the root directories and returns a list of directories to index."""
        collected_dirs: list[DirectoryStats] = []

        for root_dir in self._root_dirs:
            if not root_dir.exists():
                continue

            dir_stats_map: dict[Path, DirectoryStats] = {}

            for file_path in root_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                if not self._is_file_allowed(file_path):
                    continue

                # Check file size against the maximum limit.
                size = file_path.stat().st_size
                if size > _MAX_INDEX_FILE_SIZE_BYTES:
                    # Exclude large files that would bloat the index context.
                    logging.info(
                        "Planner excluded %s from indexing due to its large size %d > %d",
                        file_path,
                        size,
                        _MAX_INDEX_FILE_SIZE_BYTES,
                    )
                    continue

                # Group files by their parent directory.
                parent_path = file_path.parent
                dir_stats = dir_stats_map.get(parent_path)
                if dir_stats is None:
                    dir_stats = DirectoryStats(
                        path=parent_path,
                        files=[],
                        size_bytes=0,
                    )
                    dir_stats_map[parent_path] = dir_stats

                # Update directory stats with the new file discovery.
                dir_stats.files.append(file_path)
                dir_stats.size_bytes += size
                dir_stats.file_sizes[file_path] = size

            all_dirs = set(dir_stats_map.keys())
            all_dirs.add(root_dir)

            empty_dirs_to_add = set()
            for directory in list(all_dirs):
                curr = directory
                # Climb up the tree to the root to ensure all ancestors are tracked.
                while curr != root_dir and curr.parent != curr:
                    parent = curr.parent
                    if parent not in all_dirs and parent not in empty_dirs_to_add:
                        # Mark ancestor as an indexable empty directory.
                        empty_dirs_to_add.add(parent)
                    curr = parent
            all_dirs.update(empty_dirs_to_add)

            # Ensure all discovered directories have a corresponding stats entry.
            for directory in all_dirs:
                if directory not in dir_stats_map:
                    dir_stats_map[directory] = DirectoryStats(
                        path=directory,
                        files=[],
                        size_bytes=0,
                    )

            for directory in all_dirs:
                if directory != root_dir and directory.parent in dir_stats_map:
                    dir_stats_map[directory.parent].has_subdirs = True

            # Populate the list of indexable directories with statistical metadata.
            collected_dirs.extend(dir_stats_map.values())

        logging.info("Planner found %d directories to index", len(collected_dirs))
        return collected_dirs

    def _aggregate_small_work_units(
        self,
        all_indexable_dirs: Sequence[DirectoryStats],
    ) -> list[WorkUnit]:
        """Aggregates small directories into their parents to form work units."""
        logging.info(
            "Starting aggregation of %d directories", len(all_indexable_dirs)
        )

        uf_parent = {ds.path: ds.path for ds in all_indexable_dirs}
        uf_size = {ds.path: ds.size_bytes for ds in all_indexable_dirs}
        uf_items = {ds.path: [ds] for ds in all_indexable_dirs}

        all_indexable_paths = set(uf_parent.keys())
        root_dirs_set = set(self._root_dirs)
        dir_stats_map = {ds.path: ds for ds in all_indexable_dirs}

        def find(path: Path) -> Path:
            # Find the root of the disjoint set for this path.
            root = path
            while uf_parent[root] != root:
                root = uf_parent[root]

            # Path compression: flatten the structure for faster subsequent lookups.
            curr = path
            while curr != root:
                next_node = uf_parent[curr]
                uf_parent[curr] = root
                curr = next_node
            return root

        # Union-Find aggregation: merge small directories into parents.
        sorted_dirs = sorted(all_indexable_dirs, key=lambda ds: ds.size_bytes)
        for ds in sorted_dirs:
            path = ds.path
            # Root directories are never merged into a "parent".
            if path in root_dirs_set:
                continue
            parent = path.parent
            # Only merge if the parent itself is indexable.
            if parent not in all_indexable_paths:
                continue

            path_root = find(path)
            parent_root = find(parent)
            # Skip if they are already in the same aggregation block.
            if path_root == parent_root:
                continue

            merged_size = uf_size[path_root] + uf_size[parent_root]
            if merged_size > self._max_work_unit_size_bytes:
                continue

            uf_parent[path_root] = parent_root
            uf_size[parent_root] = merged_size
            uf_items[parent_root].extend(uf_items[path_root])
            del uf_items[path_root]

        work_units: list[WorkUnit] = []
        # Traverse directories in depth-order to identify candidates for upward aggregation.
        for path in sorted(dir_stats_map.keys(), key=lambda p: len(p.parts)):
            if path not in uf_items:
                continue

            items = uf_items[path]
            files_to_index: list[Path] = []
            for item in items:
                files_to_index.extend(item.files)

            # Only create a work unit if there are files to index or child summaries to aggregate.
            if files_to_index or dir_stats_map[path].has_subdirs:
                work_units.append(
                    WorkUnit(
                        output_path=path,
                        files_to_index=set(files_to_index),
                        size_bytes=uf_size[path],
                    )
                )

        return work_units

    def plan(self) -> IndexPlan:
        """Generates an indexing plan by scanning the filesystem and diffing state."""
        logging.info("Starting Planner.plan()")
        indexable_dirs = self._get_indexable_directories()
        logging.info(
            "Planner._get_indexable_directories() returned %d dirs",
            len(indexable_dirs),
        )

        unique_dirs = {ds.path: ds for ds in indexable_dirs}
        logging.info("Deduped to %d unique directories", len(unique_dirs))

        sorted_unique_dirs = sorted(
            unique_dirs.values(),
            key=lambda ds: len(ds.path.parts),
            reverse=True,
        )

        logging.info("Starting _aggregate_small_work_units")
        aggregated_work_units = self._aggregate_small_work_units(sorted_unique_dirs)
        logging.info(
            "_aggregate_small_work_units returned %d work units",
            len(aggregated_work_units),
        )

        canonicalized_work_units = [
            self._canonicalize_work_unit(work_unit)
            for work_unit in aggregated_work_units
        ]
        logging.info(
            "Canonicalized %d work units", len(canonicalized_work_units)
        )

        # Decide which work units require actual processing based on the reindexing logic.
        if self._index_differ is None:
            logging.info("No index differ configured")
            diffed_work_units = canonicalized_work_units
            paths_to_delete: list[Path] = []
        else:
            logging.info("Starting index differ")
            work_unit_diff = self._index_differ.get_work_units_to_reindex(
                canonicalized_work_units
            )
            # Log the results of the reindexing diff for system visibility.
            logging.info(
                "Index differ returned %d to reindex and %d to delete",
                len(work_unit_diff.to_reindex),
                len(work_unit_diff.to_delete),
            )
            # Collect the final work units that require indexing passes.
            diffed_work_units = list(work_unit_diff.to_reindex)
            paths_to_delete = list(work_unit_diff.to_delete)

        logging.info("Planner.plan() finished")
        # Construct the final plan container with all calculated units.
        return IndexPlan(
            all_work_units=canonicalized_work_units,
            work_units_to_process=diffed_work_units,
            paths_to_delete=paths_to_delete,
        )
