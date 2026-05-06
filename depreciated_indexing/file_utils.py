"""Filesystem helpers used by indexing modules."""

from pathlib import Path


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def list_relative_files(root: str) -> list[str]:
    base = Path(root)
    return sorted(str(path.relative_to(base)) for path in base.rglob("*") if path.is_file())
