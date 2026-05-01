# Build targets for indexing utility scripts.
load("@rules_python//python:defs.bzl", "py_library", "py_binary")

py_library(
    name = "bundle_verifier_lib",
    srcs = ["bundle_verifier.py"],
    deps = [
        "//indexing/config:bundle_pb2",
        "//indexing/utils:text_format",
    ],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "bundle_verifier",
    srcs = ["bundle_verifier.py"],
    deps = [":bundle_verifier_lib"],
    visibility = ["//visibility:public"],
)
