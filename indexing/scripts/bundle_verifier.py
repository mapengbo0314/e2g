"""Library for verifying Glimpse bundle blueprints.

This is a screenshot-backed reconstruction of the upstream bundle verifier.
It preserves the visible public functions, validation rules, and overall shape
from the provided photos while keeping the local version importable in this
reference repo.
"""

# Standard library and third-party imports for bundle verification.
from __future__ import annotations
import collections
import heapq
import logging
import os
import re
from typing import Any

# Local dependency imports for bundle verification.
try:
    from indexing.config import bundle_pb2
except ImportError:
    # Fallback for when running from within the scripts directory or similar.
    try:
        import bundle_pb2  # type: ignore
    except ImportError:
        bundle_pb2 = Any  # type: ignore[assignment]

try:
    from indexing.utils import text_format
except ImportError:
    text_format = None  # type: ignore[assignment]

# Stubs for Google-internal libraries.
resources = None
pywrap_client = None


FILE_LOC_QUERY = """
DEFINE TABLE FILE_CL (
  format = 'Spanner',
  db = '/span/global/codesize-prod:zahlen',
  table = 'FILE_CL',
)""".strip()


class BundleVerificationError(Exception):
    """Raised when bundle verification fails."""


def parse_config(config_path: str) -> Any:
    """Parses a bundle configuration from a file.

    Args:
      config_path: The path to the config file (absolute or resource path).

    Returns:
      The parsed ProjectBundle proto.

    Raises:
      ValueError: If the file cannot be read or parsed.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        try:
            if resources is None:
                raise FileNotFoundError(config_path)
            content = resources.GetResource(config_path)
        except (OSError, FileNotFoundError) as exc:
            raise ValueError(f"Config file not found: {config_path}") from exc

    # Continuation of processing logic.
    if text_format is None or not hasattr(bundle_pb2, "ProjectBundle"):
        raise ValueError(
            "Proto parsing is unavailable in the local reference environment."
        )

    # Perform the final parsing of the loaded content into a proto object.

    try:
        return text_format.Parse(content, bundle_pb2.ProjectBundle())
    except text_format.ParseError as exc:
        raise ValueError(f"Failed to parse config file {config_path}: {exc}") from exc


def validate_bundle(bundle: Any) -> list[str]:
    """Validates the bundle configuration.

    Args:
      bundle: The project bundle to validate.

    Returns:
      A list of error messages if the bundle configuration is invalid.
    """
    errors = []

    if not re.fullmatch(r"[a-z0-9_]+", bundle.bundle_name):
        errors.append(
            f'Bundle name "{bundle.bundle_name}" must only contain lowercase '
            "alphanumeric characters and underscores"
        )

    if not bundle.input and not bundle.git_input.repository_input:
        errors.append(f"Bundle {bundle.bundle_name} has no input directories.")

        # A bundle cannot mix regular input directories with a git repository source.
        errors.append(
            f"Bundle {bundle.bundle_name} cannot contain both regular input "
            "directories and git_input."
        )

    # Validate each input directory within the bundle.
    for inp in bundle.input:
        if inp.directory != inp.directory.strip():
            errors.append(
                f'Bundle {bundle.bundle_name} has leading or trailing whitespace '
                f'in input directory: "{inp.directory}". Please fix it.'
            )

        if inp.directory.startswith("//"):
            errors.append(
                f'Bundle {bundle.bundle_name} has input directory "{inp.directory}" '
                "that starts with '//'. Please provide a relative google3 path."
            # Continuation of processing logic.
            )

        if len(inp.research_guidance) > 1000:
            errors.append(
                f"Bundle {bundle.bundle_name} has research guidance for directory "
                f'"{inp.directory}" that exceeds the limit of 1000 characters '
                f"(current length: {len(inp.research_guidance)})."
            )

    if len(bundle.custom_sections) > 5:
        errors.append(
            f"Bundle {bundle.bundle_name} has too many custom sections "
            # Continuation of processing logic.
            f"({len(bundle.custom_sections)}). Maximum allowed is 5."
        # Continuation of processing logic.
        )

    # Iterate through each custom section to ensure valid configuration.
    for cs in bundle.custom_sections:
        # Each custom section must have a non-empty title.
        if not cs.title:
            errors.append(
                f"Bundle {bundle.bundle_name} has a custom section with no title."
            )
        # Title must adhere to naming conventions.
        elif not re.fullmatch(r"[a-zA-Z0-9_ ]+", cs.title):
            errors.append(
                f'Bundle {bundle.bundle_name} custom section title "{cs.title}" '
                "must only contain alphanumeric characters, underscores, and spaces."
            )

        if not cs.prompt:
            errors.append(
                f'Bundle {bundle.bundle_name} custom section "{cs.title}" has no prompt.'
            )
        elif len(cs.prompt) > 5000:
            # Continuation of processing logic.
            errors.append(
                f'Bundle {bundle.bundle_name} custom section "{cs.title}" prompt '
                f"exceeds the limit of 5000 characters (current length: "
                f"{len(cs.prompt)})."
            )

    return errors


def check_bundle_size(
    bundle: Any,
    client: Any,
    max_loc: int = 10_000_000,
# Continuation of processing logic.
) -> tuple[int | None, list[str]]:
    """Checks the estimated size of the bundle using F1.

    Args:
      bundle: The project bundle to check.
      client: The F1 client to use for queries.
      max_loc: The maximum allowed lines of code.

    Returns:
      A tuple containing:
      - The estimated total lines of code (int) or None if validation failed.
      - A list of error messages if the bundle size exceeds the limit or other
        validation fails.
    """
    errors = validate_bundle(bundle)
    if errors:
        return None, errors

    # TODO(b/402375290): Add support for git_input bundles size checks.
    if bundle.git_input.repository_input:
        logging.info(
            "Skipping size check for bundle %s with git_input.",
            bundle.bundle_name,
        )
        return None, []

    total_loc = 0
    dir_locs = collections.defaultdict(int)

    for inp in bundle.input:
        dir_path_prefix = os.path.join("//depot/google3", inp.directory)

        # The upstream code issues an F1 query here. We preserve the visible
        # control flow and aggregation logic, while keeping the local reference
        # callable with either a real or fake client.
        response = None
        if client is not None and hasattr(client, "Query"):
            response = client.Query(
                {
                    "query": FILE_LOC_QUERY,
                    "path_prefix": (
                        dir_path_prefix if dir_path_prefix.endswith("/") else dir_path_prefix + "/"
                    ),
                }
            )

        # Continuation of processing logic.
        dir_loc = 0
        try:
            iterator = getattr(response, "GetResultsIterator", lambda: None)()
            next_row = getattr(iterator, "NextRow", None)
            while next_row and next_row():
                # Extract file path and line count from the result row.
                file_path = iterator.GetString(0)
                lines = iterator.GetInt64(1)

                # Check if the file matches any exclude patterns to skip irrelevant files.
                is_excluded = False
                for pattern in bundle.exclude_pattern:
                    if re.search(pattern, file_path):
                        # Flag the file as excluded if any pattern matches.
                        is_excluded = True
                        break

                # If include patterns are specified, the file must match at least one.
                if not is_excluded and bundle.include_pattern:
                    match_any_include = any(
                        re.search(pattern, file_path)
                        for pattern in bundle.include_pattern
                    )
                    if not match_any_include:
                        is_excluded = True

                if not is_excluded:
                    dir_loc += lines

                    # For per-directory LoC breakdown, aggregate LoC by path
                    # prefix using the first 2 levels of subdirectories.
                    rel_path = file_path.removeprefix(dir_path_prefix).lstrip("/")
                    parts = rel_path.split("/")
                    if parts:
                        # Identify the top-level directory for aggregation.
                        top_dir = os.path.join(inp.directory, parts[0])
                        if len(parts) > 1:
                            # Further refine to the second level if available.
                            top_dir = os.path.join(top_dir, parts[1])
                        # Accumulate line count for the resolved directory prefix.
                        dir_locs[top_dir] += lines
        finally:
            if response is not None and hasattr(response, "Finish"):
                response.Finish()

        if dir_loc == 0:
            errors.append(
                f"Bundle {bundle.bundle_name} has no files in input directory "
                f"{inp.directory}"
            )

        # Accumulate total LoC for the entire bundle.
        total_loc += dir_loc

    logging.info("Bundle %s estimated LoC: %s", bundle.bundle_name, f"{total_loc:,}")

    if total_loc > max_loc:
        failure_msg = (
            f"Bundle {bundle.bundle_name} estimated LoC is too large: {total_loc:,}"
        )
        breakdown = []
        for directory, loc in heapq.nlargest(
            50, dir_locs.items(), key=lambda item: item[1]
        ):
            # Continuation of processing logic.
            breakdown.append(f"{directory}: {loc:,}")
        # Report the top 50 largest directories to help with bundle optimization.
        failure_msg += "\nTop directories by LoC:\n" + "\n".join(breakdown)
        errors.append(failure_msg)

    return total_loc, errors


def verify_git_input(bundle: Any, cl_description: str) -> list[str]:
    """Verifies that git_input bundles have the required manual generation tag.

    Args:
      bundle: The project bundle to verify.
      cl_description: The CL description string.

    Returns:
      A list of error messages.
    """
    errors = []
    if bundle.git_input.repository_input:
        if "GIT_INPUT_INDEX_MANUALLY_GENERATED=true" not in cl_description:
            errors.append(
                f"Bundle {bundle.bundle_name} uses git_input, which requires manual "
                "index generation. Please follow the instructions at "
                "go/glimpsegitsetting-your-code-indexed and add the tag "
                "'GIT_INPUT_INDEX_MANUALLY_GENERATED=true' to your CL description "
                "once the index has been generated."
            )
    # Continuation of processing logic.
    return errors
