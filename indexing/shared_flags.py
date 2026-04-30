"""Shared flags / configuration for the indexing engine.

Replaces the upstream absl.flags dependency with a simple module-level
configuration. Values can be overridden at runtime before the pipeline
starts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _Config:
    """Mutable configuration container. Replaces absl flags."""

    bundle_names: list[str] = field(default_factory=list)
    num_epochs: int = 2
    gemini_model: str = "gemini-3-flash-preview"
    max_llm_retries: int = 32
    max_attempts_per_conversation: int = 8
    max_workers: int = 8
    max_chunk_parallelization: int = 8
    llm_throttling_strategy: str = "semaphore"  # "semaphore" | "token_bucket"
    max_llm_parallelization: int = 8
    llm_token_limit_per_minute: int = 7_000_000
    use_vertex_ai_api: bool = True
    vertex_ai_project_id: str | None = "project-tom-meridian"
    google_api_key: str | None = None
    max_parallel_bundles: int = 4
    dry_run: bool = False
    use_srcfs_file_reading: bool = False
    add_graphviz_tool: bool = False
    review_answer: bool = False
    debug: bool = False

    # Trust pipeline additions
    verification_enabled: bool = True
    verification_model: str | None = None  # None = use same as gemini_model
    max_verification_retries: int = 3
    verification_cache_enabled: bool = True


# Singleton config instance — import and mutate directly.
config = _Config()

# ---------------------------------------------------------------------------
# Convenience accessors (backward-compatible with old flag-style .value usage)
# ---------------------------------------------------------------------------

BUNDLE_NAMES = property(lambda self: config.bundle_names)
NUM_EPOCHS = property(lambda self: config.num_epochs)
GEMINI_MODEL = property(lambda self: config.gemini_model)
MAX_LLM_RETRIES = property(lambda self: config.max_llm_retries)
MAX_ATTEMPTS_PER_CONVERSATION = property(lambda self: config.max_attempts_per_conversation)
MAX_WORKERS = property(lambda self: config.max_workers)
MAX_CHUNK_PARALLELIZATION = property(lambda self: config.max_chunk_parallelization)
LLM_THROTTLING_STRATEGY = property(lambda self: config.llm_throttling_strategy)
MAX_LLM_PARALLELIZATION = property(lambda self: config.max_llm_parallelization)
LLM_TOKEN_LIMIT_PER_MINUTE = property(lambda self: config.llm_token_limit_per_minute)
USE_VERTEX_AI_API = property(lambda self: config.use_vertex_ai_api)
VERTEX_AI_PROJECT_ID = property(lambda self: config.vertex_ai_project_id)
GOOGLE_API_KEY = property(lambda self: config.google_api_key)
DRY_RUN = property(lambda self: config.dry_run)
MAX_PARALLEL_BUNDLES = property(lambda self: config.max_parallel_bundles)
USE_SRCFS_FILE_READING = property(lambda self: config.use_srcfs_file_reading)
ADD_GRAPHVIZ_TOOL = property(lambda self: config.add_graphviz_tool)
REVIEW_ANSWER = property(lambda self: config.review_answer)
DEBUG_MODE = property(lambda self: config.debug)

# Context-preserving executor flag (referenced by context.py)
USE_CONTEXT_PRESERVING_EXECUTOR = True
