# Walkthrough Guide: Codebase Indexing Pipeline

This guide explains how to run the Trust-Oriented Codebase Indexing Pipeline locally. We have updated the core modules to run without requiring upstream dependencies (like Borg or internal databases), and we support falling back to standard provider APIs (Gemini, OpenAI, Anthropic) or performing a full mock execution, or running completely locally via Ollama.

## 1. Environment Setup

Ensure you are in the root of the repository. The pipeline relies heavily on the `indexing/` module, so the `PYTHONPATH` must be set appropriately when executing any script.

```bash
# Recommended: Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

## 2. LLM Integration & API Keys

The pipeline supports multiple LLM providers. You can choose which provider to use by passing the `--llm_provider` flag (options: `gemini`, `openai`, `anthropic`, `ollama`).

Set the appropriate environment variable for your chosen provider before running the orchestrator:

```bash
# For Gemini
export GEMINI_API_KEY="your_api_key_here"

# For OpenAI
export OPENAI_API_KEY="your_api_key_here"

# For Anthropic
export ANTHROPIC_API_KEY="your_api_key_here"

# For Ollama (Local)
# No API key required, but ensure the Ollama daemon is running locally.
# We recommend models like gemma2 or llama3 for best performance.
# e.g., ollama pull gemma4:e2b
```

## 3. Advanced Features & Robustness

The local indexing pipeline includes several "Self-Healing" features to handle the inconsistencies of local LLMs:

### A. Auto-Repair & Coercion
If an LLM (like Gemma) returns an empty object or forgets mandatory JSON wrapper keys (e.g., `key_dependencies`), the system will automatically **coerce** the data by injecting the missing empty structures. This prevents validation failures and unnecessary retries.

### B. Truncated JSON Handling
If a response is cut off (EOF while parsing), the prompter detects this and provides targeted feedback to the LLM to "finish your JSON response" in the next turn, rather than failing the entire file.

### C. Schema Integrity
The pipeline now explicitly instructs models to exclude `$defs` or "definitions" from their output, preventing them from hallucinating schema metadata and hitting context window limits.

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

Once you are confident the paths are correctly resolved, you can remove the `--dry_run` flag and specify your provider and model:

**Option 1: Local Directory Indexing**
```bash
./.venv/bin/python -m indexing.generate_bundles \
    --input_dir="./src" \
    --output_dir="./local_index_output" \
    --llm_provider=ollama \
    --model_name=gemma4:e2b
```

**Option 2: GitHub Repository Indexing (New)**
The system can now automatically clone, index, and cleanup remote repositories:
```bash
./.venv/bin/python -m indexing.generate_bundles \
    --repo_url="https://github.com/user/repo.git" \
    --output_dir="./github_index_output" \
    --llm_provider=ollama \
    --model_name=gemma4:e2b
```

**Option 3: Bazel Execution**
```bash
bazel run //indexing:generate_bundles -- \
    --repo_url="https://github.com/user/repo.git" \
    --output_dir="./github_index_output" \
    --llm_provider=ollama \
    --model_name=gemma4:e2b
```

## 4. Running the Engineering Standards Audit

We have a strict **10-line engineering documentation rule**. Every 10 consecutive lines of code must be accompanied by an explanatory grouping comment.

Before submitting any PR, ensure your code passes the standard audit:

```bash
PYTHONPATH=. pytest tests/test_code_standards.py -v --tb=short
```

If the audit fails, the script will tell you exactly which files and line numbers need semantic grouping comments injected.
