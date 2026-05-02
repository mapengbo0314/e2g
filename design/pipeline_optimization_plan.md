# Pipeline Optimization Plan — Audit & Solutions (V4 - Final Hardened)

**Date**: 2026-05-01  
**Scope**: All 12 core indexing modules (~5,500 LOC)  
**Status**: V4 (Final Hardened - Incorporates SWE & Reviewer Agent Feedback)

---

## Architecture Overview

```
CLI (generate_bundles.py)
  └─▶ Orchestrator (orchestrator.py)  ─── Multi-epoch engine
        ├─▶ Planner        ─── Directory walker
        ├─▶ LlmIndexer     ─── Per-directory generation
        │     ├─▶ Prompter  ─── LLM interface + JSON coercion
        │     ├─▶ Chunker   ─── Large directory splitter
        │     └─▶ Merger    ─── Chunk reunifier
        ├─▶ Verifier        ─── 2-stage pipeline (syntactic + semantic)
        ├─▶ RootMap         ─── Health metrics + report (Now requires LLM injection)
        └─▶ State           ─── Epoch-based persistence
```

---

## 🔴 CRITICAL — Fix Immediately

### O1. Shared Mutable State & Verifier Parameter Routing (Concurrency Bug)

**File**: `orchestrator.py:504` and `llm_indexer.py`  
**Problem**: Verification issues are written to the shared `LlmIndexerConfig` object. Under parallel execution, threads overwrite each other's issues. Additionally, manual `time.sleep()` for exponential backoff blocks the thread pool, starving the system, especially when a local LLM struggles with concurrency.  
**Solution**: Pass issues through an immutable context. Explicitly define `VerificationFailedError`. Explicitly pass the `verifier` into the chunk threads.

```python
# llm_indexer.py — add exception definition
class VerificationFailedError(Exception):
    def __init__(self, message: str, result: any, issues: list[any]):
        super().__init__(message)
        self.result = result
        self.issues = issues

# llm_indexer.py — generate_index_for_work_unit()
# PASS the verifier explicitly to the executor
future_to_chunk_id = {
    executor.submit(
        self._generate_index_for_chunk,
        directory_path=work_unit.output_path,
        epoch=epoch,
        previous_root_map_content=previous_root_map_content,
        directory_contents_chunk=chunk,
        subdirectory_indexes=subdirectory_indexes,
        existing_index=existing_index,
        is_partial=True,
        verifier=verifier, # <--- CRITICAL FIX
    ): chunk_id
    for chunk_id, chunk in enumerate(chunks)
}
```

```python
# llm_indexer.py — _generate_index_for_chunk()
import time
import logging
from pydantic import BaseModel

def _generate_index_for_chunk(self, directory_contents_chunk, verifier=None, ...):
    max_attempts = 3
    current_issues = [] 
    previous_artifact = ""
    
    for attempt in range(max_attempts):
        try:
            error_prompt = ""
            if current_issues:
                error_msg = f"Verification failed for previous attempt.\nRejected Output:\n{previous_artifact}"
                error_prompt = self._config.error_prompt_generator.generate_error_prompt(
                    error_msg, current_issues
                ) + "\n\n"
                
            artifact_chunk = self._config.llm_prompter.prompt_for_indexing(
                error_prompt=error_prompt, # ...
            )
            
            if verifier:
                source_context = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents_chunk.items()])
                verdict = verifier.verify(artifact_chunk.model_dump_json(), source_context)
                if not verdict.passed:
                    raise VerificationFailedError("Chunk failed", result=artifact_chunk, issues=verdict.issues)
            
            # Ensure verification_state includes is_empty_bypass bridge mapping
            artifact_chunk.verification_state = schema.VerificationState(
                verified=True, confidence=1.0, issues=[], quality="verified",
                is_empty_bypass=getattr(verdict, 'is_empty_bypass', False) if verifier else False
            )
            return artifact_chunk
            
        except Exception as ve:
            if isinstance(ve, VerificationFailedError):
                current_issues = ve.issues
                result = getattr(ve, "result", None)
                previous_artifact = result.model_dump_json() if isinstance(result, BaseModel) else ""
            else:
                logging.warning(f"Transient infrastructure error: {ve}")
                result = None
            
            if attempt == max_attempts - 1:
                logging.error("Chunk failed after all retries. Proceeding with 'Best Effort'.")
                if not isinstance(result, BaseModel):
                    # SYNTHESIZE FALLBACK ARTIFACT
                    import indexing.schema as schema
                    result = schema.IndexArtifact(
                        overview="Processing failed due to unrecoverable error.",
                        files={}, subdirectories={}
                    )
                
                result.verification_state = schema.VerificationState(
                    verified=False, confidence=0.0, issues=current_issues, quality="failed",
                    is_empty_bypass=False
                )
                return result
            
            # NOTE: time.sleep blocks the ThreadPoolExecutor. 
            # We explicitly acknowledge this is an accepted limitation of the synchronous thread-based retry loop.
            # In local-LLM setups, ensure `max_workers` is set low (e.g., 2-4) to avoid complete thread starvation.
            time.sleep(2 ** attempt) 
```

---

### P1. The Merger Hallucination Blind Spot & Missing Retries

**Problem**: The LLM in the merge step could introduce hallucinated claims. If verification only happens on chunks, the final merged artifact is never verified. Furthermore, if it does fail verification, it currently falls back to "best effort" immediately without utilizing a retry loop.
**Solution**: Verify the `merged_doc` using the verified chunk documents. Crucially, **apply the same retry loop** used for chunks to the merger, so it can self-correct hallucinations.

```python
# llm_indexer.py — generate_index_for_work_unit() (Caller Context)
def generate_index_for_work_unit(self, work_unit, epoch, ...):
    # ... chunk resolution logic ...
    resolved_chunks = []
    for future in as_completed(future_to_chunk_id):
        # ... collect chunks ...
        pass
    
    # CRITICAL: Replace old direct merge call with the retry wrapper
    merged_doc = self._merge_with_retries(resolved_chunks, work_unit, verifier)
    return merged_doc

# llm_indexer.py — inside the merger logic
from pydantic import BaseModel

def _merge_with_retries(self, chunk_docs, work_unit, verifier):
    max_attempts = 3
    current_issues = []
    previous_artifact = ""

    for attempt in range(max_attempts):
        try:
            error_prompt = ""
            if current_issues:
                # Provide hallucination feedback to the merger
                error_msg = f"Merger verification failed.\nRejected Output:\n{previous_artifact}\nIssues:\n{current_issues}"
                error_prompt = error_msg # Feed into merge prompt
            
            merged_doc = self._config.summary_merger.merge(
                chunk_docs, str(work_unit.output_path), error_prompt=error_prompt
            )
            
            # CRITICAL: Verify the merged document against the chunk summaries to catch merger hallucinations
            if verifier:
                from indexing import rendering
                # Safely cap the context window to prevent local LLM blowout
                chunk_context = ""
                for doc in chunk_docs:
                    doc_md = rendering.to_markdown(doc)
                    if len(chunk_context) + len(doc_md) > 24000:
                        chunk_context += f"\n\n...[Truncated due to context limits]..."
                        break
                    chunk_context += f"\n\n{doc_md}"

                verdict = verifier.verify(merged_doc.model_dump_json(), chunk_context, is_merger_mode=True)
                if not verdict.passed:
                    raise VerificationFailedError("Merger failed", result=merged_doc, issues=verdict.issues)
            
            return merged_doc
            
        except Exception as ve:
            if isinstance(ve, VerificationFailedError):
                current_issues = ve.issues
                result = getattr(ve, "result", None)
                previous_artifact = result.model_dump_json() if isinstance(result, BaseModel) else ""
            else:
                logging.warning(f"Transient infrastructure error in Merger: {ve}")
                result = None
            
            if attempt == max_attempts - 1:
                # The merger failed completely. Fall back to best effort.
                if not isinstance(result, BaseModel):
                    import indexing.schema as schema
                    result = schema.IndexArtifact(
                        overview="Merge failed due to unrecoverable error.",
                        files={}, subdirectories={}
                    )
                    
                result.verification_state = schema.VerificationState(
                    verified=False, confidence=0.0, issues=current_issues, quality="failed"
                )
                return result
```

---

### O2. Tenacity Retry Burns LLM Credits & Drops Network Resilience

**File**: `summary_merger.py`  
**Problem**: Removing `@tenacity.retry` from the orchestrator unprotected `SummaryMerger.merge()` from transient network errors.
**Solution**: Add a stateless `@tenacity.retry` specifically around the `self._config.summary_merger.merge()` call restricted to Network Errors.

```python
# summary_merger.py
import tenacity
import requests
import openai
import httpx # Catch Ollama/local LLM errors

class SummaryMerger:
    # ...
    
    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((
            requests.exceptions.RequestException, 
            openai.APIError,
            httpx.RequestError 
        )),
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def merge(self, docs: list[any], directory_path: str, error_prompt: str = "") -> any:
        # ... logic ...
```

---

### O3 & O4. Progress Tracking String Mismatch & Massive O(N^2) I/O Bottleneck

**File**: `orchestrator.py`  
**Problem**: Modifying a monolithic JSON file via `os.replace` on every chunk is $O(N^2)$ IO, which thrashes disk and locks, mimicking the issue found in the verification cache.
**Solution**: Align success strings and use an append-only `.jsonl` file.

```python
# orchestrator.py — inside _SimpleProgressManager
import os
import json
import threading

_WU_STATUS_DONE = "COMPLETED"

class _SimpleProgressManager:
    def __init__(self, progress_file_path: str):
        self._progress_file_path = progress_file_path.replace('.json', '.jsonl')
        self._lock = threading.Lock()
        self._compact_jsonl()
        
    def _compact_jsonl(self) -> None:
        if not os.path.exists(self._progress_file_path): return
        progress = self.get_progress()
        # Rewrite compacted
        with open(self._progress_file_path, "w", encoding="utf-8") as f:
            for path, status in progress.items():
                f.write(json.dumps({"path": path, "status": status}) + "\n")
                
    def mark_work_unit_completed(self, output_path: str) -> None:
        with self._lock:
            # Atomic append, no full-file rewrite locking
            with open(self._progress_file_path, "a", encoding="utf-8") as f:
                json.dump({"path": output_path, "status": _WU_STATUS_DONE}, f)
                f.write("\n")
                
    def get_progress(self) -> dict:
        progress = {}
        with self._lock: # Acquire lock to avoid reading partially flushed lines
            if os.path.exists(self._progress_file_path):
                with open(self._progress_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            data = json.loads(line)
                            progress[data["path"]] = data["status"]
                        except json.JSONDecodeError:
                            pass # Safely ignore incomplete terminal lines
        return progress
```

---

### Q1. Unbound Variable in Error Prompt Generator

**File**: `error_prompt_generator.py:44`  
**Solution**: Initialize `is_schema_failure = False` and `is_syntactic_failure = False` before the `if issues:` check.

---

## 🟡 HIGH PRIORITY — Fix This Sprint

### V3. Cache File Concurrency Bottleneck & Crash Safety

**File**: `verification.py`  
**Problem**: Migration logic unlinks the legacy JSON file after writing JSONL. A crash in between causes duplicate migrations.
**Solution**: Use an append-only JSONL format and ensure migration is crash-safe.

```python
# verification.py
import tempfile
import os

class VerificationCache:
    # ...
    def _load_cache(self) -> dict[str, any]:
        cache = {}
        legacy_json_file = self.cache_file.with_suffix('.json')
        
        # 1. Handle Migration from Legacy .json
        # CRITICAL: Only migrate if the .jsonl does NOT exist yet
        if legacy_json_file.exists():
            if not self.cache_file.exists():
                try:
                    with open(legacy_json_file, "r", encoding="utf-8") as f:
                        legacy_data = json.load(f)
                    
                    # Write to temp file and atomic rename to prevent corruption on crash
                    dir_name = os.path.dirname(self.cache_file)
                    fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        for hash_key, verdict in legacy_data.items():
                            cache[hash_key] = verdict
                            f.write(json.dumps({
                                "hash": hash_key, "model_name": self.model_name, "verdict": verdict
                            }) + "\n")
                    
                    os.replace(temp_path, self.cache_file)
                    legacy_json_file.unlink() # Safe unlink
                except Exception as e:
                    logging.warning(f"Failed to migrate legacy cache: {e}.")
            else:
                # Dangling file from a previous crash
                legacy_json_file.unlink(missing_ok=True)
                
        # 2. Compact JSONL to prevent O(E * N) memory leak over epochs
        if self.cache_file.exists():
            self._compact_jsonl()

    def _compact_jsonl(self) -> None:
        data = {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        rec = json.loads(line)
                        data[rec["hash"]] = rec
                    except json.JSONDecodeError: pass
            
            with open(self.cache_file, "w", encoding="utf-8") as f:
                for rec in data.values():
                    f.write(json.dumps(rec) + "\n")
        except Exception as e:
            logging.warning(f"Cache compaction failed: {e}")

    def set_verdict(self, hash_key: str, verdict: any) -> None:
        import fcntl
        import json
        
        # Thread-safe atomic append for the JSONL cache
        with open(self.cache_file, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                record = {"hash": hash_key, "model_name": self.model_name, "verdict": verdict}
                f.write(json.dumps(record) + "\n")
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
```

### V1 & H1 & H2. Auto-Pass Penalties & RootMap Aggregation Updates

**Problem**: The `RootMap` health score must explicitly filter out directories bypassed due to being empty, otherwise global scores will tank.
**Solution**: Add `is_empty_bypass` and update `RootMap` metric logic.

```python
# llm_indexer.py - Empty directory bypass logic inside `generate_index_for_work_unit`
def generate_index_for_work_unit(self, work_unit, ...):
    # CRITICAL: Detect empty directories before LLM is invoked
    if not work_unit.files and not work_unit.subdirectories:
        logging.info(f"Directory {work_unit.output_path} is completely empty. Bypassing LLM.")
        empty_state = schema.VerificationState(
            verified=True, confidence=1.0, issues=[], quality="verified", is_empty_bypass=True
        )
        empty_artifact = schema.IndexArtifact(
            overview="Empty directory", files={}, subdirectories={}, 
            verification_state=empty_state
        )
        return empty_artifact

# schema.py (or verification_types.py)
class VerificationState(_BaseModel):
    # ... existing fields
    is_empty_bypass: bool = _field(default=False)

class VerificationVerdict(_BaseModel):
    auto_pass_reason: Optional[str] = _field(default=None)
    is_empty_bypass: bool = _field(default=False)

# root_map.py - Filtering logic
class RootMapGenerator:
    def _calculate_health_score(self, index_metadata: dict) -> float:
        valid_items = [
            item for item in index_metadata.values()
            if not item.get("verification_state", {}).get("is_empty_bypass", False)
        ]
        if not valid_items:
            return 1.0 
        
        total_confidence = sum(item.get("verification_state", {}).get("confidence", 0.0) for item in valid_items)
        return total_confidence / len(valid_items)
```

### V2. Verifier Too Pedantic for Summarization
Update method signature to `def verify(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> VerificationVerdict`. 
Inject the `MERGER_MODE` instructions by **prepending them to the `system_prompt`** inside `verifier.verify()`.

```python
# verifier.py
def verify(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> VerificationVerdict:
    system_prompt = self._config.verifier_system_prompt
    
    if is_merger_mode:
        merger_injection = (
            "\n# MERGER MODE ENABLED\n"
            "The source context provided is a collection of summarized chunks, NOT raw code.\n"
            "You must evaluate if the proposed artifact is a faithful, concise aggregation of these summaries.\n"
            "Do NOT reject claims just because exact syntactic evidence (like raw imports) is missing.\n"
        )
        system_prompt = merger_injection + system_prompt
        
    # ... proceed with LLM call using system_prompt ...
```

---

## 🟢 MEDIUM & LOW PRIORITY

### H3. Root Map Summary LLM Injection & Local LLM Safeguards

**Problem**: `RootMap` originally lacked the necessary dependency injection for an LLM Prompter and didn't guard against local LLM context window limits.
**Solution**: Inject `llm_prompter` into the constructor and strictly control the chunk size during map-reduce.

```python
# root_map.py - Constructor DI and Map-Reduce implementation
class RootMapGenerator:
    def __init__(self, config, llm_prompter=None): # <-- Inject Prompter
        self.config = config
        self.llm_prompter = llm_prompter
        # Set explicitly for Local Llama Safety (avoiding 80k+ contexts)
        self.max_context_chars = 24000 

    def generate_summary(self, directory_summaries: list[str]) -> str:
        if not self.llm_prompter:
            return "LLM Prompter not configured for RootMap. Provide a Prompter instance to enable structural summaries."
            
        def _recursive_summarize(summaries: list[str], prompt: str) -> str:
            if not summaries: return ""
            batches = []
            current_batch = ""
            for summary in summaries:
                # Force truncation on individual overly large summaries
                if len(summary) > self.max_context_chars:
                    summary = summary[:self.max_context_chars] + "\n...[TRUNCATED]"
                    
                if len(current_batch) + len(summary) > self.max_context_chars and current_batch:
                    batches.append(current_batch)
                    current_batch = summary
                else:
                    current_batch += f"\n\n{summary}"
            if current_batch: batches.append(current_batch)
            
            results = []
            for batch in batches:
                # Assuming prompt_for_indexing handles the Map/Reduce prompts appropriately
                res = self.llm_prompter.prompt_for_indexing(system_prompt=prompt, source_context=batch)
                results.append(res.overview if hasattr(res, 'overview') else str(res))
            
            if len(results) == 1:
                return results[0]
            
            reduce_prompt = "Synthesize these regional summaries into a cohesive, high-level overview of the entire codebase architecture."
            return _recursive_summarize(results, reduce_prompt)
            
        map_prompt = "Summarize the core responsibilities and domain boundaries of these directories. Omit minor details."
        return _recursive_summarize(directory_summaries, map_prompt)
```

### P2. Downstream Protection for Batch Artifact Reads

**Problem**: `read_artifacts` returns `None` gracefully, which causes `AttributeError` when callers try to read from it.
**Solution**: Ensure downstream callers like `collect_overviews` filter out `None`.

```python
# state.py or caller logic
def collect_overviews(self, paths: list[str]) -> dict:
    artifacts = self.local_state.read_artifacts(paths)
    overviews = {}
    for path, artifact in artifacts.items():
        if artifact is None:
            logging.warning(f"Skipping missing artifact for {path}")
            continue
        # artifact is guaranteed to be a valid Pydantic model or dict here
        overviews[path] = artifact.get('overview', '') if isinstance(artifact, dict) else artifact.overview
    return overviews
```

---

## Execution Order & Unit Test Plan

1. **O1/P1**: Implement explicit `VerificationFailedError`, thread-safe verification issues, Merger Verification, and Merger Retry. Use a custom mock LLM prompter (e.g., `MockLlmPrompter`) that intentionally yields predictable failures to simulate race conditions safely without sleeping (`test_orchestrator_concurrency.py`, `test_merger_verification.py`).
2. **O4/V3**: Migrate Progress Tracker and Verification Cache to append-only JSONL with atomic rename crash-safety (`test_progress_tracking.py`, `test_verification_cache.py`).
3. **O2**: Add tenacity strictly for network bounds on merger (`test_merger_retry.py`).
4. **V1/H1/H2**: Expose `is_empty_bypass` and update `RootMap` calculation (`test_verification_auto_pass.py`).
5. **H3**: Inject `llm_prompter` into `RootMap` and implement Map-Reduce with local LLM character limits and explicit prompts (`test_root_map_summary.py`).
6. **P2**: Implement `None`-safe batch artifact reads.
7. **Q1**: Unbound variable fix (`test_error_prompt_generator.py`).
8. **V2**: 3-tier verifier prompt with `is_merger_mode` support.
