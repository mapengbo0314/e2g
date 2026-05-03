"""Real filesystem manager for the indexing engine."""

import os
import pathlib

class RealFsManager:
    """A simple local filesystem manager."""

    def normpath(self, path: str) -> str:
        # Standardize path string format for the local OS.
        return os.path.normpath(path)

    def sep(self) -> str:
        # Return the OS-specific path separator.
        return os.sep

    def make_dirs(self, path: str) -> None:
        # Recursively create directories if they don't exist.
        os.makedirs(path, exist_ok=True)

    def exists(self, path: str) -> bool:
        # Check if a file or directory exists at the given path.
        return os.path.exists(path)

    def read(self, path: str) -> str:
        # Read the entire content of a file into a string.
        return pathlib.Path(path).read_text(encoding="utf-8")

    def write(self, path: str, content: str) -> None:
        # Ensure parent directories exist then write the file content.
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_text(content, encoding="utf-8")

    def join(self, *parts: str) -> str:
        # Concatenate path parts using the OS-specific separator.
        return os.path.join(*parts)

    def delete(self, path: str) -> None:
        # Remove a file from the filesystem, ignoring errors if not found.
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
