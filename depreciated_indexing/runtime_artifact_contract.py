"""Runtime artifact path contract for indexing outputs."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Iterable

from indexing import state


@dataclasses.dataclass(frozen=True)
class RuntimeArtifactContract:
    """Explicit artifact paths for one logical work unit and epoch."""

    output_path: str
    files_to_index: tuple[str, ...]
    epoch: int
    summary_path: str
    artifact_path: str
    root_map_path: str

    @classmethod
    def build(
        cls,
        *,
        state_dir: str | Path,
        output_path: str | Path,
        epoch: int,
        files_to_index: Iterable[str | Path] = (),
        input_prefix_to_strip: str | Path | None = None,
    ) -> "RuntimeArtifactContract":
        """Builds the contract using the current LocalState path conventions."""
        logical_output_path = _logical_output_path(
            output_path, input_prefix_to_strip=input_prefix_to_strip
        )
        state_root = Path(state_dir)
        return cls(
            output_path=logical_output_path,
            files_to_index=tuple(sorted(str(Path(path)) for path in files_to_index)),
            epoch=epoch,
            summary_path=str(
                state_root
                / logical_output_path
                / state.get_index_file_name(epoch, extension="md")
            ),
            artifact_path=str(
                state_root
                / logical_output_path
                / state.get_index_file_name(epoch, extension="json")
            ),
            root_map_path=str(
                state_root / state.get_rootmap_file_name(epoch, extension="md")
            ),
        )


def _logical_output_path(
    output_path: str | Path, *, input_prefix_to_strip: str | Path | None
) -> str:
    path_obj = Path(output_path)
    if input_prefix_to_strip and str(path_obj).startswith(str(input_prefix_to_strip)):
        try:
            path_obj = path_obj.relative_to(input_prefix_to_strip)
        except ValueError:
            pass
    return str(path_obj)
