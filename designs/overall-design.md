# Recursive-Index: Overall System Design

## Core Philosophy
Recursive-Index is designed to provide a "Mental Model" of large codebases by creating a hierarchical index of LLM-generated summaries. This allows both human developers and AI agents to reason about multi-million line projects that would otherwise exceed context limits.

## Key Features

### 1. Codebase Indexing & Summarization
- **Purpose**: Processes a configured codebase (a "bundle") and creates a hierarchical index of Markdown summaries.
- **Implementation**: An automated backend process configured via bundle files (e.g., `.textproto` files).

### 2. Interactive Q&A Interface
- **Purpose**: Provides a web interface to ask natural language questions about an indexed codebase.
- **Workflow**:
    - Select a bundle from the available list.
    - Ask a technical question (e.g., "How does the authentication module handle token renewal?").
    - The system performs "deep research" using the hierarchical index and provides a grounded, synthesized answer.

### 3. Command-Line Interface (CLI)
- **Purpose**: A tool for interactive Q&A sessions and providing additional context.
- **Usage**:
    - Basic query: `recursive-index --bundle_names=my_bundle`
    - Adding context: `recursive-index --bundle_names=my_bundle --extra_context=./design_doc.md`
    - Adjusting research depth: `--target_runtime_seconds=120`

### 4. MCP Server Integration
- **Purpose**: Exposes the codebase intelligence to other AI tools and IDEs via the Model Context Protocol (MCP).
- **Benefits**: Allows tools like IDE agents to use the `query_codebase_expert` tool to understand code context.

## Detailed Indexing Walkthrough

### Phase 1: Initialization
1.  **Scanning**: The system reads bundle configurations and identifies the target directories or Git repositories.
2.  **Resource Planning**: Calculates the scale of the codebase and initializes parallel workers.
3.  **Throttling**: Sets up rate-limiting strategies to manage API quotas across concurrent indexing tasks.

### Phase 2: Per-Bundle Execution
1.  **Preparation**: For Git-based bundles, the repository is cloned into a temporary workspace.
2.  **Differing**: If re-indexing, the system identifies changed, added, or deleted files to minimize unnecessary LLM calls.
3.  **Work Unit Creation**: Groups files and directories into logical "Work Units" for processing.

### Phase 3: The Indexing Loop (Bottom-Up)
1.  **Epochs**: Indexing occurs in multiple "epochs" to handle dependencies.
    - **Epoch 0**: Generates initial summaries for files and leaf directories based on local content.
    - **Epoch 1+**: Passes global context (the "Root Map") back to the indexer to refine summaries with cross-directory awareness.
2.  **Orchestration**: Ensures a directory is only summarized after all its children have been successfully processed.

### Phase 4: Summary Synthesis
1.  **File Summarization**: Large files are chunked, summarized individually, and then synthesized into a single file-level overview.
2.  **Directory Summarization**: Synthesizes the summaries of all child files and subdirectories into a high-level directory overview.
3.  **Root Map Generation**: Concatenates top-level summaries into an architectural map of the entire project.
    - **Architectural Synthesis**: A "Senior Architect" persona synthesizes the raw map of overviews into a cohesive architectural summary using a recursive Map-Reduce pattern. This ensures the top-level summary remains grounded even for very large projects.
    - **Health Monitoring**: Calculates project-wide "Index Health" by weighting the confidence scores of individual directory summaries by their respective codebase size (LOC/bytes).


## Output Structure
The generated index consists of a hierarchy of JSON files containing:
- **Overviews**: High-level summaries for humans.
- **Metadata**: Structural information, dependencies, and indexing stats.
- **Last Indexed Info**: Tracks the specific version (commit SHA) and timestamp of the index.

---

## Technical Maintenance
- **Build System**: Uses Bazel for dependency management and running the pipeline.
- **Validation**: Includes a `bundle_verifier` to ensure configurations stay within operational limits (e.g., < 10M LoC per bundle).
- **Configuration Enforcement**: The system mandates the use of `.textproto` configuration files for all indexing runs. This ensures that every bundle definition is explicit, versionable, and adheres to the formal `ProjectBundle` structure, preventing ad-hoc or inconsistent indexing definitions.
- **Testing**: Comprehensive integration tests verify that the "Index Expert" can accurately answer questions using the generated summaries.
