"""Configuration for path filtering during indexing."""

# List of file extensions that are indexed by default.
# This can be extended per-bundle using 'additional_extensions'.
APPROVED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".rs",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".proto",
    ".textproto",
    ".prototxt",
    ".sql",
    ".sh",
    ".bash",
}

# Directories that are always excluded from indexing.
DEFAULT_EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "bazel-bin",
    "bazel-out",
    "bazel-testlogs",
    "dist",
    "build",
}
