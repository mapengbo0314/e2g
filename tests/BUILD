# Build targets for testing the AI Codebase Indexing pipeline.
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
py_test(
    name = "test_code_standards",
    srcs = ["test_code_standards.py"],
)

py_test(
    name = "test_dry_run",
    srcs = ["test_dry_run.py"],
    deps = [
        "//indexing:generate_bundles",
    ],
)

py_test(
    name = "test_schema",
    srcs = ["test_schema.py"],
    deps = [
        "//indexing:schema",
    ],
)

py_test(
    name = "test_verification",
    srcs = ["test_verification.py"],
    deps = [
        "//indexing:verification",
        "//indexing:verification_types",
        "//indexing:schema",
    ],
)
