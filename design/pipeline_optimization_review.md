# Pipeline Optimization Plan — Technical Review

## Review / Query Checklist
- Severity taxonomy: [Critical], [High], [Medium], [Low]
- Impact / Regression: High (system crashes, LLM poisoning, infinite loops, resource leaks)
- Reproducibility: Deterministic under load or specific failure conditions
- Confidence: High

---

## Findings

### 1. [Critical] [Chunking & Merging] `NoneType` Crash Bomb on Fallback
**Finding Summary:** Fallback logic on non-validation errors returns `None` instead of a fallback model, causing a guaranteed `AttributeError` crash during the merge phase.
**Evidence:** 
- `llm_indexer.py: _generate_index_for_chunk` (Plan O1)
- `llm_indexer.py: _merge_with_retries` (Plan P1)
**Notes:** 
If the LLM call fails with a network exception, JSON parsing error, or timeout, `result = getattr(ve, "result", None)` resolves to `None`. The final `if isinstance(result, BaseModel):` evaluates to `False`, and the function implicitly returns `None` (or explicitly if modified). When `_merge_with_retries` iterates over `chunk_docs` to build the context (`for doc in chunk_docs: doc_md = rendering.to_markdown(doc)`), it will crash the entire pipeline because `doc` is `None`. 
**Remediation:** You must explicitly synthesize a dummy/empty fallback `BaseModel` artifact when `result is None` so downstream components receive a valid object with a `best_effort` or `failed` verification state.

### 2. [Critical] [Prompter] LLM Prompt Poisoning via Infrastructure Errors
**Finding Summary:** Feeding non-validation exceptions directly into the `error_prompt` will cause severe LLM hallucinations.
**Evidence:**
- `llm_indexer.py: _generate_index_for_chunk` (Plan O1)
**Notes:**
The `except Exception as ve:` block catches *all* exceptions. If a `ConnectionTimeout` or `RateLimitError` occurs, `current_issues` becomes `[str(ve)]`. On the next retry, the LLM receives: *"Verification failed... Rejected Output: <empty>. Issues: ['ConnectionTimeout']"*. The LLM will attempt to "fix" its code to prevent a connection timeout, leading to nonsensical artifacts.
**Remediation:** Distinguish between `VerificationFailedError` (which warrants an updated `error_prompt`) and infrastructure exceptions (which require a silent retry with the exact same initial prompt).

### 3. [High] [Verification] Merger Verification Defeated by Context Truncation
**Finding Summary:** Truncating `chunk_context` for the Verifier guarantees false-positive hallucination rejections for large directories.
**Evidence:**
- `llm_indexer.py: _merge_with_retries` (Plan P1)
**Notes:**
The Merger LLM receives the full context of all chunks to generate the merged document. However, you truncate `chunk_context` at 24,000 characters before passing it to the Verifier. The Verifier will read valid aggregated claims in the merged document, fail to find supporting evidence in the truncated context, and reject the merge as a hallucination. This guarantees a failure loop and `Best Effort` fallback for large merges.
**Remediation:** Do not arbitrarily truncate the verification context. If local LLM context limits are strict, either verify the merged doc against chunks of the chunks (map-reduce verification) or skip verification entirely if the combined chunk context exceeds the window.

### 4. [High] [Orchestrator] Exponential Retry Amplification and Stalling
**Finding Summary:** Nesting a Tenacity retry loop inside a manual retry loop causes exponential amplification of network requests and pipeline stalling.
**Evidence:**
- `summary_merger.py: merge` (Plan O2)
- `llm_indexer.py: _merge_with_retries` (Plan P1)
**Notes:**
You wrapped `SummaryMerger.merge()` with `@tenacity.retry` (3 attempts). But it is called inside `_merge_with_retries` which has its own 3-attempt loop. A persistent network error triggers 3 Tenacity retries, raises to the manual loop, which catches it, creates an error prompt, and fires Tenacity *again*. This results in $3 \times 3 = 9$ network requests, compounding Tenacity's exponential backoff with `time.sleep(2 ** attempt)`.
**Remediation:** Remove infrastructure exception handling from the manual LLM-correction loop. Tenacity should handle network issues invisibly at the client level. The manual loop should strictly handle logic/validation self-correction.

### 5. [Medium] [State] Unbounded Memory Growth (JSONL Leaks)
**Finding Summary:** Append-only JSONL files solve I/O bottlenecks but introduce a memory and parse-time bottleneck across multi-epoch runs.
**Evidence:**
- `orchestrator.py: _SimpleProgressManager` (Plan O3 & O4)
- `verification.py: VerificationCache` (Plan V3)
**Notes:**
Because this is a multi-epoch pipeline, the same paths will be processed repeatedly over time. The append-only `.jsonl` files will grow indefinitely with redundant entries. `get_progress()` and `_load_cache()` read the entire file into memory. Over many epochs, this becomes an $O(E \times N)$ memory leak.
**Remediation:** Implement a compaction strategy. At the start of an orchestrator run (when no threads are competing), read the `.jsonl` file, deduplicate the keys in memory, and rewrite it as a fresh, compacted `.jsonl` file.

### 6. [Medium] [State] Dangling Legacy Files in Crash Recovery
**Finding Summary:** The `.json` to `.jsonl` cache migration is not entirely crash-safe and can permanently orphan the legacy file.
**Evidence:**
- `verification.py: _load_cache` (Plan V3)
**Notes:**
The migration logic executes atomic `os.replace(temp_path, self.cache_file)`, followed by `legacy_json_file.unlink()`. If the process crashes immediately after `os.replace`, the `.jsonl` is created but the `.json` remains. On the next run, `if legacy_json_file.exists() and not self.cache_file.exists():` is `False`. The `.json` file is permanently orphaned.
**Remediation:** Add an explicit cleanup fallback: if `legacy_json_file` exists but `cache_file` *also* exists, it indicates a previously interrupted migration. Unlink the legacy file safely.

### 7. [Medium] [RootMap] Map-Reduce Infinite Loop Risk
**Finding Summary:** Batching summaries up to a strict character limit lacks fallback logic for oversized items.
**Evidence:**
- `root_map.py: generate_summary` (Plan H3)
**Notes:**
The plan states: "Batch summaries up to `self.max_context_chars`". If a *single* directory's summary exceeds `max_context_chars`, the batching logic may fail to add it, potentially throwing an unhandled exception or entering an infinite loop.
**Remediation:** Ensure there is a forced truncation (`summary[:max_context_chars]`) or a secondary splitting mechanism for individual items that exceed the batch limit *before* attempting to batch them.

### 8. [Low] [Orchestrator] `time.sleep()` blocks ThreadPoolExecutor
**Finding Summary:** `time.sleep()` is used in a thread pool for backoff.
**Evidence:**
- `llm_indexer.py: _generate_index_for_chunk` (Plan O1)
**Notes:**
While the plan acknowledges this as an "accepted limitation", if `max_workers` is small (e.g., 2-4 for local LLMs) and multiple threads fail simultaneously, the entire pipeline halts until the sleeps expire.
**Remediation:** Consider replacing `time.sleep` with an asynchronous queue or a non-blocking retry mechanism in future iterations, though acceptable for the current scope if heavily documented.
