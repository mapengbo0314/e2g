"""Shared flags for the AI Codebase Indexer.

This reference file is reconstructed from `reference-photos/IMG_1665.HEIC`,
which clearly shows the top of `shared_flags.py` through the early flag block.
Defaults and help text below follow the visible screenshot as closely as
possible.
"""

from absl import flags


BUNDLE_NAMES = flags.DEFINE_list(
    "bundle_names",
    default=[],
    help="The names of the bundles to use. If empty, all bundles will be used.",
)

NUM_EPOCHS = flags.DEFINE_integer(
    "num_epochs",
    default=2,
    help="The number of refinement epochs to run.",
)

GEMINI_MODEL = flags.DEFINE_string(
    "gemini_model",
    default="gemini-3-flash-preview",
    help="The Gemini model name to use for summarization.",
)

MAX_LLM_RETRIES = flags.DEFINE_integer(
    "max_llm_retries",
    default=32,
    help="The maximum number of retries for LLM calls if validation fails.",
)

MAX_ATTEMPTS_PER_CONVERSATION = flags.DEFINE_integer(
    "max_attempts_per_conversation",
    default=8,
    help=(
        "The maximum number of attempts to process a conversation. After this "
        "number of retries, if there are still validation or restriction "
        "failures, we create a new conversation."
    ),
)

MAX_WORKERS = flags.DEFINE_integer(
    "max_workers",
    default=8,
    help="The maximum number of worker threads for parallel LLM requests.",
)

MAX_CHUNK_PARALLELIZATION = flags.DEFINE_integer(
    "max_chunk_parallelization",
    default=8,
    help="The maximum number of chunks to process in parallel.",
)

LLM_THROTTLING_STRATEGY = flags.DEFINE_enum(
    "llm_throttling_strategy",
    default="semaphore",
    enum_values=["semaphore", "token_bucket"],
    help="The strategy used for LLM requests.",
)

MAX_LLM_PARALLELIZATION = flags.DEFINE_integer(
    "max_llm_parallelization",
    default=8,
    help="The maximum number of parallel threads for parallel LLM requests.",
)

LLM_TOKEN_LIMIT_PER_MINUTE = flags.DEFINE_integer(
    "llm_token_limit_per_minute",
    default=7_000_000,
    help="The token limit per minute for token-bucket throttling.",
)

USE_VERTEX_AI_API = flags.DEFINE_bool(
    "use_vertex_ai_api",
    default=False,
    help="Whether to use Vertex AI API for Gemini model access.",
)

VERTEX_AI_PROJECT_ID = flags.DEFINE_string(
    "vertex_ai_project_id",
    default=None,
    help=(
        "The related project ID for Vertex AI API usage. Only needed if "
        "--use_vertex_ai_api is set."
    ),
)

MAX_PARALLEL_BUNDLES = flags.DEFINE_integer(
    "max_parallel_bundles",
    default=4,
    help="Max number of bundles to process in parallel.",
)

USE_SRCFS_FILE_READING = flags.DEFINE_bool(
    "use_srcfs_file_reading",
    default=False,
    help=(
        "Whether to use SrcFS for file reading, NOTE: not yet universally "
        "respected."
    ),
)

ADD_GRAPHVIZ_TOOL = flags.DEFINE_bool(
    "add_graphviz_tool",
    default=False,
    help="Whether to add the graphviz tool to a graph service MCP agent.",
)

REVIEW_ANSWER = flags.DEFINE_bool(
    "review_answer",
    default=False,
    help=(
        "Whether to use an LLM to review answers before they are returned to "
        "the user."
    ),
)

DEBUG_MODE = flags.DEFINE_bool(
    "debug",
    default=False,
    help="Whether to run with debug mode enabled.",
)
