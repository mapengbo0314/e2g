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

# Run with a config file
python3 indexing/generate_bundles.py --dry_run --config=indexing/config/my_project.textproto --model_name=mock

# OR run with a direct repo URL (no config needed)
python3 indexing/generate_bundles.py --repo_url="https://github.com/user/repo.git" --output_dir="./local_out" --model_name=mock
```

## Running a Full Indexing Pass

To run a real indexing pass with LLM generation, you must provide a Gemini API key.

1.  **Set your API Key**:
    ```bash
    export GOOGLE_API_KEY="your-api-key-here"
    ```

2.  **Execute the Generator**:
    ```bash
    python3 indexing/generate_bundles.py --config=indexing/config/my_project.textproto
    ```

-   `--config`: Path to your `.textproto` bundle configuration. Optional if `--repo_url` is provided.
-   `--model_name`: **(Required)** The specific model to use (e.g., `gemini-1.5-pro`, `gemma4:e2b`).
-   `--repo_url`: The Git repository URL to index.
-   `--output_dir`: Where to save the index files.
-   `--dry_run`: Enable mocked LLM responses.
-   `--llm_provider`: The provider to use (gemini, openai, anthropic, ollama). Default: `gemini`.

### Example: Running locally with Ollama

The indexing engine now supports local tool-based research (Code Search and File Reading) when using Ollama.

```bash
./.venv/bin/python -m indexing.generate_bundles \
    --repo_url="https://github.com/mapengbo0314/span-landing.git" \
    --output_dir="./local_outputs/span_landing_index" \
    --llm_provider=ollama \
    --model_name=gemma4:e2b
```

### Example .textproto (indexing/config/my_project.textproto)

```textproto
bundle_name: "my_project"
input {
  directory: "src"
}
input {
  directory: "lib"
}
exclude_pattern: ".*_test\\.py"
custom_output {
  output_directory: "index_out/"
}
```

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
