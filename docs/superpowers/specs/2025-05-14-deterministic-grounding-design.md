# Deterministic Injection and Metadata Extraction Design

**Status:** Draft
**Date:** 2025-05-14

## Goal
Improve the reliability of the indexing pipeline by:
1. Ensuring symbol blueprints and implementation invariants are deterministically grounded in AST data, overwriting any LLM hallucinations.
2. Collecting and exporting aggregate token usage and cost metadata for the entire indexing run.
3. Fixing nested class instantiation in the fallback Pydantic-like schema system.
4. Tuning chunking logic and origin tracking for better performance and traceability.

## 1. Deterministic Injection
**Location:** `indexing/sequential_llm_prompter.py` -> `prompt_for_indexing`

### Logic
After the `IndexDocument` is assembled from various agent stages:
- If `directory_files` is provided:
    - Iterate over each file path.
    - Resolve the absolute path using `repo_root`.
    - Read the file content.
    - Call `ast_extractor.extract_ast_grounding(file_path, source_code)`.
    - For each symbol and invariant:
        - Generate a deterministic ID using `ast_extractor.generate_deterministic_id`.
        - Ensure `source_kind` or `evidence_origin` is set to `"ast"`.
- Collect all symbols into a `schema.Blueprint` and all invariants into `schema.ImplementationInvariants`.
- Overwrite `artifact.blueprint` and `artifact.implementation_invariants` with these collections.

## 2. Metadata Extraction
**Location:** `indexing/root_map.py` -> `regenerate_root_map`

### Logic
- Initialize an aggregate metadata structure:
    ```json
    {
      "timestamp": "ISO-8601",
      "total_tokens": 0,
      "total_cost": 0.0,
      "models_used": []
    }
    ```
- As `collect_overviews` iterates through artifacts, it will now also return the `cost_report` or we will extract it directly in `regenerate_root_map`.
- Sum `total_tokens` (input + output) and `estimated_cost_usd`.
- Collect unique `model_name`s.
- Write the final object to `metadata.json` in the `output_dir`.

## 3. Bug Fixes

### 3.1 Regex Fallback (`indexing/schema.py`)
Update `_BaseModel.__init__` to use `re.findall` instead of `re.search`.
Iterate through all matches. The first match that is a valid `_BaseModel` subclass in `globals()` will be used as the target class for recursion. This allows `Optional[Overview]` to correctly resolve to `Overview`.

### 3.2 Chunking Math (`indexing/sequential_llm_prompter.py`)
In `prompt_for_enrichment`, update `num_chunks` to:
`math.ceil((len(skeleton.symbols) + len(skeleton.invariants)) / 40.0)`
This treats symbols and invariants as a single pool of items to be chunked into groups of ~40.

### 3.3 AST Fallback Source Kind (`indexing/ast_merger.py`)
In `ASTMerger.merge`, when a symbol or invariant from the skeleton is missing from the LLM enrichment, the resulting object should have `source_kind="ast_fallback"` (for symbols) or `evidence_origin="ast_fallback"` (for invariants).

## Verification Plan
- **Unit Tests**:
    - Test `schema.py` with `Optional[Overview]` in a mock class.
    - Test `ast_merger.py` fallback logic.
- **Integration Tests**:
    - Run `prompt_for_indexing` on a directory with known symbols and verify `IndexDocument` contains them even if they weren't in the LLM response.
    - Run `regenerate_root_map` and verify `metadata.json` is created with correct sums.
