# Build targets for the indexing planner.
load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "planner",
    srcs = ["planner.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//indexing:reindexing",
        "//indexing:work_unit",
    ],
)
