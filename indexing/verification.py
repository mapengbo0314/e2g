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
from typing import Any, Protocol

# Optional Pydantic import for schema-driven validation.
try:
    import pydantic
except ImportError:
    pydantic = None

from indexing import schema
from indexing import verification_types


class LlmPrompterProtocol(Protocol):
    """Protocol for LLM prompting needed by verification."""
    def verify_artifact(self, artifact_json: str, source_context: str) -> verification_types.VerificationVerdict: ...


class VerificationCache:
    """Aggressive caching mechanism to bypass re-verification for unmodified chunks."""

    def __init__(self, cache_file: Path) -> None:
        self.cache_file = cache_file
        self.cache: dict[str, dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        if not self.cache_file.exists():
            return {}
        try:
            return json.loads(self.cache_file.read_text())
        except json.JSONDecodeError:
            # If the cache file is malformed, log a warning and return an empty state.
            logging.warning("Verification cache is corrupted. Starting fresh.")
            return {}

    def _save_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache, indent=2))

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
        key = self._compute_hash(artifact_json, source_context)
        if pydantic is not None:
            self.cache[key] = verdict.model_dump()
        else:
            # Continuation of processing logic.
            self.cache[key] = verdict.model_dump()
        self._save_cache()


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
                issues.append(f"Schema error at '{loc}': {err['msg']}")
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

    def _stage2_semantic_verification(
        self, 
        artifact_json: str, 
        # Continuation of processing logic.
        source_context: str
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
        verdict = self.llm_prompter.verify_artifact(artifact_json, source_context)
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
        skip_semantic: bool = False
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
            logging.warning("[Verifier] Pipeline aborted at Stage 1.")
            return stage1_result
            
        if skip_semantic:
            # Return success if Stage 1 passes and semantic verification is disabled.
            logging.info("[Verifier] Pipeline complete (semantic skipped).")
            return verification_types.VerificationVerdict.success()

        # Stage 2: Semantic (Slow, non-deterministic grounding check).
        # We pass the original JSON for verification against the raw source context.
        return self._stage2_semantic_verification(artifact_json, source_context)
