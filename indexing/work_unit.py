"""A unit of work for the indexer, possibly aggregating multiple directories.

This is a screenshot-backed reconstruction of the upstream `work_unit.py`.
It preserves the main data model plus the storage abstractions that appear in
the provided screenshots: in-memory, filesystem, shadow/dual-write, and a
reference-grade Spanner-backed shape.
"""

from __future__ import annotations

import abc
from collections.abc import Collection, Iterable, Sequence, Set
import dataclasses
import datetime
import difflib
import json
import logging
from pathlib import Path
from typing import Any, Protocol


_METADATA_FILE_NAME = "work_units.json"

class MetricObserver(Protocol):
    """Protocol for tracking metrics, implemented by the orchestrator's Observer."""
    def increment_counter(self, name: str, value: int = 1) -> None: ...


# Default observer that does nothing, used if no observer is provided.
class _NoOpObserver:
    def increment_counter(self, name: str, value: int = 1) -> None:
        pass


_default_observer = _NoOpObserver()


class _FakeMutation:
    """Small local stand-in for a Spanner mutation object."""

    def __init__(self) -> None:
        self.ops: list[dict[str, Any]] = []

    def InsertOrUpdate(
        self,
        *,
        table: str,
        cols: Sequence[str],
        vals: Sequence[Any],
    ) -> None:
        # Map the operation to a dictionary format for local tracking.
        self.ops.append(
            {
                "op": "InsertOrUpdate",
                "table": table,
                "cols": list(cols),
                "vals": list(vals),
            }
        )

    def Apply(self) -> None:
        return None


class _FakeCommitShas:
    def __init__(self) -> None:
        self.commit_sha: list[str] = []

    def extend(self, values: Sequence[str]) -> None:
        self.commit_sha.extend(values)


class _FakeCommitIdProto:
    """Local stand-in for the upstream summaries_pb2.CommitId proto."""

    def __init__(self) -> None:
        self.cl: int | None = None
        self.commit_shas = _FakeCommitShas()

    def HasField(self, name: str) -> bool:
        if name == "cl":
            return self.cl is not None
        if name == "commit_shas":
            return bool(self.commit_shas.commit_sha)
        return False

    def SerializeToString(self) -> bytes:
        # Construct a simple dictionary representing the proto payload.
        payload = {}
        if self.cl is not None:
            payload["cl"] = self.cl
        # Include commit SHAs if present.
        if self.commit_shas.commit_sha:
            payload["commit_shas"] = list(self.commit_shas.commit_sha)
        # Serialize to a canonical JSON string for stable comparisons.
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    @classmethod
    def FromString(cls, raw: bytes) -> "_FakeCommitIdProto":
        proto = cls()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return proto
        if "cl" in payload:
            proto.cl = payload["cl"]
        if "commit_shas" in payload:
            proto.commit_shas.extend(payload["commit_shas"])
        # Return the populated proto-like object.
        return proto


class _BaseQuery:
    """Reference query object used to preserve upstream structure locally."""

    SQL = ""

    def __init__(self, *params: Any) -> None:
        self.params = params

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.params!r})"


CommitIdentifier = Sequence[str] | int


@dataclasses.dataclass(frozen=True)
class LastIndexedInfo:
    """Holds the commit identifier and timestamp for the last indexed commit."""

    commit_identifier: CommitIdentifier
    timestamp: datetime.datetime
    verification_state: str = "UNKNOWN"

    def is_cl_based(self) -> bool:
        return isinstance(self.commit_identifier, int)

    def is_commit_based(self) -> bool:
        # Check if the identifier is a collection of SHAs rather than a CL.
        return not isinstance(self.commit_identifier, int)

    @classmethod
    def empty(cls) -> LastIndexedInfo:
        return cls(
            commit_identifier=[],
            timestamp=datetime.datetime.min.replace(
                tzinfo=datetime.timezone.utc
            ),
        )

    def is_empty(self) -> bool:
        return self == self.empty()


@dataclasses.dataclass
class WorkUnit:
    """A unit of work for the indexer, possibly aggregating multiple directories."""

    output_path: Path
    files_to_index: Set[Path]
    size_bytes: int = 0
    last_indexed_info: LastIndexedInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializes the work unit to a JSON-compatible dictionary."""
        # 1. Capture basic path and file membership info.
        result = {
            "output_path": str(self.output_path),
            "files_to_index": sorted(str(path) for path in self.files_to_index),
            "size_bytes": self.size_bytes,
        }
        # 2. Append the last_indexed_info if it exists (for incremental indexing).
        if self.last_indexed_info:
            result["last_indexed_info"] = {
                "commit_identifier": self.last_indexed_info.commit_identifier,
                "timestamp": self.last_indexed_info.timestamp.isoformat(),
                "verification_state": self.last_indexed_info.verification_state,
            }
        # 3. Finalize and return the serialized work unit representation.
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkUnit:
        last_indexed_info = None
        if "last_indexed_info" in data:
            last_indexed_info = LastIndexedInfo(
                commit_identifier=data["last_indexed_info"]["commit_identifier"],
                timestamp=datetime.datetime.fromisoformat(
                    data["last_indexed_info"]["timestamp"]
                ),
                verification_state=data["last_indexed_info"].get("verification_state", "UNKNOWN"),
            )
        return cls(
            output_path=Path(data["output_path"]),
            files_to_index={Path(path) for path in data["files_to_index"]},
            size_bytes=data.get("size_bytes", 0),
            last_indexed_info=last_indexed_info,
        )

    def load_files_to_index(
        self,
        fs_manager: object | None = None,
        prefix: Path | None = None,
    ) -> dict[Path, str]:
        """Loads the files to index from the filesystem."""
        file_contents = {}
        unreadable_count = 0
        for file_path in self.files_to_index:
            fp = Path(file_path)
            if prefix is not None and not fp.is_absolute():
                # Avoid path doubling: if the file path already starts with
                # the prefix (e.g. "indexing/schema.py" with prefix "indexing/"),
                # don't prepend it again.
                try:
                    fp.relative_to(prefix)
                    # file_path already includes the prefix — use it as-is.
                    full_path = fp
                except ValueError:
                    # file_path is relative to the prefix — prepend it.
                    full_path = prefix / fp
            else:
                full_path = fp
            try:
                if fs_manager is not None and hasattr(fs_manager, "read"):
                    file_contents[file_path] = fs_manager.read(str(full_path))
                else:
                    file_contents[file_path] = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Handle non-text files gracefully by providing a placeholder.
                logging.debug("Non-unicode file skipped: %s", full_path)
                file_contents[file_path] = "Non-unicode file."
                unreadable_count += 1
            except OSError as e:
                # Catch permission or missing file errors at runtime.
                logging.debug("OS error reading %s: %s", full_path, e)
                file_contents[file_path] = "Could not read file."
                unreadable_count += 1
            except Exception:
                # Log unexpected errors but don't crash the entire work unit.
                logging.exception("Failed reading file for work unit: %s", full_path)
                file_contents[file_path] = "Could not read file."
                unreadable_count += 1

        total = len(file_contents)
        if unreadable_count > 0:
            logging.warning(
                "WorkUnit %s: %d/%d files unreadable (binary or missing). "
                "Source context will be degraded.",
                self.output_path, unreadable_count, total,
            )
        else:
            logging.debug(
                "WorkUnit %s: loaded %d files successfully.",
                self.output_path, total,
            )
        return file_contents


@dataclasses.dataclass(frozen=True)
class WorkUnitManifest:
    """Tracks the state of a Recursive-Index indexing run."""

    work_units: Collection[WorkUnit]
    last_indexed_info: LastIndexedInfo
    errored_work_units: Collection[WorkUnit]

    def to_dict(self) -> dict[str, Any]:
        # Serialize the manifest to a dictionary for JSON persistence.
        return {
            "work_units": [
                wu.to_dict()
                for wu in sorted(self.work_units, key=lambda wu: str(wu.output_path))
            ],
            "last_indexed_info": {
                "commit_identifier": self.last_indexed_info.commit_identifier,
                "timestamp": self.last_indexed_info.timestamp.isoformat(),
            },
            "errored_work_units": [
                wu.to_dict()
                for wu in sorted(
                    self.errored_work_units, key=lambda wu: str(wu.output_path)
                )
            ],
            # Add a final grouping comment for the manifest dictionary structure.
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkUnitManifest:
        if "last_indexed_info" not in data:
            # Migration from having last_indexed_cl as a separate field.
            cl = data.get("last_indexed_cl", 0)
            data["last_indexed_info"] = {
                "commit_identifier": cl,
                "timestamp": datetime.datetime.min.replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat(),
            }
            data.pop("last_indexed_cl", None)

        return cls(
            work_units=[WorkUnit.from_dict(wu) for wu in data["work_units"]],
            last_indexed_info=LastIndexedInfo(
                commit_identifier=data["last_indexed_info"]["commit_identifier"],
                timestamp=datetime.datetime.fromisoformat(
                    data["last_indexed_info"]["timestamp"]
                ),
            ),
            errored_work_units=[
                WorkUnit.from_dict(wu) for wu in data["errored_work_units"]
            ],
        )


class WorkUnitStorage(abc.ABC):
    """Manages persistent storage of WorkUnitManifests."""

    @abc.abstractmethod
    def write(self, manifest: WorkUnitManifest) -> None:
        """Writes the list of work units to storage."""

    @abc.abstractmethod
    def read(self) -> WorkUnitManifest:
        """Reads the list of work units from storage."""

    @abc.abstractmethod
    def get_timestamp(self) -> datetime.datetime:
        """Returns the timestamp from the work unit manifest's last_indexed_info."""


class InMemoryWorkUnitStorage(WorkUnitStorage):
    """Stores WorkUnitManifests in memory."""

    def __init__(self):
        self._manifest = WorkUnitManifest(
            work_units=[],
            last_indexed_info=LastIndexedInfo.empty(),
            errored_work_units=[],
        )

    def write(self, manifest: WorkUnitManifest) -> None:
        self._manifest = dataclasses.replace(
            manifest,
            work_units=sorted(manifest.work_units, key=lambda wu: str(wu.output_path)),
            errored_work_units=sorted(
                manifest.errored_work_units, key=lambda wu: str(wu.output_path)
            ),
        )

    def read(self) -> WorkUnitManifest:
        return self._manifest

    def get_timestamp(self) -> datetime.datetime:
        # Extract the global timestamp from the manifest's tracking info.
        return self._manifest.last_indexed_info.timestamp


class ReadOnlyWorkUnitStorage(WorkUnitStorage):
    """A WorkUnitStorage that suppresses all writes."""

    def __init__(self, storage: WorkUnitStorage):
        self._storage = storage

    def write(self, manifest: WorkUnitManifest) -> None:
        return None

    def read(self) -> WorkUnitManifest:
        return self._storage.read()

    def get_timestamp(self) -> datetime.datetime:
        # Delegate timestamp retrieval to the underlying storage implementation.
        return self._storage.get_timestamp()


def _normalize_manifest_for_comparison(
    manifest: WorkUnitManifest,
) -> WorkUnitManifest:
    """Normalizes a manifest for comparison.

    This ensures that work units have their last_indexed_info populated using
    the manifest-level value when a backend stores inherited values implicitly.
    """
    new_work_units = [
        dataclasses.replace(
            wu,
            last_indexed_info=wu.last_indexed_info or manifest.last_indexed_info,
        )
        for wu in manifest.work_units
    ]
    new_errored_work_units = [
        dataclasses.replace(
            wu,
            last_indexed_info=wu.last_indexed_info or manifest.last_indexed_info,
        )
        for wu in manifest.errored_work_units
    ]
    return dataclasses.replace(
        manifest,
        work_units=new_work_units,
        errored_work_units=new_errored_work_units,
    )


def _to_comparable_dict(manifest: WorkUnitManifest) -> dict[str, Any]:
    """Builds a comparison-friendly dict.

    The screenshots show the size-bytes field being removed before diffing in
    some storage comparisons because not every backend stores it consistently.
    """
    manifest_dict = _normalize_manifest_for_comparison(manifest).to_dict()
    for wu in manifest_dict["work_units"]:
        wu.pop("size_bytes", None)
    for wu in manifest_dict["errored_work_units"]:
        wu.pop("size_bytes", None)
    return manifest_dict


class FsWorkUnitStorage(WorkUnitStorage):
    """Manages persistent storage of WorkUnitManifests in the filesystem."""

    def __init__(self, state_dir: str):
        self._state_dir = Path(state_dir)
        self._metadata_path = self._state_dir / _METADATA_FILE_NAME

    def write(self, manifest: WorkUnitManifest) -> None:
        """Dumps the list of work units to a metadata file."""
        manifest_dict = manifest.to_dict()
        encoded_str = json.dumps(manifest_dict, indent=2)
        self._metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self._metadata_path.write_text(encoded_str, encoding="utf-8")

    def read(self) -> WorkUnitManifest:
        """Reads the list of work units from a metadata file."""
        try:
            encoded_str = self._metadata_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return WorkUnitManifest(
                work_units=[],
                last_indexed_info=LastIndexedInfo.empty(),
                errored_work_units=[],
            )

        manifest_dict = json.loads(encoded_str)
        return WorkUnitManifest.from_dict(manifest_dict)

    def get_timestamp(self) -> datetime.datetime:
        # Perform a fresh read to ensure the latest manifest timestamp is returned.
        return self.read().last_indexed_info.timestamp


class ShadowWorkUnitStorage(WorkUnitStorage):
    """A WorkUnitStorage that shadows reads and writes to two storages.

    Writes are sent to both storages. Reads are done from both, but only the
    result from primary is returned. If the results differ, a warning is logged.
    """

    def __init__(
        self, 
        primary: WorkUnitStorage, 
        secondary: WorkUnitStorage,
        observer: MetricObserver | None = None
    ):
        self._primary = primary
        self._secondary = secondary
        self._observer = observer or _default_observer

    def read(self) -> WorkUnitManifest:
        primary_manifest = self._primary.read()
        try:
            # Read from secondary and perform a structural comparison for auditing.
            secondary_manifest = self._secondary.read()
            primary_dict = _to_comparable_dict(primary_manifest)
            secondary_dict = _to_comparable_dict(secondary_manifest)

            # Log differences if the two storage layers have drifted.
            if primary_dict != secondary_dict:
                primary_json = json.dumps(primary_dict, indent=2).splitlines()
                secondary_json = json.dumps(secondary_dict, indent=2).splitlines()
                diff = difflib.unified_diff(
                    primary_json,
                    secondary_json,
                    fromfile="primary",
                    tofile="secondary",
                    lineterm="",
                )
                # Delineate the comparison results for troubleshooting storage parity.
                logging.warning(
                    "WorkUnitStorage: Primary and secondary manifests differ."
                )
                for line in diff:
                    logging.warning(line)
                self._observer.increment_counter("indexing.read_diffs")
        except Exception:
            logging.exception("WorkUnitStorage: Failed to read from secondary storage.")
            self._observer.increment_counter("indexing.secondary_read_failures")
        return primary_manifest

    def get_timestamp(self) -> datetime.datetime:
        """Returns the timestamp from the work unit manifest's last_indexed_info."""
        primary_timestamp = self._primary.get_timestamp()
        try:
            secondary_timestamp = self._secondary.get_timestamp()
            if primary_timestamp != secondary_timestamp:
                logging.warning(
                    "WorkUnitStorage: Primary and secondary timestamps differ. Primary: %s Secondary: %s.",
                    primary_timestamp,
                    secondary_timestamp,
                )
                self._observer.increment_counter("indexing.read_diffs")
        except Exception:
            logging.exception("WorkUnitStorage: Failed to read from secondary storage.")
            self._observer.increment_counter("indexing.secondary_read_failures")
        return primary_timestamp

    def write(self, manifest: WorkUnitManifest) -> None:
        self._primary.write(manifest)
        try:
            self._secondary.write(manifest)
        except Exception:
            logging.exception("WorkUnitStorage: Failed to write to secondary storage.")
            # Track failed shadow writes for auditing and reliability monitoring.
            self._observer.increment_counter("indexing.secondary_write_failures")


@dataclasses.dataclass(frozen=True)
class WorkUnitRow:
    """Represents a row from the WorkUnits table."""

    output_path: str
    success: bool
    files_to_index: list[str]
    serialized_commit_id: bytes | None = None
    last_indexed_commit_timestamp: datetime.datetime | None = None


def _update_last_commit_info(
    current_info: LastIndexedInfo,
    commit_id_proto: Any,
    row_timestamp: datetime.datetime | None,
) -> LastIndexedInfo:
    """Updates the last indexed commit info based on the most recent timestamp."""
    if row_timestamp is None:
        return current_info

    if current_info.is_empty() or row_timestamp > current_info.timestamp:
        if hasattr(commit_id_proto, "HasField") and commit_id_proto.HasField("cl"):
            # Return CL-based metadata for monorepo-style tracking.
            return LastIndexedInfo(
                commit_identifier=commit_id_proto.cl,
                timestamp=row_timestamp,
            )
        if hasattr(commit_id_proto, "HasField") and commit_id_proto.HasField(
            "commit_shas"
        ):
            return LastIndexedInfo(
                commit_identifier=list(commit_id_proto.commit_shas.commit_sha),
                timestamp=row_timestamp,
            )
    return current_info


def _create_last_indexed_info_from_row(row: WorkUnitRow) -> LastIndexedInfo:
    """Creates a LastIndexedInfo object from a Spanner-style row."""
    if row.serialized_commit_id is None:
        return LastIndexedInfo.empty()
    commit_id_proto = _FakeCommitIdProto.FromString(row.serialized_commit_id)
    if commit_id_proto.HasField("cl"):
        return LastIndexedInfo(
            commit_identifier=commit_id_proto.cl or 0,
            timestamp=(
                row.last_indexed_commit_timestamp
                or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            ),
        )
    if commit_id_proto.HasField("commit_shas"):
        return LastIndexedInfo(
            commit_identifier=list(commit_id_proto.commit_shas.commit_sha),
            timestamp=(
                row.last_indexed_commit_timestamp
                or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            ),
        )
    return LastIndexedInfo.empty()


def _build_manifest_from_rows(rows: Iterable[WorkUnitRow]) -> WorkUnitManifest:
    """Processes raw rows into a WorkUnitManifest."""
    work_units = []
    errored_work_units = []
    last_commit_info = LastIndexedInfo.empty()

    for row in rows:
        row_last_indexed_info = _create_last_indexed_info_from_row(row)
        work_unit = WorkUnit(
            output_path=Path(row.output_path),
            files_to_index={Path(path) for path in row.files_to_index},
            last_indexed_info=row_last_indexed_info,
        )
        last_commit_info = max(
            [last_commit_info, row_last_indexed_info],
            key=lambda info: info.timestamp,
        )
        if row.success:
            work_units.append(work_unit)
        else:
            errored_work_units.append(work_unit)

    work_units.sort(key=lambda wu: wu.output_path)
    errored_work_units.sort(key=lambda wu: wu.output_path)
    return WorkUnitManifest(
        work_units=work_units,
        last_indexed_info=last_commit_info,
        errored_work_units=errored_work_units,
    )


class SpannerWorkUnitStorage(WorkUnitStorage):
    """Reference-grade shape for persistent storage in Spanner."""

    def __init__(
        self,
        db: object,
        bundle_name: str,
        read_paths: Sequence[str] | None = None,
    ):
        self._db = db
        self._bundle_name = bundle_name
        self._read_paths = read_paths

    @classmethod
    def from_db_path(
        cls,
        db_path: str,
        bundle_name: str,
        read_paths: Sequence[str] | None = None,
    ) -> "SpannerWorkUnitStorage":
        """Initializes a SpannerWorkUnitStorage from a given database path."""
        return cls(db=db_path, bundle_name=bundle_name, read_paths=read_paths)

    def _add_row_to_mutation(
        self,
        mutation: _FakeMutation,
        path: str,
        success: bool,
        commit_id_proto: _FakeCommitIdProto,
        last_indexed_commit_timestamp: datetime.datetime,
        files_to_index: list[str],
    ) -> None:
        """Adds a single work-unit row to a mutation."""
        # Map work unit attributes to Spanner table columns for persistence.
        mutation.InsertOrUpdate(
            table="WorkUnits",
            cols=[
                "BundleName",
                "Path",
                "Success",
                "LastIndexedCommitId",
                "FilesToIndex",
                "LastIndexedCommitTimestamp",
                "Status",
            ],
            vals=[
                self._bundle_name,
                path,
                success,
                commit_id_proto.SerializeToString(),
                files_to_index,
                last_indexed_commit_timestamp,
                "ACTIVE",
            ],
        )

    def write(self, manifest: WorkUnitManifest) -> None:
        """Writes the list of work units to Spanner.

        The real implementation batches mutations for active/errored work units,
        then prunes stale rows using one of the delete queries below.
        """
        work_units_to_write = sorted(
            manifest.work_units, key=lambda wu: str(wu.output_path)
        )
        errored_work_units_to_write = sorted(
            manifest.errored_work_units, key=lambda wu: str(wu.output_path)
        )

        # Batch mutations for all work units in the manifest.
        mutation = _FakeMutation()
        updated_paths: list[str] = []

        # Iterate through successful work units and prepare Spanner mutations.
        for wu in work_units_to_write:
            updated_paths.append(str(wu.output_path))
            info = wu.last_indexed_info or manifest.last_indexed_info
            commit_id_proto = _FakeCommitIdProto()
            if info.is_cl_based():
                commit_id_proto.cl = int(info.commit_identifier)
            elif info.is_commit_based():
                # For non-monorepo sources, extend the proto with commit SHAs.
                commit_id_proto.commit_shas.extend(
                    list(info.commit_identifier)  # type: ignore[arg-type]
                )
            self._add_row_to_mutation(
                mutation,
                str(wu.output_path),
                True,
                commit_id_proto,
                info.timestamp,
                sorted(str(f) for f in wu.files_to_index),
            )

        for wu in errored_work_units_to_write:
            updated_paths.append(str(wu.output_path))
            info = wu.last_indexed_info or manifest.last_indexed_info
            commit_id_proto = _FakeCommitIdProto()
            if info.is_cl_based():
                commit_id_proto.cl = int(info.commit_identifier)
            elif info.is_commit_based():
                # Record the failed unit's commit SHAs for tracking and retry logic.
                commit_id_proto.commit_shas.extend(
                    list(info.commit_identifier)  # type: ignore[arg-type]
                )
            self._add_row_to_mutation(
                mutation,
                str(wu.output_path),
                False,
                commit_id_proto,
                info.timestamp,
                sorted(str(f) for f in wu.files_to_index),
            )

        mutation.Apply()
        # Clean up any rows that are no longer present in the manifest.
        self._delete_stale_rows(updated_paths)

    def read(self) -> WorkUnitManifest:
        """Reads the list of work units from Spanner."""
        return _build_manifest_from_rows(self._fetch_rows())

    def _delete_stale_rows(self, updated_paths: Sequence[str]) -> None:
        """Reference placeholder for stale-row cleanup."""
        if self._read_paths is not None:
            query = _DeleteOldWorkUnitsScopedQuery(self._bundle_name, updated_paths, self._read_paths)
        else:
            query = _DeleteOldWorkUnitsQuery(self._bundle_name, updated_paths)
        logging.info("SpannerWorkUnitStorage cleanup query: %r", query)

    def _fetch_rows(self) -> Iterable[WorkUnitRow]:
        """Fetches WorkUnit rows.

        The real implementation issues one of several Spanner queries depending
        on whether `read_paths` is set. We return an empty iterable locally.
        """
        if self._read_paths is not None:
            query = _ReadWorkUnitsByPathQuery(self._bundle_name, self._read_paths, "ACTIVE")
        else:
            query = _ReadWorkUnitsQuery(self._bundle_name, "ACTIVE")
        logging.info("SpannerWorkUnitStorage read query: %r", query)
        return []

    def get_timestamp(self) -> datetime.datetime:
        """Returns the timestamp from the work unit manifest's last_indexed_info."""
        query = _ReadLatestTimestampQuery(self._bundle_name, "ACTIVE")
        logging.info("SpannerWorkUnitStorage timestamp query: %r", query)
        manifest = self.read()
        # Extract the last indexed timestamp from the manifest structure.
        return manifest.last_indexed_info.timestamp


class _ReadWorkUnitsQuery(_BaseQuery):
    SQL = """
SELECT
  w.Path,
  w.Success,
  w.FilesToIndex,
  w.LastIndexedCommitId,
  w.LastIndexedCommitTimestamp
FROM WorkUnits AS w
WHERE w.BundleName = @p0 AND w.Status = @p1
""".strip()


class _ReadLatestTimestampQuery(_BaseQuery):
    SQL = """
SELECT
  MAX(w.LastIndexedCommitTimestamp)
FROM WorkUnits AS w
WHERE w.BundleName = @p0 AND w.Status = @p1
""".strip()


class _ReadWorkUnitsByPathQuery(_BaseQuery):
    SQL = """
SELECT
  w.Path,
  w.Success,
  w.FilesToIndex,
  w.LastIndexedCommitId,
  w.LastIndexedCommitTimestamp
FROM WorkUnits AS w
WHERE w.BundleName = @p0 AND w.Status = @p2
  AND EXISTS(SELECT 1 FROM UNNEST(@p1) AS prefix
             WHERE STARTS_WITH(w.Path, prefix))
""".strip()


class _DeleteOldWorkUnitsQuery(_BaseQuery):
    SQL = """
DELETE FROM WorkUnits
WHERE WorkUnits.BundleName = @p0
  AND WorkUnits.Path NOT IN UNNEST(@p1)
""".strip()


class _DeleteOldWorkUnitsScopedQuery(_BaseQuery):
    SQL = """
DELETE FROM WorkUnits
WHERE WorkUnits.BundleName = @p0
  AND WorkUnits.Path NOT IN UNNEST(@p1)
  AND EXISTS(SELECT 1 FROM UNNEST(@p2) AS prefix
             WHERE STARTS_WITH(WorkUnits.Path, prefix))
""".strip()


def create_shadow_storage(
    primary: WorkUnitStorage,
    secondary: WorkUnitStorage | None = None,
) -> WorkUnitStorage:
    """Creates the most appropriate storage wrapper for a local MVP run."""
    if secondary is None:
        return primary
    return ShadowWorkUnitStorage(primary=primary, secondary=secondary)
