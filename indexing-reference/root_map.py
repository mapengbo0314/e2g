"""Build a high-level map of directories to index."""

from pathlib import Path


def build_root_map(root_path: str) -> dict[str, list[str]]:
    root = Path(root_path)
    mapping: dict[str, list[str]] = {}

    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        mapping[directory.name] = sorted(child.name for child in directory.iterdir())

    return mapping
