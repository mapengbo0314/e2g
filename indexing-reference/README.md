# Indexing Reference

This is the reduced indexing core derived from the reference screenshots.
It keeps the pieces that appear central to bundle configuration, directory
summarization, orchestration, file access, and agent-facing integration.

## Kept directories

- `change_detection`
- `config`
- `continuous`
- `filesystem`
- `g3doc`
- `gemini_cli`
- `index_expert`
- `indexer`
- `mcp`
- `planner`
- `ui`
- `utils`

## Kept root modules

- `generate_bundles.py`
- `orchestrator.py`
- `llm_indexer.py`
- `chunker.py`
- `summary_merger.py`
- `schema.py`
- `prompt_templates.py`
- `sequential_llm_prompter.py`
- `file_utils.py`
- `bundle_storage.py`
- `state.py`
- `root_map.py`
- `context.py`
- `constants.py`
- `shared_flags.py`
- `multi_bundle_state.py`
- `work_unit.py`
- `reindexing.py`
- `github_cloner.py`
- `error_prompt_generator.py`

The surrounding `_agents/` workspace is where media-driven transcription and
file population workflows live, while this directory remains a reference-first
scaffold for the original indexing shape.
