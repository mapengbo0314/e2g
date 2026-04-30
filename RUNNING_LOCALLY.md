# Running the Trust-Oriented Indexing Engine Locally

This guide explains how to run the indexing pipeline on your local machine for development, testing, and production use.

## Prerequisites

1.  **Python 3.10+**: Ensure you have a modern Python environment.
2.  **Dependencies**: Install the required packages:
    ```bash
    pip install pydantic pytest typing-extensions
    ```

## Running a Dry Run (Recommended for First Use)

The dry run mode allows you to verify the entire pipeline (planning, generation, verification, and root map consolidation) without calling the actual Gemini API. This is the fastest way to ensure your environment is set up correctly.

```bash
# Set PYTHONPATH to the project root
export PYTHONPATH=.

# Run the bundle generator with the dry-run flag
python3 indexing/generate_bundles.py --dry_run --bundle_name=my_project --root_dirs=./path/to/source
```

## Running a Full Indexing Pass

To run a real indexing pass with LLM generation, you must provide a Gemini API key.

1.  **Set your API Key**:
    ```bash
    export GOOGLE_API_KEY="your-api-key-here"
    ```

2.  **Execute the Generator**:
    ```bash
    python3 indexing/generate_bundles.py --bundle_name=my_project --root_dirs=./path/to/source
    ```

### Configuration Flags

-   `--bundle_name`: A unique identifier for your project.
-   `--root_dirs`: Comma-separated list of directories to index.
-   `--output_dir`: (Optional) Where to save the index files. Defaults to `index_out/`.
-   `--dry_run`: Enable mocked LLM responses for verification logic testing.

## Running Tests

We have a comprehensive test suite to ensure the pipeline remains stable.

```bash
# Run all tests
PYTHONPATH=. pytest tests/

# Run specifically the dry-run pipeline test
PYTHONPATH=. pytest tests/test_dry_run.py

# Check code standards (10-line comment rule)
PYTHONPATH=. pytest tests/test_code_standards.py
```

## Understanding the Output

The output will be generated in the `index_out/` directory (or your specified `--output_dir`):
-   `llm_index_v0.json`: The canonical structured data for the index.
-   `llm_index_v0.md`: The human-readable Markdown rendering.
-   `root_map_v0.md`: The consolidated overview map for the entire bundle.
-   `verification_cache/`: Stores results of artifact verifications to speed up subsequent runs.
