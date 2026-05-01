# Overview

The indexing/config directory contains Protocol Buffer definitions that define the schema for project bundles used in the indexing system. This directory primarily establishes the structure for grouping directories, setting filtering rules, and defining how Git repositories are included in an index.

The core definitions are found in bundle.proto, which defines the `ProjectBundle` message. This message outlines the structure for bundling input directories, specifying exclusion and inclusion patterns for file selection, and configuring output modes (CustomOutput or InterleavedOutput). It also includes definitions for `InputDirectory` (specifying input paths with optional research guidance), `GitRepository` (for indexing Git repositories), and `CustomSection` (for generating custom index content).

Specific configurations are provided by separate files: `aadc.textproto` defines a bundle named 'aadc' with specific input directories related to AI training and demographics data. Additionally, `rcs.textproto` defines another bundle named 'rcs' focused on the Core Java codebase and APIs, along with exclusion patterns to filter test data.

# Deep Dive

The `indexing/config` directory contains configuration files defining project bundles for indexing, primarily using Protocol Buffers (`.proto`) files. These files define the structure for how directories are selected, filtered, and how Git repositories are handled during the indexing process.

**`indexing/config/bundle.proto`**
This file defines the core structure for a `ProjectBundle` message. It specifies how a bundle is constructed by defining:

1.  **`input`**: A repeated field specifying the root directories to be indexed (e.g., `ads/ai/aadc/`, `production/borg/aadc-demographics`).
2.  **Filtering Logic**: Fields for `exclude_pattern` (to exclude files/directories matching regex) and `include_pattern` (to filter for files matching regex).
3.  **`InputDirectory` Message**: Defines a specific input directory and allows for optional `research_guidance` to provide instructions to a researcher agent.
4.  **`GitRepository` Message**: Defines the metadata for indexing Git repositories, including owner, name, and URL.
5.  **`GitInput` Message**: Contains `repository_input` and an optional `Versioning` field to specify index versions based on commit SHAs.
6.  **`output_config`**: Defines how the final index files are generated, allowing for `CustomOutput` (specifying an output directory) or `InterleavedOutput` (for interleaving outputs).

**`indexing/config/aadc.textproto`**
This file defines a specific project bundle named `aadc`. It specifies the set of root directories to be indexed, which include paths related to AI training workflows, demographics, and security data, defining the scope for the 'aadc' bundle.

**`indexing/config/rcs.textproto`**
This file defines a separate project bundle named `rcs`. It specifies input directories for the Core Java codebase and APIs, along with exclusion patterns intended to filter out large test data or noise patterns.

# Key Individual Components

- **aadc.textproto**: Defines the input directories for the 'aadc' project bundle, listing paths related to AI training, demographics, and security data.
- **bundle.proto**: Defines the structure for a project bundle, including fields for input directories, exclusion/inclusion patterns, indexer configuration, Git repository information, and output configurations.
- **rcs.textproto**: Defines a separate project bundle named 'rcs' focusing on the Core Java codebase and APIs, including specific exclusion patterns for test data.

# Key Dependencies

- **coresystems/data/excellence/applications/indexing/config/indexer/indexer_config.proto**: Used by `bundle.proto` to reference the configuration structure for the indexer.

# Configuration and flags

- **bundle.proto**: Defines the schema for project bundles, handling inputs, filtering logic, Git repository indexing, and output configurations for indexing operations. (Defined in: indexing/config/bundle.proto)
- **aadc.textproto**: Specifies the input directories that form the 'aadc' bundle, defining the scope for indexing. (Defined in: indexing/config/aadc.textproto)
- **rcs.textproto**: Specifies the input directories for the 'rcs' bundle and defines exclusion patterns for test data. (Defined in: indexing/config/rcs.textproto)

# All Subcomponents

- `aadc.textproto`
- `bundle.proto`
- `rcs.textproto`