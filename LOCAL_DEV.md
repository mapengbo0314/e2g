# Local Development Guide: Codebase Indexing Pipeline

This guide explains how to run the Trust-Oriented Codebase Indexing Pipeline locally. We have updated the core modules to run without requiring upstream dependencies (like Borg or internal databases), and we support falling back to the standard Gemini API or performing a full mock execution.

## 1. Environment Setup

Ensure you are in the root of the repository. The pipeline relies heavily on the `indexing/` module, so the `PYTHONPATH` must be set appropriately when executing any script.

```bash
# Recommended: Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install google-generativeai pydantic
```

## 2. LLM Integration & API Keys

To perform a real indexing run, the pipeline uses Google's Generative AI to summarize and merge codebase directories. 

Set your `GEMINI_API_KEY` as an environment variable before running the orchestrator. The pipeline automatically switches from Vertex AI to the direct Google API when this key is detected.

```bash
export GEMINI_API_KEY="your_api_key_here"
```

## 3. Running the Pipeline

The main entry point for the local indexer is `generate_bundles.py`.

### A. Performing a Dry Run (Recommended for Testing)

To verify your configuration and ensure the Orchestrator successfully plans the indexing tasks without making any expensive LLM calls, use the `--dry_run` flag.

This will simulate the outputs using mocked text maps and will still generate the `.index_output` directory structure.

**Option 1: Standard Python Execution (Fastest)**
```bash
PYTHONPATH=. python indexing/generate_bundles.py \
    --input_dir="./indexing" \
    --output_dir="./local_index_output" \
    --dry_run
```

**Option 2: Bazel Hermetic Build**
If you prefer running within the Bazel sandbox (which guarantees consistent dependencies across environments), use:
```bash
bazel run //indexing:generate_bundles -- \
    --input_dir="./indexing" \
    --output_dir="./local_index_output" \
    --dry_run
```
*Note:* If you add new dependencies, you must synchronize Bazel's pip lockfile by running `pip-compile requirements.txt --output-file requirements_lock.txt` before running the Bazel target.

### B. Performing a Full Indexing Run

Once you are confident the paths are correctly resolved, you can remove the `--dry_run` flag and allow the LLM Prompter to do the heavy lifting:

```bash
PYTHONPATH=. python indexing/generate_bundles.py \
    --input_dir="./src" \
    --output_dir="./local_index_output"
```

## 4. Running the Engineering Standards Audit

We have a strict **10-line engineering documentation rule**. Every 10 consecutive lines of code must be accompanied by an explanatory grouping comment.

Before submitting any PR, ensure your code passes the standard audit:

```bash
PYTHONPATH=. pytest tests/test_code_standards.py -v --tb=short
```

If the audit fails, the script will tell you exactly which files and line numbers need semantic grouping comments injected.
