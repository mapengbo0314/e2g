"""Verification subsystem for the AI Codebase Indexer.

This module implements the two-stage verification pipeline:
1. Syntactic Validation (Pydantic parsing)
2. Semantic Verification (LLM factual grounding check)

It also includes aggressive caching via .verification_cache.json to avoid
re-verifying unmodified outputs.
"""

# Standard library and internal project imports for artifact verification.
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Protocol, Optional

# Optional Pydantic import for schema-driven validation.
try:
    import pydantic
except ImportError:
    pydantic = None

from indexing import schema
from indexing import section_registry
from indexing import verification_types


class LlmPrompterProtocol(Protocol):
    """Protocol for LLM prompting needed by verification."""
    def verify_artifact(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> verification_types.VerificationVerdict: ...


class VerificationCache:
    """Aggressive caching mechanism to bypass re-verification for unmodified chunks."""

    def __init__(self, cache_file: Path) -> None:
        if cache_file.suffix == '.json':
            cache_file = cache_file.with_suffix('.jsonl')
        self.cache_file = cache_file
        import threading
        self._lock = threading.Lock()
        self.cache: dict[str, dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        import fcntl
        import tempfile
        import os
        cache = {}
        
        # --- Handle Legacy .json Migration (Review Finding #6) ---
        legacy_json_file = self.cache_file.with_suffix('.json')
        if legacy_json_file.exists():
            if not self.cache_file.exists():
                # Migrate: legacy exists, JSONL does not yet
                try:
                    with open(legacy_json_file, "r", encoding="utf-8") as f:
                        legacy_data = json.load(f)
                    
                    # Write to temp file and atomic rename to prevent corruption on crash
                    dir_name = str(self.cache_file.parent)
                    fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        for hash_key, verdict in legacy_data.items():
                            cache[hash_key] = verdict
                            f.write(json.dumps({"key": hash_key, "verdict": verdict}) + "\n")
                    
                    os.replace(temp_path, str(self.cache_file))
                    legacy_json_file.unlink()  # Safe unlink after atomic replace
                    logging.info("Migrated legacy verification cache to JSONL format.")
                    return cache
                except Exception as e:
                    logging.warning(f"Failed to migrate legacy cache: {e}. Starting fresh.")
                    return {}
            else:
                # Orphaned .json from a previously interrupted migration.
                # The .jsonl already exists, so the .json is stale — clean it up.
                logging.info("Cleaning up orphaned legacy verification cache file.")
                legacy_json_file.unlink(missing_ok=True)
        
        if not self.cache_file.exists():
            return cache
        
        # --- Load and Compact JSONL (Review Finding #5) ---
        # Read all entries, deduplicating by key (last-write-wins)
        try:
            with self._lock:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    try:
                        fcntl.flock(f, fcntl.LOCK_SH)
                        for line in f:
                            if not line.strip(): continue
                            try:
                                data = json.loads(line)
                                cache[data['key']] = data['verdict']
                            except Exception:
                                pass
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            
            # Compact: rewrite the JSONL with deduplicated entries to prevent
            # O(E * N) unbounded growth across multi-epoch runs.
            if cache:
                self._compact_cache(cache)
            
            return cache
        except Exception:
            logging.warning("Verification cache is corrupted. Starting fresh.")
            return {}
    
    def _compact_cache(self, cache: dict[str, dict[str, Any]]) -> None:
        """Rewrites the JSONL cache with deduplicated entries.
        
        Uses atomic tempfile rename to ensure crash safety and fcntl.LOCK_EX
        to synchronize with concurrent processes.
        """
        import tempfile
        import os
        import fcntl
        
        dir_name = str(self.cache_file.parent)
        try:
            fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                # Acquire exclusive lock on the ACTUAL cache file during compaction
                # to prevent other processes from appending while we're rewriting.
                if self.cache_file.exists():
                    with open(self.cache_file, "a") as lock_file:
                        fcntl.flock(lock_file, fcntl.LOCK_EX)
                        for key, verdict in cache.items():
                            f.write(json.dumps({"key": key, "verdict": verdict}) + "\n")
                        os.replace(temp_path, str(self.cache_file))
                        # Lock is released when lock_file is closed.
                else:
                    for key, verdict in cache.items():
                        f.write(json.dumps({"key": key, "verdict": verdict}) + "\n")
                    os.replace(temp_path, str(self.cache_file))
        except Exception as e:
            logging.warning(f"Cache compaction failed: {e}")
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _compute_hash(self, artifact_json: str, source_context: str) -> str:
        """Computes a stable hash of the input and context."""
        # Use SHA-256 for high collision resistance in the verification cache.
        hasher = hashlib.sha256()
        hasher.update(artifact_json.encode("utf-8"))
        hasher.update(source_context.encode("utf-8"))
        return hasher.hexdigest()

    def get_cached_verdict(self, artifact_json: str, source_context: str) -> verification_types.VerificationVerdict | None:
        key = self._compute_hash(artifact_json, source_context)
        if key in self.cache:
            logging.info("Verification cache hit.")
            cached_data = self.cache[key]
            # Reconstruct verdict
            if pydantic is not None:
                return verification_types.VerificationVerdict.model_validate(cached_data)
            else:
                return verification_types.VerificationVerdict(**cached_data)
        return None

    def store_verdict(self, artifact_json: str, source_context: str, verdict: verification_types.VerificationVerdict) -> None:
        import fcntl
        key = self._compute_hash(artifact_json, source_context)
        dumped = verdict.model_dump() if pydantic is not None else verdict.model_dump()
        with self._lock:
            self.cache[key] = dumped
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'a', encoding='utf-8') as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(json.dumps({"key": key, "verdict": dumped}) + "\n")
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)


class ArtifactVerifier:
    """Coordinates the two-stage verification pipeline."""

    def __init__(self, llm_prompter: LlmPrompterProtocol, cache_dir: Path) -> None:
        self.llm_prompter = llm_prompter
        self.cache = VerificationCache(cache_dir / ".verification_cache.json")

    def _stage1_syntactic_validation(self, artifact_json: str) -> verification_types.VerificationVerdict | schema.IndexDocument:
        """Runs Stage 1: Deterministic Pydantic validation.
        
        Returns the parsed IndexDocument on success, or a failing VerificationVerdict.
        """
        if pydantic is None:
            # Fallback if Pydantic isn't installed in the local environment.
            try:
                data = json.loads(artifact_json)
                doc = schema.IndexDocument(**data)
                logging.info("[Verifier] Stage 1 PASSED (no-pydantic fallback).")
                return doc
            except Exception as e:
                logging.warning("[Verifier] Stage 1 FAILED (syntactic): %s", e)
                # Return a structured syntactic failure verdict.
                return verification_types.VerificationVerdict.syntactic_failure(str(e))
                
        try:
            # Attempt to parse and validate against the IndexDocument schema.
            doc = schema.IndexDocument.model_validate_json(artifact_json)
            logging.info("[Verifier] Stage 1 PASSED (Pydantic validation).")
            return doc
        except pydantic.ValidationError as e:
            # Extract and format readable schema violation errors.
            issues = []
            for err in e.errors():
                loc = ".".join(str(l) for l in err["loc"])
                issues.append(f"Schema violation at '{loc}': {err['msg']}")
            logging.warning(
                "[Verifier] Stage 1 FAILED (%d schema violations): %s",
                len(issues), "; ".join(issues[:3]),
            )
            
            # Map Pydantic errors to the domain-specific VerificationIssue type.
            detailed = [
                verification_types.VerificationIssue(
                    category=verification_types.IssueCategory.SCHEMA_VIOLATION.value,
                    severity=verification_types.IssueSeverity.CRITICAL.value,
                    description=i
                ) for i in issues
            ]
            
            # Return a failure verdict with the accumulated issues.
            return verification_types.VerificationVerdict.failure(
                issues=issues,
                detailed_issues=detailed,
                can_retry=True
            )
        except Exception as e:
            logging.warning("[Verifier] Stage 1 FAILED (unexpected): %s", e)
            return verification_types.VerificationVerdict.syntactic_failure(str(e))

    def _check_mandatory_sections(self, doc: schema.IndexDocument, source_context: str, ast_grounding: Optional[Dict[str, Any]] = None) -> Optional[verification_types.VerificationVerdict]:
        """Enforces presence of mandatory sections (blueprint, invariants) for non-trivial codebases."""
        issues = []
        
        # Heuristic: Is this a directory with source code?
        code_extensions = {".py", ".ts", ".js", ".go", ".rs", ".c", ".cpp", ".h", ".java", ".kt", ".swift", ".rb"}
        has_code = any(ext in source_context for ext in code_extensions)
        
        if not has_code:
            return None

        # Pre-extract all AST symbols and invariants to see what is TRULY mandatory.
        from indexing import ast_extractor
        import re
        all_ast_symbols = []
        all_ast_invariants = []
        
        if ast_grounding:
            for file_data in ast_grounding.values():
                all_ast_symbols.extend(file_data.get("symbols", []))
                all_ast_invariants.extend(file_data.get("invariants", []))
        else:
            files = re.split(r'--- (.*?) ---\n', source_context)
            if len(files) > 1:
                for i in range(1, len(files), 2):
                    filename = files[i]
                    content = files[i+1]
                    syms, invs = ast_extractor.extract_ast_grounding(filename, content)
                    all_ast_symbols.extend(syms)
                    all_ast_invariants.extend(invs)

        # 1. Enforce Registry-driven mandatory sections
        for spec in section_registry.SECTION_SPECS:
            if spec.verification_policy == "required_for_code":
                # Only enforce if we have deterministic evidence that the section SHOULD be populated.
                if spec.section_id == "blueprint" and not all_ast_symbols:
                    continue
                if spec.section_id == "implementation_invariants" and not all_ast_invariants:
                    continue
                if spec.section_id == "key_interfaces" and not all_ast_symbols:
                    # Usually if there are no symbols, there are no meaningful interfaces.
                    continue

                section_instance = getattr(doc, spec.section_id, None)
                if section_registry.is_section_empty(spec.section_id, section_instance):
                    issues.append(f"Mandatory section '{spec.section_id}' is empty despite evidence in source code.")

        if issues:
            logging.warning("[Verifier] Mandatory section check FAILED: %s", "; ".join(issues))
            detailed = [
                verification_types.VerificationIssue(
                    category=verification_types.IssueCategory.EMPTY_MANDATORY_SECTION.value,
                    severity=verification_types.IssueSeverity.CRITICAL.value,
                    description=i
                ) for i in issues
            ]
            return verification_types.VerificationVerdict.failure(
                issues=issues,
                detailed_issues=detailed,
                can_retry=True
            )
        
        return None

    def _check_ast_grounding(self, doc: schema.IndexDocument, source_context: str, ast_grounding: Optional[Dict[str, Any]] = None) -> Optional[verification_types.VerificationVerdict]:
        """Validates that deterministically extracted AST symbols are present in the blueprint."""
        try:
            from indexing import ast_extractor
            import re
            
            issues = []
            
            if ast_grounding:
                for filename, file_data in ast_grounding.items():
                    ast_symbols = file_data.get("symbols", [])
                    if not ast_symbols:
                        continue
                        
                    # Check if the blueprint has these symbols.
                    blueprint = getattr(doc, "blueprint", None)
                    llm_symbols = []
                    if blueprint and blueprint.symbols:
                        llm_symbols = [s.name for s in blueprint.symbols]
                        
                    for expected_sym in ast_symbols:
                        if expected_sym.name not in llm_symbols:
                            issues.append(f"AST Grounding Failure: Symbol '{expected_sym.name}' found in {filename} but missing from blueprint symbols.")
            else:
                # Fallback to manual extraction if no cache provided
                files = re.split(r'--- (.*?) ---\n', source_context)
                if len(files) > 1:
                    for i in range(1, len(files), 2):
                        filename = files[i]
                        content = files[i+1]
                        
                        ast_symbols, _ = ast_extractor.extract_ast_grounding(filename, content)
                        if not ast_symbols:
                            continue
                            
                        # Check if the blueprint has these symbols.
                        blueprint = getattr(doc, "blueprint", None)
                        llm_symbols = []
                        if blueprint and blueprint.symbols:
                            llm_symbols = [s.name for s in blueprint.symbols]
                            
                        for expected_sym in ast_symbols:
                            if expected_sym.name not in llm_symbols:
                                issues.append(f"AST Grounding Failure: Symbol '{expected_sym.name}' found in {filename} but missing from blueprint symbols.")
                            
            if issues:
                logging.warning("[Verifier] AST Grounding check FAILED: %s", "; ".join(issues))
                detailed = [
                    verification_types.VerificationIssue(
                        category=verification_types.IssueCategory.MISSING_GROUNDED_SYMBOL.value,
                        severity=verification_types.IssueSeverity.CRITICAL.value,
                        description=i
                    ) for i in issues
                ]
                return verification_types.VerificationVerdict.failure(
                    issues=issues,
                    detailed_issues=detailed,
                    can_retry=True
                )
        except Exception as e:
            logging.warning("[Verifier] AST Grounding check crashed (ignoring): %s", e)
            
        return None

    def _stage2_semantic_verification(
        self, 
        artifact_json: str, 
        source_context: str,
        is_merger_mode: bool = False
    ) -> verification_types.VerificationVerdict:
        """Runs Stage 2: LLM factual grounding check."""
        # Check cache first to avoid expensive and redundant LLM calls.
        cached = self.cache.get_cached_verdict(artifact_json, source_context)
        if cached is not None:
            logging.info(
                "[Verifier] Stage 2 cache HIT (passed=%s, confidence=%.2f).",
                cached.passed, cached.confidence,
            )
            return cached

        logging.info(
            "[Verifier] Stage 2 cache MISS, running LLM semantic verification "
            "(source_context=%d bytes, artifact=%d bytes).",
            len(source_context), len(artifact_json),
        )
        # Delegate the actual semantic checking to the LLM.
        verdict = self.llm_prompter.verify_artifact(artifact_json, source_context, is_merger_mode=is_merger_mode)
        logging.info(
            "[Verifier] Stage 2 LLM verdict: passed=%s, confidence=%.2f, "
            "issues=%d, decision=%s.",
            verdict.passed, verdict.confidence,
            len(verdict.issues), verdict.decision,
        )
        if verdict.issues:
            for i, issue in enumerate(verdict.issues[:5]):
                logging.info("[Verifier]   issue[%d]: %s", i, issue)
        
        # Cache the result to prevent repeated verification of the same artifact/context pair.
        self.cache.store_verdict(artifact_json, source_context, verdict)
        return verdict

    def verify(
        self, 
        artifact_json: str, 
        source_context: str,
        skip_semantic: bool = False,
        is_merger_mode: bool = False,
        ast_grounding: Optional[Dict[str, Any]] = None
    ) -> verification_types.VerificationVerdict:
        """Executes the full verification pipeline.
        
        Args:
            artifact_json: The generated JSON artifact.
            source_context: The raw source code or context used to generate the artifact.
            skip_semantic: If True, only runs syntactic validation (useful for partial generation).
        """
        logging.info(
            "[Verifier] Starting verification pipeline "
            "(artifact=%d bytes, context=%d bytes, skip_semantic=%s).",
            len(artifact_json), len(source_context), skip_semantic,
        )

        # Stage 1: Syntactic (Fast, deterministic check).
        stage1_result = self._stage1_syntactic_validation(artifact_json)
        if isinstance(stage1_result, verification_types.VerificationVerdict):
            # Stage 1 failed, abort and return the failure immediately.
            logging.warning("[Verifier] Pipeline aborted at Stage 1 (syntactic).")
            return stage1_result
            
        mandatory_result = self._check_mandatory_sections(stage1_result, source_context, ast_grounding=ast_grounding)
        if mandatory_result:
            logging.warning("[Verifier] Pipeline aborted at Stage 1.5 (mandatory sections).")
            return mandatory_result
            
        # Stage 1.6: AST Grounding Enforcement (NEW)
        # Prevents LLM from silently dropping deterministic structural facts.
        ast_result = self._check_ast_grounding(stage1_result, source_context, ast_grounding=ast_grounding)
        if ast_result:
            logging.warning("[Verifier] Pipeline aborted at Stage 1.6 (AST grounding).")
            return ast_result
            
        if skip_semantic:
            # Return an explicit bypass if Stage 1 passes and semantic verification is disabled.
            logging.info("[Verifier] Pipeline complete (semantic skipped).")
            return verification_types.VerificationVerdict.infrastructure_bypass(
                confidence=0.5,
                reason="Semantic verification skipped by caller.",
            )

        # Stage 2: Semantic (Slow, non-deterministic grounding check).
        # We pass the original JSON for verification against the raw source context.
        return self._stage2_semantic_verification(artifact_json, source_context, is_merger_mode)
