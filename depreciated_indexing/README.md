# Trust-Oriented Indexing Engine

This directory contains the core codebase indexing pipeline, enhanced with artifact verification and trust-oriented persistence.

## Features

- **Recursive Summarization**: Summarizes codebases directory-by-directory.
- **Artifact Verification**: Mandatory two-stage verification (syntactic and semantic) for every index artifact.
- **Trust-Aware Persistence**: Stores both human-readable Markdown and structured JSON artifacts.
- **Incremental Re-indexing**: Automatically detects source changes or previous verification failures to ensure a trustworthy index.

## LLM Configuration

The engine supports two primary LLM backends:

### 1. Vertex AI (Recommended for GCP users)
- Set `use_vertex_ai_api = True` and provide `vertex_ai_project_id` in `shared_flags.py`.
- Ensure you are authenticated via `gcloud auth application-default login`.

### 2. Google AI Studio (API Key)
- Set `use_vertex_ai_api = False` in `shared_flags.py`.
- Provide your `google_api_key` in `shared_flags.py` or as an environment variable (support coming soon).

## Key Components

- `orchestrator.py`: Manages the parallel execution of indexing work units.
- `llm_indexer.py`: The main logic for chunking code and prompting the LLM.
- `verification.py`: Implements the syntactic and semantic verification gates.
- `schema.py`: Canonical definitions for `IndexDocument` and its components.
- `reindexing.py`: Logic for trust-aware incremental updates.

## Usage

To run the indexer locally:

```bash
python -m indexing.generate_bundles --input_dir <path_to_code> --output_dir <output_path>
```

Add `--reindex` to perform an incremental update that respects previous verification results.
