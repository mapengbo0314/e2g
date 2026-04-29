"""A unit of work for the indexer, possibly aggregating multiple directories.

This is a local, screenshot-backed reconstruction of the most important parts
of `work_unit.py`. It keeps the core data model and local storage machinery
that other reference modules depend on, while intentionally omitting the
Google-internal Spanner query implementation details.
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
from typing import Any


_METADATA_FILE_NAME = "work_units.json"


CommitIdentifier = Sequence[str] | int


@dataclasses.dataclass(frozen=True)
class LastIndexedInfo:
    """Holds the commit identifier and timestamp for the last indexed commit."""

    commit_identifier: CommitIdentifier
    timestamp: datetime.datetime

    def is_cl_based(self) -> bool:
        return isinstance(self.commit_identifier, int)

    def is_commit_based(self) -> bool:
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


@dataclasses.dataclass(frozen=True)
class WorkUnit:
    """A unit of work for the indexer, possibly aggregating multiple directories."""

    output_path: Path
    files_to_index: Set[Path]
    size_bytes: int = 0
    last_indexed_info: LastIndexedInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "output_path": str(self.output_path),
            "files_to_index": sorted(str(path) for path in self.files_to_index),
            "size_bytes": self.size_bytes,
        }
        if self.last_indexed_info:
            result["last_indexed_info"] = {
                "commit_identifier": self.last_indexed_info.commit_identifier,
                "timestamp": self.last_indexed_info.timestamp.isoformat(),
            }
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
            )
        return cls(
            output_path=Path(data["output_path"]),
            files_to_index={Path(path) for path in data["files_to_index"]},
            size_bytes=data.get("size_bytes", 0),
            last_indexed_info=last_indexed_info,
        )

    def load_files_to_index(
        self,
        prefix: Path | None = None,
    ) -> dict[Path, str]:
        """Loads the files to index from the filesystem."""
        file_contents = {}
        for file_path in self.files_to_index:
            full_path = prefix / file_path if prefix is not None else file_path
            try:
                file_contents[file_path] = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                file_contents[file_path] = "Non-unicode file."
            except OSError:
                file_contents[file_path] = "Could not read file."
        return file_contents


@dataclasses.dataclass(frozen=True)
class WorkUnitManifest:
    """Tracks the state of a Glimpse indexing run."""

    work_units: Collection[WorkUnit]
    last_indexed_info: LastIndexedInfo
    errored_work_units: Collection[WorkUnit]

    def to_dict(self) -> dict[str, Any]:
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
        return self._manifest.last_indexed_info.timestamp


class ReadOnlyWorkUnitStorage(WorkUnitStorage):
    """A WorkUnitStorage that suppresses all writes."""

    def __init__(self, storage: WorkUnitStorage):
        self._storage = storage

    def write(self, manifest: WorkUnitManifest) -> None:
        pass

    def read(self) -> WorkUnitManifest:
        return self._storage.read()

    def get_timestamp(self) -> datetime.datetime:
        return self._storage.get_timestamp()


def _normalize_manifest_for_comparison(
    manifest: WorkUnitManifest,
) -> WorkUnitManifest:
    """Normalizes a manifest for comparison."""
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
        """Returns the timestamp from the work unit manifest's last_indexed_info."""
        return self.read().last_indexed_info.timestamp


class ShadowWorkUnitStorage(WorkUnitStorage):
    """A WorkUnitStorage that shadows reads and writes to two storages.

    Writes are sent to both storages. Reads are done from both, but only the
    result from primary is returned. If the results differ, a warning is logged.
    """

    def __init__(self, primary: WorkUnitStorage, secondary: WorkUnitStorage):
        self._primary = primary
        self._secondary = secondary

    def write(self, manifest: WorkUnitManifest) -> None:
        self._primary.write(manifest)
        try:
            self._secondary.write(manifest)
        except Exception:
            logging.exception("WorkUnitStorage: Failed to write to secondary storage.")

    def read(self) -> WorkUnitManifest:
        primary_manifest = self._primary.read()
        try:
            secondary_manifest = self._secondary.read()
            primary_dict = _normalize_manifest_for_comparison(
                primary_manifest
            ).to_dict()
            secondary_dict = _normalize_manifest_for_comparison(
                secondary_manifest
            ).to_dict()

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
                logging.warning(
                    "WorkUnitStorage: Primary and secondary manifests differ."
                )
                for line in diff:
                    logging.warning(line)
        except Exception:
            logging.exception("WorkUnitStorage: Failed to read from secondary storage.")
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
        except Exception:
            logging.exception("WorkUnitStorage: Failed to read from secondary storage.")
        return primary_timestamp
