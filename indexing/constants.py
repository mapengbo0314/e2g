"""Shared constants for the indexing engine."""

INDEXING_ROOT = "indexing"
DEFAULT_BUNDLE_NAME = "default"
DEFAULT_CHUNK_SIZE = 12_000

# Trust pipeline constants
MAX_VERIFICATION_RETRIES = 3
VERIFICATION_CACHE_FILE = ".verification_cache.json"

# Publication states
PUBLICATION_STATE_PUBLISHED = "published"
PUBLICATION_STATE_FAILED = "failed"
PUBLICATION_STATE_DEGRADED = "degraded"
PUBLICATION_STATE_PENDING = "pending"

# Verification modes
VERIFICATION_MODE_FULL = "full"
VERIFICATION_MODE_SYNTACTIC_ONLY = "syntactic_only"
VERIFICATION_MODE_SKIP = "skip"

# Severity levels for verification issues
SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"
