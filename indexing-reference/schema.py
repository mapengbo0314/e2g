"""Core schema objects for indexing workflows.

The previous pass incorrectly attributed `reference-photos/IMG_1655.HEIC` to
this module. That screenshot is now confirmed to be `llm_indexer.py`, so this
file returns to a neutral local reference stub until a real schema screenshot is
identified.
"""

from dataclasses import dataclass, field


REFERENCE_EXCERPT = """\
# No confirmed screenshot-backed excerpt yet for schema.py.
"""


@dataclass(slots=True)
class FileRecord:
    path: str
    content: str = ""


@dataclass(slots=True)
class ChunkRecord:
    name: str
    items: list[FileRecord] = field(default_factory=list)


@dataclass(slots=True)
class IndexBundle:
    bundle_id: str
    summary: str = ""
    chunks: list[ChunkRecord] = field(default_factory=list)
