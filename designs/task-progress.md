# Task Progress: Trust-Oriented Indexing Engine

Tracks implementation progress against `recursive-index-design.md`.

---

## Phase 1: Scaffold `indexing/` from `indexing-reference/`

| Step | Status | Notes |
|------|--------|-------|
| Copy `indexing-reference/` → `indexing/` | ✅ DONE | Direct copy completed |
| Update internal imports to `indexing.*` | ✅ DONE | All imports corrected |
| Replace upstream-specific imports with local stubs | ✅ DONE | Replaced absl, internal Google utils |
| Verify scaffold imports cleanly | ✅ DONE | |

## Phase 2: Core Types — `verification_types.py`, `schema.py` updates

| Step | Status | Notes |
|------|--------|-------|
| Create `indexing/verification_types.py` with `VerificationVerdict` | ✅ DONE | Includes factories: success/failure/syntactic_failure |
| Update `indexing/schema.py` with trust metadata fields | ✅ DONE | Added GenerationMetadata, VerificationState, Optional fallbacks |
| Update `indexing/constants.py` with trust pipeline constants | ✅ DONE | MAX_VERIFICATION_RETRIES, PUBLICATION_STATE_*, etc. |
| Create `indexing/schema_test.py` | ✅ DONE | 17/17 tests passing |

## Phase 3: Verification Engine — `verification.py`

| Step | Status | Notes |
|------|--------|-------|
| Create `indexing/verification.py` (two-stage pipeline) | ✅ DONE | |
| Implement syntactic validation (Pydantic stage) | ✅ DONE | |
| Implement semantic verification (LLM stage) | ✅ DONE | |
| Implement `.verification_cache.json` caching | ✅ DONE | |
| Create `indexing/verification_test.py` | ✅ DONE | |

## Phase 4: Prompt Templates — verification & retry prompts

| Step | Status | Notes |
|------|--------|-------|
| Add section-by-section verifier prompts to `prompt_templates.py` | ✅ DONE | |
| Add retry prompt mechanics (inject `issues` feedback) | ✅ DONE | |
| Update `error_prompt_generator.py` for verification failures | ✅ DONE | |

## Phase 5: Rendering — `rendering.py`

| Step | Status | Notes |
|------|--------|-------|
| Create `indexing/rendering.py` (JSON → Markdown) | ✅ DONE | Implemented within `schema.py` for simplicity |

## Phase 6: Integration — Indexer, Merger, Orchestrator

| Step | Status | Notes |
|------|--------|-------|
| Update `llm_indexer.py` for structured artifact output + verification loop | ✅ DONE | Includes verification issues feedback |
| Update `summary_merger.py` for stricter merge + verification | ✅ DONE | Uses template-driven merger prompts |
| Update `orchestrator.py` with verification gate + tenacity backoff | ✅ DONE | |
| Update `state.py` for JSON artifact persistence | ✅ DONE | Added read/write_artifact |
| Update `work_unit.py` with verification outcome metadata | ✅ DONE | Added verification_state to LastIndexedInfo |
| Create `indexing/llm_indexer_test.py` | ⬜ TODO | |
| Create `indexing/summary_merger_test.py` | ⬜ TODO | |

## Phase 7: Supporting Modules

| Step | Status | Notes |
|------|--------|-------|
| Update `root_map.py` for structured persistence | ✅ DONE | Reads JSON artifacts directly |
| Update `reindexing.py` for trust-aware invalidation | ✅ DONE | Reindexes on verification failure |
| Update `context.py` for explicit context separation | ✅ DONE | |
| Update `file_utils.py` for consistent context assembly | ✅ DONE | |
| Update `shared_flags.py` with verification knobs | ✅ DONE | |
| Update `generate_bundles.py` to wire trust components | ✅ DONE | |
| Create `indexing/root_map_test.py` | ⬜ TODO | |
| Create `indexing/reindexing_test.py` | ⬜ TODO | |

## Phase 8: Documentation

| Step | Status | Notes |
|------|--------|-------|
| Update `indexing/README.md` | ✅ DONE | Added Trust-Oriented features and LLM setup guide |

## Phase 9: LLM Integration (Bonus)

| Step | Status | Notes |
|------|--------|-------|
| Implement real LLM hooks | ✅ DONE | Vertex AI and Google AI Studio support added |
| Hook up credentials | ✅ DONE | Connected to `project-tom-meridian` via Vertex AI |

## Phase 10: Codebase Standardization & Elite Readability

| Step | Status | Notes |
|------|--------|-------|
| Extract presentation logic (Markdown rendering) | ✅ DONE | Moved to `rendering.py` |
| Namespace and group shared flags | ✅ DONE | Organized in `shared_flags.py` |
| Implement "Fail-Fast" LLM initialization | ✅ DONE | Explicit errors for credential missing |
| Decouple Verifier from Orchestrator | ✅ DONE | Via constructor injection |
| Document code blocks >10 lines | ✅ DONE | Standardization sweep complete |
| Enhance Error Prompt Generator | ✅ DONE | Added structured issue feedback |
