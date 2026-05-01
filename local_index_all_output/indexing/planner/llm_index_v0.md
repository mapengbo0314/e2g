# Overview

The `indexing/planner` directory contains the core logic for planning the Recursive-Index indexing process. It implements the `Planner` class, which manages filesystem scanning, directory statistics collection, and the aggregation of directories into manageable work units. This functionality is designed to prepare a plan for a subsequent reindexing operation by grouping related file system content based on size constraints and path structures.

The planner's primary goal is to transform raw filesystem data into an `IndexPlan`, which specifies which work units need to be processed or deleted. This is achieved by recursively scanning input root directories, collecting file statistics, filtering files based on configuration, and employing a Union-Find algorithm within the `_aggregate_small_work_units` method to group small directories into larger work units, ensuring that the work units adhere to a specified maximum size limit.

The system relies on imported definitions for `WorkUnit` and reindexing protocols, and manages path canonicalization to handle input prefixes, providing a structured and canonical representation of the filesystem structure for the indexing process.

# Deep Dive

The `indexing/planner` directory contains the core logic for planning the Recursive-Index indexing process. It is implemented in `planner.py` and defines the necessary data structures and methods to manage the filesystem scanning and aggregation for indexing.

**Core Components and Logic in `planner.py`:**

1.  **Data Structures:**
    *   `DirectoryStats`: Holds statistics for a single directory, including file lists, total size, and whether it contains subdirectories.
    *   `IndexPlan`: A container for the final plan, summarizing all work units, work units to process, and paths to delete.
    *   `PathFilteringConfig`: A structure defining configuration for filtering files based on path patterns, file extensions, and additional extensions.
    *   `IndexDifferProtocol`: A protocol defining the interface for providing reindexing difference calculations.

2.  **Planner Implementation (`Planner` class):**
    *   **Initialization:** The planner is initialized with root directories, filtering configurations, maximum work unit size, and an optional index differ.
    *   **Path Canonicalization:** Methods are implemented to strip an input prefix from file paths to standardize the indexing context.
    *   **File Filtering:** Logic is present to apply filters based on allowed silos and specified file extensions.
    *   **Directory Scanning (`_get_indexable_directories`):** This method recursively scans the root directories. It collects file statistics, excludes files larger than 1MiB, groups files by parent directory, and identifies all relevant directories to be indexed.
    *   **Work Unit Aggregation (`_aggregate_small_work_units`):** This method aggregates small directories into their parents to form `WorkUnit`s using a Union-Find algorithm. It merges directories into work units if the aggregated size does not exceed the maximum allowed work unit size, optimizing the grouping of files for indexing.
    *   **Planning (`plan` method):** The main method orchestrates the process: scanning directories, aggregating into work units, canonicalizing them, and finally using the optional `index_differ` to determine the final list of work units to process and paths to delete, producing an `IndexPlan`.

**Interactions with Subdirectories:**

The planner operates by scanning the filesystem rooted at the input root directories. It collects statistics from all discovered directories. The aggregation phase involves grouping files and directories from these discovered locations into cohesive `WorkUnit`s, which represent manageable chunks of the filesystem to be processed by the reindexing logic defined by the injected `IndexDifferProtocol`.

# Key Individual Components

- **planner.py**: Implements the core logic for planning the Recursive-Index indexing process, handling filesystem scanning, work unit aggregation using a Union-Find algorithm, path canonicalization, and determining the final index plan based on reindexing requirements.

# Key Interfaces

- **IndexDifferProtocol**: A protocol defining the interface for plugging in local reindexing reference logic, specifically requiring a method to determine which work units need to be reindexed.

# Key Dependencies

- **indexing:reindexing**: Used to potentially import the `DiffForReindexing` class for calculating reindexing differences.
- **indexing:work_unit**: Used to import the `WorkUnit` data structure for defining indexing work units.

# Configuration and flags

- **Max Work Unit Size Bytes**: The maximum aggregated size allowed for a group of directories to be considered a single work unit, defaulted to 500,000 bytes. (Defined in: planning logic within planner.py)
- **Input Prefix to Strip**: A prefix path that is stripped from file paths during canonicalization to standardize the indexing context. (Defined in: Initialization of Planner)
- **Allowed Silos**: A set of paths (silos) that are allowed to be scanned and indexed, used for file filtering. (Defined in: Initialization of Planner)
- **Exclude/Include Patterns & Extensions**: Configuration for filtering files based on path patterns and desired file extensions. (Defined in: PathFilteringConfig)

# All Subcomponents

- `BUILD`
- `planner.py`