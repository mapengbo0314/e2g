# Build targets for the AI Codebase Indexing pipeline.
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@pip//:requirements.bzl", "requirement")
py_library(
    name = "chunker",
    srcs = ["chunker.py"],
    deps = [
        "//indexing:file_utils",
    ],
)

py_library(
    name = "error_prompt_generator",
    srcs = ["error_prompt_generator.py"],
    deps = [
        "//indexing:prompt_templates",
    ],
)

py_library(
    name = "file_utils",
    srcs = ["file_utils.py"],
)

py_binary(
    name = "generate_bundles",
    srcs = ["generate_bundles.py"],
    deps = [
        ":chunker",
        ":llm_indexer",
        ":orchestrator",
        ":reindexing",
        ":sequential_llm_prompter",
        ":shared_flags",
        ":state",
        ":summary_merger",
        ":verification",
        ":work_unit",
    ],
)

py_library(
    name = "llm_indexer",
    srcs = ["llm_indexer.py"],
    deps = [
        ":chunker",
        ":error_prompt_generator",
        ":file_utils",
        ":prompt_templates",
        ":rendering",
        ":schema",
        ":sequential_llm_prompter",
        ":state",
        ":summary_merger",
        ":work_unit",
    ],
)

py_library(
    name = "orchestrator",
    srcs = ["orchestrator.py"],
    deps = [
        ":file_utils",
        ":llm_indexer",
        ":reindexing",
        ":root_map",
        ":schema",
        ":state",
        ":verification",
        ":work_unit",
        requirement("tenacity"),
    ],
)

py_library(
    name = "prompt_templates",
    srcs = ["prompt_templates.py"],
    deps = [
        ":schema",
        requirement("pydantic"),
    ],
)

py_library(
    name = "reindexing",
    srcs = ["reindexing.py"],
    deps = [
        ":work_unit",
    ],
)

py_library(
    name = "rendering",
    srcs = ["rendering.py"],
)

py_library(
    name = "root_map",
    srcs = ["root_map.py"],
    deps = [
        ":schema",
        ":work_unit",
    ],
)

py_library(
    name = "schema",
    srcs = ["schema.py"],
    deps = [
        requirement("pydantic"),
    ],
)

py_library(
    name = "sequential_llm_prompter",
    srcs = ["sequential_llm_prompter.py"],
    deps = [
        ":error_prompt_generator",
        ":prompt_templates",
        ":schema",
        ":verification_types",
        requirement("google-generativeai"),
        requirement("google-cloud-aiplatform"),
        requirement("openai"),
        requirement("anthropic"),
        requirement("ollama"),
    ],
)

py_library(
    name = "shared_flags",
    srcs = ["shared_flags.py"],
)

py_library(
    name = "state",
    srcs = ["state.py"],
)

py_library(
    name = "summary_merger",
    srcs = ["summary_merger.py"],
    deps = [
        ":schema",
    ],
)

py_library(
    name = "verification",
    srcs = ["verification.py"],
    deps = [
        ":schema",
        ":verification_types",
    ],
)

py_library(
    name = "verification_types",
    srcs = ["verification_types.py"],
    deps = [
        requirement("pydantic"),
    ],
)

py_library(
    name = "work_unit",
    srcs = ["work_unit.py"],
)
