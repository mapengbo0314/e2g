"""Structured types for the artifact verification subsystem.

Defines verdicts, issue categories, severity levels, and publication
decisions used by the verifier. Kept separate from the main index
artifact schema so verifier contracts remain stable and explicit.
"""

# Standard library and type hinting imports.
from __future__ import annotations
import enum
from typing import List, Optional

# Conditional import for Pydantic for schema-backed verification.
try:
    import pydantic
except ImportError:
    pydantic = None


if pydantic is None:  # pragma: no cover
    class _BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self):
            return dict(self.__dict__)

    def _field(default=None, default_factory=None, description: str = ""):
        # Minimal field definition to mimic Pydantic behavior.
        if default_factory is not None:
            return default_factory()
        return default
else:
    _BaseModel = pydantic.BaseModel
    _field = pydantic.Field


class IssueSeverity(str, enum.Enum):
    """Severity level of a verification issue."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, enum.Enum):
    """Category of a verification issue."""
    HALLUCINATED_DEPENDENCY = "hallucinated_dependency"
    HALLUCINATED_COMPONENT = "hallucinated_component"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    MERGE_DISTORTION = "merge_distortion"
    STALE_REFERENCE = "stale_reference"
    OMITTED_COMPONENT = "omitted_component"
    MALFORMED_JSON = "malformed_json"
    SCHEMA_VIOLATION = "schema_violation"
    EMPTY_MANDATORY_SECTION = "empty_mandatory_section"
    MISSING_GROUNDED_SYMBOL = "missing_grounded_symbol"


class PublicationDecision(str, enum.Enum):
    """Outcome decision for a verified artifact."""
    PUBLISH = "publish"
    RETRY = "retry"
    FAIL = "fail"


class VerificationIssue(_BaseModel):
    """A single issue found during verification."""

    category: str = _field(
        description="The category of the issue (from IssueCategory)."
    )
    severity: str = _field(
        description="The severity of the issue (from IssueSeverity)."
    )
    description: str = _field(
        description="Human-readable description of the issue."
    )
    section: Optional[str] = _field(
        default=None,
        description="The schema section where the issue was found (e.g., 'overview', 'key_dependencies')."
    )


class VerificationVerdict(_BaseModel):
    """The structured verdict returned by the verification subsystem.

    This is the canonical contract between the verifier, orchestrator,
    and prompt generator. The orchestrator uses `passed` to decide
    whether to publish or retry. The prompt generator injects `issues`
    back into the LLM context for targeted retries.
    """

    passed: bool = _field(
        description="Whether the artifact passed verification."
    )
    confidence: float = _field(
        default=1.0,
        description="Confidence score from 0.0 to 1.0. Values below 0.7 trigger warnings."
    )
    issues: List[str] = _field(
        default_factory=list,
        description=(
            "List of human-readable issue descriptions. These are injected "
            "directly into retry prompts so the LLM knows exactly why it failed."
        ),
    )
    detailed_issues: List[VerificationIssue] = _field(
        default_factory=list,
        description="Structured issue objects for programmatic processing.",
    )
    decision: str = _field(
        default="publish",
        description="The publication decision: 'publish', 'retry', or 'fail'.",
    )
    verification_model: Optional[str] = _field(
        default=None,
        description="The model used for verification.",
    )
    auto_pass_reason: Optional[str] = _field(
        default=None,
        description="Reason the artifact was auto-passed without full verification (e.g., 'empty_directory').",
    )
    is_empty_bypass: bool = _field(
        default=False,
        description="True if this verdict bypassed LLM verification because the directory was empty.",
    )
    is_infrastructure_bypass: bool = _field(
        default=False,
        description="True if verification was bypassed due to verifier infrastructure limits or failures.",
    )

    @classmethod
    def success(cls, confidence: float = 1.0) -> "VerificationVerdict":
        """Factory for a passing verdict."""
        # A successful verdict implies no blocking issues and a high confidence score.
        return cls(
            passed=True,
            confidence=confidence,
            issues=[],
            detailed_issues=[],
            decision=PublicationDecision.PUBLISH.value,
        )

    @classmethod
    def infrastructure_bypass(
        cls,
        confidence: float = 0.3,
        reason: str = "",
    ) -> "VerificationVerdict":
        """Factory for an explicit low-confidence infrastructure bypass."""
        return cls(
            passed=True,
            confidence=confidence,
            issues=[reason] if reason else [],
            detailed_issues=[],
            decision="infrastructure_bypass",
            auto_pass_reason=reason or "infrastructure_bypass",
            is_infrastructure_bypass=True,
        )

    @classmethod
    def failure(
        cls,
        issues: List[str],
        detailed_issues: Optional[List[VerificationIssue]] = None,
        can_retry: bool = True,
    ) -> "VerificationVerdict":
        """Factory for a failing verdict."""
        return cls(
            passed=False,
            confidence=0.0,
            issues=issues,
            detailed_issues=detailed_issues or [],
            decision=PublicationDecision.RETRY.value if can_retry else PublicationDecision.FAIL.value,
        )

    @classmethod
    def syntactic_failure(cls, error_message: str) -> "VerificationVerdict":
        """Factory for a JSON/schema parsing failure."""
        return cls(
            passed=False,
            confidence=0.0,
            issues=[f"Syntactic validation failed: {error_message}"],
            detailed_issues=[
                VerificationIssue(
                    category=IssueCategory.MALFORMED_JSON.value,
                    severity=IssueSeverity.CRITICAL.value,
                    description=error_message,
                )
            ],
            decision=PublicationDecision.RETRY.value,
        )
