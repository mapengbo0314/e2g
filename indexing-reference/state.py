"""State container for persistent indexing results."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class IndexState:
    bundles: dict[str, str] = field(default_factory=dict)
    last_updated_at: str = ""
