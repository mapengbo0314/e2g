"""Splits a directory's contents into chunks of a maximum size."""

from typing import Any


class Chunker:
    """Splits a directory's contents into chunks of a maximum size."""

    def chunk(
        self, directory_contents: dict[Any, str], max_size: int
    ) -> list[dict[Any, str]]:
        """Chunks the directory contents by size.

        Args:
          directory_contents: A dictionary of file names to their contents.
          max_size: The maximum size of a chunk in bytes.

        Returns:
          A list of chunks, where each chunk is a dictionary of file names to
          their contents.
        """
        chunks = []
        current_chunk = {}
        current_chunk_size = 0
        # Iterate over a sorted list of files to ensure deterministic chunking.
        for filename, content in sorted(directory_contents.items()):
            # If the current chunk is not empty and adding the next file would exceed
            # the max size, finalize the current chunk and start a new one.
            if current_chunk and (current_chunk_size + len(content)) > max_size:
                chunks.append(current_chunk)
                current_chunk = {}
                current_chunk_size = 0

            current_chunk[filename] = content
            current_chunk_size += len(content)

        # Add the last chunk if it's not empty.
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
