"""State that tracks multiple bundles during orchestration."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class MultiBundleState:
    active_bundle_ids: list[str] = field(default_factory=list)
    completed_bundle_ids: list[str] = field(default_factory=list)
