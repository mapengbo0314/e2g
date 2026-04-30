"""Protocol for interacting with the index state.

Both a protocol and an implementation using the local file system.
This is a local, screenshot-backed reconstruction of the production
`state.py`, adapted to use `pathlib` and simple filesystem helpers.
"""

from __future__ import annotations

from collections.abc import Sequence
import logging
from pathlib import Path
import re
from typing import Protocol


ROOT_MAP_FILE_PATTERN = r"root_map_v(\d+)\.(?:md|json)"
LLM_INDEX_FILE_PATTERN = r"llm_index_v(\d+)\.(?:md|json)"


def get_index_file_name(epoch: int, extension: str = "md") -> str:
    """Returns the index file name for the given epoch."""
    return f"llm_index_v{epoch}.{extension}"


def get_rootmap_file_name(epoch: int, extension: str = "md") -> str:
    """Returns the root map file name for the given epoch."""
    return f"root_map_v{epoch}.{extension}"


def _parse_epoch_from_filename(filename: str) -> int | None:
    """Parses the epoch number from the index file name."""
    match = re.fullmatch(LLM_INDEX_FILE_PATTERN, filename)
    return int(match.group(1)) if match else None


class State(Protocol):
    """Protocol for reading and writing index state."""

    # Metadata Methods
    def get_display_path(self, path: str) -> str:
        """Gets the display path for a given path."""

    # Read Methods
    def get_latest_rootmap(self) -> str:
        """Gets the content of the latest version of the root map."""

    def read_summary(self, path: str, epoch: int) -> str:
        """Reads the content of the index file for the given path and epoch."""

    def read_latest_summary(self, path: str) -> str:
        """Reads the content of the latest index file for the given path."""

    def read_summaries(self, paths: Sequence[str], epoch: int) -> dict[str, str]:
        """Reads the content of the index files for the given paths and epoch."""

    def read_artifact(self, path: str, epoch: int) -> str:
        """Reads the JSON artifact for the given path and epoch."""

    def exist_summary(self, path: str, epoch: int) -> bool:
        """Checks if an index file exists for the given path and epoch."""

    def latest_epoch(self, path: str) -> int | None:
        """Returns the latest epoch for which an index file exists."""

    # Write/Mutating Methods
    def write_summary(self, path: str, epoch: int, content: str) -> None:
        """Writes the index/summary for the given path and epoch to storage."""

    def write_artifact(self, path: str, epoch: int, content: str) -> None:
        """Writes the JSON artifact for the given path and epoch to storage."""

    def write_rootmap(self, epoch: int, content: str) -> None:
        """Writes the root map for the given epoch to storage."""

    def delete_summary(self, path: str, epoch: int) -> None:
        """Deletes an index/summary for the given path and epoch from storage."""

    def delete_rootmap(self, epoch: int) -> None:
        """Deletes the root map for the given epoch from storage."""


class LocalState(State):
    """Implementation of the State protocol using the local file system."""

    def __init__(
        self,
        state_dir: str,
        fs_manager: object | None = None,
        input_prefix_to_strip: str | None = None,
    ):
        """Initializes the LocalState."""
        self._state_dir = Path(state_dir)
        self._fs_manager = fs_manager
        self._input_prefix_to_strip = input_prefix_to_strip

    def __repr__(self) -> str:
        return (
            f"LocalState(state_dir={self._state_dir!r}, "
            f"fs_manager={self._fs_manager!r}, "
            f"input_prefix_to_strip={self._input_prefix_to_strip!r})"
        )

    # Metadata Methods
    def get_display_path(self, path: str) -> str:
        """Gets the display path for a given path."""
        if self._input_prefix_to_strip and path.startswith(self._input_prefix_to_strip):
            try:
                return str(Path(path).relative_to(self._input_prefix_to_strip))
            except ValueError:
                return path
        return path

    # Read Methods
    def get_latest_rootmap(self) -> str:
        """Finds the latest version of the root map file in the directory."""
        version = -1
        latest_file: Path | None = None
        regex = ROOT_MAP_FILE_PATTERN
        if self._state_dir.exists():
            for file_path in self._state_dir.iterdir():
                match = re.fullmatch(regex, file_path.name)
                if not match:
                    continue
                current_version = int(match.group(1))
                if current_version > version:
                    version = current_version
                    latest_file = file_path
        if latest_file:
            return latest_file.read_text(encoding="utf-8")
        raise ValueError(f"No root map file found in {self._state_dir}.")

    def read_summary(self, path: str, epoch: int) -> str:
        """Reads the content of the index file for the given path and epoch."""
        if not self.exist_summary(path, epoch):
            raise FileNotFoundError(
                f"Index file not found for path {path} and epoch {epoch}"
            )
        full_path = self._get_path(path, epoch)
        return full_path.read_text(encoding="utf-8")

    def read_latest_summary(self, path: str) -> str:
        """Reads the content of the latest index file for the given path."""
        epoch = self.latest_epoch(path)
        if epoch is None:
            raise FileNotFoundError(f"No index file found for path {path}")
        return self.read_summary(path, epoch)

    def read_artifact(self, path: str, epoch: int) -> str:
        """Reads the JSON artifact for the given path and epoch."""
        full_path = self._get_path(path, epoch, extension="json")
        if not full_path.exists():
            raise FileNotFoundError(
                f"Artifact file not found for path {path} and epoch {epoch}"
            )
        return full_path.read_text(encoding="utf-8")

    def read_summaries(self, paths: Sequence[str], epoch: int) -> dict[str, str]:
        """Reads the content of the index files for the given paths and epoch."""
        results = {}
        for path in paths:
            if self.exist_summary(path, epoch):
                try:
                    results[path] = self.read_summary(path, epoch)
                except FileNotFoundError:
                    pass
        return results

    def exist_summary(self, path: str, epoch: int) -> bool:
        """Checks if an index file exists for the given path and epoch."""
        path = str(Path(path))
        return self._get_path(path, epoch).exists()

    def latest_epoch(self, path: str) -> int | None:
        """Returns the latest epoch for which an index file exists."""
        path_obj = Path(path)
        if (
            self._input_prefix_to_strip
            and str(path_obj).startswith(self._input_prefix_to_strip)
        ):
            try:
                relative = path_obj.relative_to(self._input_prefix_to_strip)
                dir_path = self._state_dir / relative
            except ValueError:
                dir_path = self._state_dir / path_obj
        else:
            dir_path = self._state_dir / path_obj

        if not dir_path.is_dir():
            return None

        epochs = []
        for filename in (entry.name for entry in dir_path.iterdir()):
            epoch = _parse_epoch_from_filename(filename)
            if epoch is not None:
                epochs.append(epoch)
        return max(epochs) if epochs else None

    # Write/Mutating Methods
    def write_summary(self, path: str, epoch: int, content: str) -> None:
        """Writes the index/summary for the given path and epoch to storage."""
        full_path = self._get_path(path, epoch, extension="md")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def write_artifact(self, path: str, epoch: int, content: str) -> None:
        """Writes the JSON artifact for the given path and epoch to storage."""
        full_path = self._get_path(path, epoch, extension="json")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def write_rootmap(self, epoch: int, content: str) -> None:
        """Writes the root map for the given epoch to storage."""
        full_path = self._get_rootmap_path(epoch, extension="md")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def delete_summary(self, path: str, epoch: int) -> None:
        """Deletes an index/summary for the given path and epoch from storage."""
        full_path = self._get_path(path, epoch)
        if full_path.exists():
            full_path.unlink()

    def delete_rootmap(self, epoch: int) -> None:
        """Deletes the root map for the given epoch from storage."""
        full_path = self._get_rootmap_path(epoch)
        if full_path.exists():
            full_path.unlink()

    # Helper Methods
    def _get_rootmap_path(self, epoch: int, extension: str = "md") -> Path:
        """Gets the full path to the root map file without checking existence."""
        return self._state_dir / get_rootmap_file_name(epoch, extension)

    def _get_path(self, path: str, epoch: int, extension: str = "md") -> Path:
        """Gets the full path to the index file without checking existence."""
        path_obj = Path(path)
        if (
            self._input_prefix_to_strip
            and str(path_obj).startswith(self._input_prefix_to_strip)
        ):
            try:
                path_obj = path_obj.relative_to(self._input_prefix_to_strip)
            except ValueError:
                pass
        return self._state_dir / path_obj / get_index_file_name(epoch, extension)


class ShadowState(State):
    """A State that shadows reads and writes to a primary and secondary state.

    Writes are sent to both states. Reads are done from both, but only the
    result from primary is returned. If the results differ, a warning is logged.
    """

    def __init__(self, primary: State, secondary: State):
        self._primary = primary
        self._secondary = secondary

    def get_display_path(self, path: str) -> str:
        return self._primary.get_display_path(path)

    def get_latest_rootmap(self) -> str:
        primary_result = self._primary.get_latest_rootmap()
        try:
            secondary_result = self._secondary.get_latest_rootmap()
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary latest rootmaps differ."
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def read_summary(self, path: str, epoch: int) -> str:
        primary_result = self._primary.read_summary(path, epoch)
        try:
            secondary_result = self._secondary.read_summary(path, epoch)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary summaries differ for path %s, epoch %d.",
                    path,
                    epoch,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def read_latest_summary(self, path: str) -> str:
        primary_result = self._primary.read_latest_summary(path)
        try:
            secondary_result = self._secondary.read_latest_summary(path)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary latest summaries differ for path %s.",
                    path,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def read_artifact(self, path: str, epoch: int) -> str:
        primary_result = self._primary.read_artifact(path, epoch)
        try:
            secondary_result = self._secondary.read_artifact(path, epoch)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary artifacts differ for path %s, epoch %d.",
                    path,
                    epoch,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read artifact from secondary state.")
        return primary_result

    def read_summaries(self, paths: Sequence[str], epoch: int) -> dict[str, str]:
        primary_result = self._primary.read_summaries(paths, epoch)
        try:
            secondary_result = self._secondary.read_summaries(paths, epoch)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary summaries differ for epoch %d.",
                    epoch,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def exist_summary(self, path: str, epoch: int) -> bool:
        primary_result = self._primary.exist_summary(path, epoch)
        try:
            secondary_result = self._secondary.exist_summary(path, epoch)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary exist_summary differ for path %s, epoch %d.",
                    path,
                    epoch,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def latest_epoch(self, path: str) -> int | None:
        primary_result = self._primary.latest_epoch(path)
        try:
            secondary_result = self._secondary.latest_epoch(path)
            if primary_result != secondary_result:
                logging.warning(
                    "ShadowState: Primary and secondary latest_epoch differ for path %s.",
                    path,
                )
        except Exception:
            logging.exception("ShadowState: Failed to read from secondary state.")
        return primary_result

    def write_summary(self, path: str, epoch: int, content: str) -> None:
        self._primary.write_summary(path, epoch, content)
        try:
            self._secondary.write_summary(path, epoch, content)
        except Exception:
            logging.exception("ShadowState: Failed to write to secondary state.")

    def write_artifact(self, path: str, epoch: int, content: str) -> None:
        self._primary.write_artifact(path, epoch, content)
        try:
            self._secondary.write_artifact(path, epoch, content)
        except Exception:
            logging.exception("ShadowState: Failed to write artifact to secondary state.")

    def write_rootmap(self, epoch: int, content: str) -> None:
        self._primary.write_rootmap(epoch, content)
        try:
            self._secondary.write_rootmap(epoch, content)
        except Exception:
            logging.exception("ShadowState: Failed to write to secondary state.")

    def delete_summary(self, path: str, epoch: int) -> None:
        self._primary.delete_summary(path, epoch)
        try:
            self._secondary.delete_summary(path, epoch)
        except Exception:
            logging.exception("ShadowState: Failed to delete from secondary state.")

    def delete_rootmap(self, epoch: int) -> None:
        self._primary.delete_rootmap(epoch)
        try:
            self._secondary.delete_rootmap(epoch)
        except Exception:
            logging.exception("ShadowState: Failed to delete from secondary state.")
