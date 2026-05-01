# Overview

The directory indexing/scripts contains utility code for verifying Glimpse bundle blueprints. The primary file, bundle_verifier.py, implements functions to parse bundle configurations, validate their structure, estimate bundle size using an F1 client query, and verify specific conditions related to git input bundles.

The script handles configuration parsing, structural validation (checking bundle names, input directory formats, research guidance length, and custom section constraints), and a size estimation mechanism that queries an external F1 system using a predefined file location query. It also includes logic to verify requirements for git input bundles, such as checking for the necessary manual index generation tag in commit messages.

# Deep Dive

The `indexing/scripts` directory contains utility scripts for verifying Glimpse bundle blueprints. The main file, `bundle_verifier.py`, implements functions to parse bundle configurations, validate their structure, estimate bundle size using an F1 client query, and verify specific conditions for `git_input` bundles.

Key functions and logic:

*   **`parse_config(config_path)`**: Reads a bundle configuration file, handling potential resource loading via `google3.pyglib.resources`, and parses the content into a `ProjectBundle` proto using `text_format`.
*   **`validate_bundle(bundle)`**: Checks the bundle configuration for several constraints. This includes ensuring the bundle name adheres to alphanumeric/underscore rules, verifying the presence and structure of input directories (checking for whitespace and paths starting with `//`), validating the length of `research_guidance` (max 1000 characters), and enforcing limits on the number of custom sections (max 5) and the length of custom section prompts (max 5000 characters).
*   **`check_bundle_size(bundle, client, max_loc)`**: Estimates the total lines of code (LoC) for the bundle by querying an external F1 client. It first runs `validate_bundle`. It handles `git_input` bundles by skipping the size check. For standard bundles, it iterates over input directories, constructs F1 queries using a predefined `FILE_LOC_QUERY` against the F1 client, filters results based on `bundle.include_pattern` and `bundle.exclude_pattern`, and aggregates the line counts. If the estimated LoC exceeds `max_loc`, it reports the total size and lists the top 50 largest directories.
*   **`verify_git_input(bundle, cl_description)`**: Checks bundles that use `git_input`. If `git_input` is present, it verifies that the CL description includes the tag `GIT_INPUT_INDEX_MANUALLY_GENERATED=true`, which is required when index generation is performed manually.

The script relies on several optional imports that use `try...except` blocks to provide local fallbacks if dependencies like proto bindings or the F1 client are missing, ensuring the script can run in environments without full dependencies.

# Key Individual Components

- **bundle_verifier.py**: Library for verifying Glimpse bundle blueprints, containing functions to parse configuration, validate bundle structure, check bundle size via F1, and verify git input tagging.

# Key Interfaces

- **parse_config**: Parses a bundle configuration from a file, handling file reading (including resource access) and parsing content into a ProjectBundle proto.
- **validate_bundle**: Validates the structure and content of a project bundle, checking bundle name format, input directory structure, research guidance length, custom section titles, and prompts.
- **check_bundle_size**: Checks the estimated lines of code (LoC) of a bundle using an F1 client query against a specified maximum limit, performing validation first.
- **verify_git_input**: Verifies that bundles using `git_input` have the required manual index generation tag in the CL description.

# Key Dependencies

- **google3.coresystems.data.excellence.applications.indexing.config**: Used to import the `bundle_pb2` proto bindings, which are necessary for parsing bundle configuration files.
- **google3.net.proto2.python.public.text_format**: Used for parsing the configuration content from files into protobuf objects.
- **google3.pyglib.resources**: Used for reading configuration files, potentially accessing resources via the `resources` object.
- **google3.pyglib.f1.client.pywrap_client**: Attempted import for the F1 client, used by `check_bundle_size` to estimate bundle size via code location queries.

# Configuration and flags

- **FILE_LOC_QUERY**: A string defining a Spanner table (`FILE_CL`) used in F1 queries to retrieve file location and line count information. (Defined in: indexing/scripts/bundle_verifier.py)

# All Subcomponents

- `BUILD`
- `bundle_verifier.py`