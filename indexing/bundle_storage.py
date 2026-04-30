"""Bundle persistence helpers."""

from indexing.schema import IndexBundle


class BundleStorage:
    """Tiny in-memory placeholder for bundle storage."""

    def __init__(self) -> None:
        self._bundles: dict[str, IndexBundle] = {}

    def save(self, bundle: IndexBundle) -> None:
        self._bundles[bundle.bundle_id] = bundle

    def load(self, bundle_id: str) -> IndexBundle | None:
        return self._bundles.get(bundle_id)
