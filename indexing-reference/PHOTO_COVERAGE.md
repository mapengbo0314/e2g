# Reference Photo Coverage

This document tracks which `reference-photos/` screenshots appear to map to files in `indexing-reference/`.

Rule used for this pass:
- Ignore files already populated with more than 80 lines.
- Only treat a photo match as confirmed when the filename is visible in the
  tab or breadcrumb.
- Prefer correcting wrong attributions over keeping a thin but inaccurate fill.

## In Scope Files

These are the current `indexing-reference/` files at 80 lines or fewer:

- `bundle_storage.py`
- `chunker.py`
- `constants.py`
- `error_prompt_generator.py`
- `file_utils.py`
- `github_cloner.py`
- `llm_indexer.py`
- `multi_bundle_state.py`
- `README.md`
- `root_map.py`
- `schema.py`
- `sequential_llm_prompter.py`
- `shared_flags.py`
- `state.py`
- `summary_merger.py`
- `work_unit.py`

## Confirmed Photo Matches

These matches were confirmed by visually checking sampled screenshots where the filename is visible in the editor tab or breadcrumb.

| File | Status | Evidence |
| --- | --- | --- |
| `llm_indexer.py` | transcribed more precisely | `IMG_1655.HEIC` clearly shows `llm_indexer.py` lines 79-178, including `__init__`, `llm_prompter`, and most of `_generate_index_for_chunk()`. |
| `shared_flags.py` | top-of-file block confirmed | `IMG_1665.HEIC` clearly shows `shared_flags.py` lines 1-92 with multiple flag defaults and help strings. |

## Likely Matches But Lower Priority

These are real matches to the original indexing codebase, but they are currently out of scope for filling because the local reference file is already over 80 lines.

| File | Evidence |
| --- | --- |
| `generate_bundles.py` | `IMG_1607.HEIC` through nearby sequential screenshots appear to be continuous slices of `generate_bundles.py`. |
| `reindexing.py` | `IMG_1615.HEIC` shows `reindexing.py`; adjacent images likely continue the same file. |
| `prompt_templates.py` | `IMG_1645.HEIC` shows `prompt_templates.py`. |
| `change_detection/change_detection_strategy.py` | `IMG_1669.HEIC` and `IMG_1670.HEIC` show this file, but it is outside the current top-level under-80-line fill target. |
| `change_detection/git_change_detection_strategy.py` | `IMG_1667.HEIC` and `IMG_1668.HEIC` show this file, but it is outside the current top-level under-80-line fill target. |
| `github_cloner.py` | A later screenshot in the same sequence clearly shows `github_cloner.py`, though I have not yet pinned the exact image number in this document. |

## Not Yet Located Clearly In Sampled Photos

I did not see a clear filename match yet for these in the sampled checkpoints:

- `bundle_storage.py`
- `chunker.py`
- `constants.py`
- `error_prompt_generator.py`
- `file_utils.py`
- `multi_bundle_state.py`
- `README.md`
- `root_map.py`
- `schema.py`
- `sequential_llm_prompter.py`
- `state.py`
- `summary_merger.py`
- `work_unit.py`

## Notes

- The earlier pass had at least two bad matches: `IMG_1655.HEIC` is `llm_indexer.py`,
  not `schema.py`, and `IMG_1665.HEIC` is `shared_flags.py`, not
  `sequential_llm_prompter.py`.
- The screenshots are strongly sequential. A single file often spans several
  consecutive images.
- The first image in a run is often the best place to identify the filename from
  the tab.
- Several later screenshots clearly come from directories outside the current
  top-level `indexing-reference/` set, such as `change_detection/`. Those are
  useful architectural references, but they do not directly map to the current
  thin top-level files.
- The next precise pass should continue one file at a time: confirm filename,
  capture the exact image span, then transcribe only that span.
