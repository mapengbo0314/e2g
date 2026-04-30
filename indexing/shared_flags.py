"""Shared flags / configuration for the indexing engine.

Organized into logical groups for better discoverability and standardization.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LlmConfig:
    """Configuration for LLM interaction."""
    model: str = "gemini-3-flash-preview"
    max_retries: int = 32
    max_attempts_per_conversation: int = 8
    throttling_strategy: str = "semaphore"  # "semaphore" | "token_bucket"
    max_parallelization: int = 8
    token_limit_per_minute: int = 7_000_000
    use_vertex_ai: bool = True
    vertex_project_id: str | None = "project-tom-meridian"
    google_api_key: str | None = None
    allow_mock_fallback: bool = False  # Set to False for strict production runs


# Configuration schema for the indexing pipeline components.
@dataclass
class PipelineConfig:
    """Configuration for the indexing pipeline execution."""
    bundle_names: list[str] = field(default_factory=list)
    num_epochs: int = 2
    max_workers: int = 8
    max_chunk_parallelization: int = 8
    max_parallel_bundles: int = 4
    dry_run: bool = False
    use_srcfs_file_reading: bool = False


@dataclass
class TrustConfig:
    """Configuration for the trust-oriented verification pipeline."""
    enabled: bool = True
    verification_model: str | None = None  # None = use same as LlmConfig.model
    max_retries: int = 3
    cache_enabled: bool = True


@dataclass
class _GlobalConfig:
    """Mutable global configuration container."""
    llm: LlmConfig = field(default_factory=LlmConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    trust: TrustConfig = field(default_factory=TrustConfig)
    
    # Debug/Audit flags
    review_answer: bool = False
    debug: bool = False
    add_graphviz_tool: bool = False


# Singleton config instance
config = _GlobalConfig()

# ---------------------------------------------------------------------------
# Backward-compatibility layer for legacy codebases
# ---------------------------------------------------------------------------

class LegacyFlags:
    """Maps old flat flag names to the new structured config."""
    
    @property
    def bundle_names(self) -> list[str]: return config.pipeline.bundle_names
    @property
    def num_epochs(self) -> int: return config.pipeline.num_epochs
    @property
    def gemini_model(self) -> str: return config.llm.model
    # Throttling and parallelization settings.
    @property
    def max_llm_retries(self) -> int: return config.llm.max_retries
    @property
    def max_attempts_per_conversation(self) -> int: return config.llm.max_attempts_per_conversation
    @property
    def max_workers(self) -> int: return config.pipeline.max_workers
    # Infrastructure and resource limits.
    @property
    def max_chunk_parallelization(self) -> int: return config.pipeline.max_chunk_parallelization
    @property
    def llm_throttling_strategy(self) -> str: return config.llm.throttling_strategy
    @property
    def max_llm_parallelization(self) -> int: return config.llm.max_parallelization
    # API authentication and platform routing.
    @property
    def llm_token_limit_per_minute(self) -> int: return config.llm.token_limit_per_minute
    @property
    def use_vertex_ai_api(self) -> bool: return config.llm.use_vertex_ai
    @property
    def vertex_ai_project_id(self) -> str | None: return config.llm.vertex_project_id
    # Execution mode flags.
    @property
    def google_api_key(self) -> str | None: return config.llm.google_api_key
    @property
    def dry_run(self) -> bool: return config.pipeline.dry_run
    @property
    def max_parallel_bundles(self) -> int: return config.pipeline.max_parallel_bundles
    # Debugging and UI-specific toggles.
    @property
    def use_srcfs_file_reading(self) -> bool: return config.pipeline.use_srcfs_file_reading
    @property
    def add_graphviz_tool(self) -> bool: return config.add_graphviz_tool
    @property
    def review_answer(self) -> bool: return config.review_answer
    @property
    def debug(self) -> bool: return config.debug

# Instantiate legacy flags for those using 'from indexing.shared_flags import ...'
_legacy = LegacyFlags()
# Global constants mapped from the legacy property class.
BUNDLE_NAMES = _legacy.bundle_names
NUM_EPOCHS = _legacy.num_epochs
GEMINI_MODEL = _legacy.gemini_model
# LLM interaction constants.
MAX_LLM_RETRIES = _legacy.max_llm_retries
MAX_ATTEMPTS_PER_CONVERSATION = _legacy.max_attempts_per_conversation
MAX_WORKERS = _legacy.max_workers
# Concurrency and batching constants.
MAX_CHUNK_PARALLELIZATION = _legacy.max_chunk_parallelization
LLM_THROTTLING_STRATEGY = _legacy.llm_throttling_strategy
MAX_LLM_PARALLELIZATION = _legacy.max_llm_parallelization
# Rate limiting and identity constants.
LLM_TOKEN_LIMIT_PER_MINUTE = _legacy.llm_token_limit_per_minute
USE_VERTEX_AI_API = _legacy.use_vertex_ai_api
VERTEX_AI_PROJECT_ID = _legacy.vertex_ai_project_id
# Pipeline behavior constants.
GOOGLE_API_KEY = _legacy.google_api_key
DRY_RUN = _legacy.dry_run
MAX_PARALLEL_BUNDLES = _legacy.max_parallel_bundles
# Feature-specific flag constants.
USE_SRCFS_FILE_READING = _legacy.use_srcfs_file_reading
ADD_GRAPHVIZ_TOOL = _legacy.add_graphviz_tool
REVIEW_ANSWER = _legacy.review_answer
DEBUG_MODE = _legacy.debug

# Context-preserving executor flag (referenced by context.py)
USE_CONTEXT_PRESERVING_EXECUTOR = True
