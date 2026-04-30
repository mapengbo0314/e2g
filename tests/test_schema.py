"""Tests for the updated structured artifact schema and verification types.

Validates serialization, deserialization, optional metadata handling,
and markdown rendering behavior.
"""

import json
import pytest
from indexing.schema import (
    Component,
    Configurations,
    ConfigurationItem,
    DeepDive,
    GenerationMetadata,
    IndexDocument,
    KeyDependencies,
    KeyIndividualComponents,
    KeyInterfaces,
    Overview,
    TestingStrategy,
    VerificationState,
    from_json,
    to_json,
)
from indexing.rendering import sanitize_unicode, to_markdown
from indexing.verification_types import (
    IssueCategory,
    IssueSeverity,
    PublicationDecision,
    VerificationIssue,
    VerificationVerdict,
)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestIndexDocumentSerialization:
    """Tests for IndexDocument JSON round-trip."""

    def _make_minimal_doc(self) -> IndexDocument:
        return IndexDocument(
            overview=Overview(content="This directory handles auth."),
        )

    def _make_full_doc(self) -> IndexDocument:
        return IndexDocument(
            overview=Overview(content="This directory handles auth."),
            deep_dive=DeepDive(content="The auth module uses JWT tokens."),
            key_individual_components=KeyIndividualComponents(
                components=[Component(name="auth.py", description="Main auth logic.")]
            ),
            key_interfaces=KeyInterfaces(interfaces=[]),
            key_dependencies=KeyDependencies(dependencies=[]),
            configurations=Configurations(configurations=[]),
            testing_strategy=TestingStrategy(content="Unit tests with pytest."),
            generation_metadata=GenerationMetadata(
                model_name="gemini-3-flash",
                epoch=1,
                generated_at="2026-01-01T00:00:00Z",
                chunk_count=1,
                retry_count=0,
            ),
            verification_state=VerificationState(
                verified=True,
                verification_model="gemini-3-flash",
                verified_at="2026-01-01T00:01:00Z",
                confidence=0.95,
                issues=[],
            ),
        )

    def test_minimal_doc_serializes(self):
        doc = self._make_minimal_doc()
        json_str = to_json(doc)
        data = json.loads(json_str)
        assert data["overview"]["content"] == "This directory handles auth."
        # Optional fields should be None/null
        assert data.get("deep_dive") is None
        assert data.get("key_interfaces") is None

    def test_full_doc_round_trips(self):
        doc = self._make_full_doc()
        json_str = to_json(doc)
        restored = from_json(json_str)
        assert restored.overview.content == doc.overview.content
        assert restored.generation_metadata.model_name == "gemini-3-flash"
        assert restored.verification_state.verified is True
        assert restored.verification_state.confidence == 0.95

    def test_null_optional_sections_are_valid(self):
        """The LLM should be able to return null for optional sections."""
        doc = IndexDocument(
            overview=Overview(content="Minimal."),
            deep_dive=None,
            key_interfaces=None,
            key_dependencies=None,
            testing_strategy=None,
        )
        json_str = to_json(doc)
        restored = from_json(json_str)
        assert restored.deep_dive is None
        assert restored.key_interfaces is None
        assert restored.key_dependencies is None
        assert restored.testing_strategy is None

    def test_trust_metadata_defaults(self):
        """Generation and verification metadata should have safe defaults."""
        meta = GenerationMetadata()
        assert meta.epoch == 0
        assert meta.chunk_count == 1
        assert meta.retry_count == 0

        state = VerificationState()
        assert state.verified is False
        assert state.confidence == 0.0
        assert state.issues == []


class TestMarkdownRendering:
    """Tests for to_markdown rendering."""

    def test_renders_overview_only(self):
        doc = IndexDocument(
            overview=Overview(content="Hello world."),
        )
        md = to_markdown(doc)
        assert "# Overview" in md
        assert "Hello world." in md

    def test_skips_none_sections(self):
        doc = IndexDocument(
            overview=Overview(content="Auth module."),
            deep_dive=None,
            key_interfaces=None,
        )
        md = to_markdown(doc)
        assert "# Deep Dive" not in md
        assert "# Key Interfaces" not in md

    def test_skips_empty_list_sections(self):
        doc = IndexDocument(
            overview=Overview(content="Auth module."),
            key_individual_components=KeyIndividualComponents(components=[]),
        )
        md = to_markdown(doc)
        assert "# Key Individual Components" not in md

    def test_renders_full_doc(self):
        doc = IndexDocument(
            overview=Overview(content="Auth module."),
            deep_dive=DeepDive(content="JWT-based auth."),
            key_individual_components=KeyIndividualComponents(
                components=[Component(name="auth.py", description="Core auth.")]
            ),
        )
        md = to_markdown(doc)
        assert "# Overview" in md
        assert "# Deep Dive" in md
        assert "# Key Individual Components" in md
        assert "**auth.py**" in md


class TestSanitizeUnicode:
    def test_removes_control_characters(self):
        assert sanitize_unicode("hello\x00world") == "helloworld"

    def test_preserves_normal_text(self):
        assert sanitize_unicode("hello world") == "hello world"


# ---------------------------------------------------------------------------
# Verification types tests
# ---------------------------------------------------------------------------

class TestVerificationVerdict:
    def test_success_factory(self):
        v = VerificationVerdict.success(confidence=0.9)
        assert v.passed is True
        assert v.confidence == 0.9
        assert v.issues == []
        assert v.decision == "publish"

    def test_failure_factory(self):
        v = VerificationVerdict.failure(
            issues=["Claimed Redis dependency not in source."],
            can_retry=True,
        )
        assert v.passed is False
        assert v.confidence == 0.0
        assert len(v.issues) == 1
        assert v.decision == "retry"

    def test_failure_no_retry(self):
        v = VerificationVerdict.failure(
            issues=["Persistent hallucination after 3 retries."],
            can_retry=False,
        )
        assert v.decision == "fail"

    def test_syntactic_failure_factory(self):
        v = VerificationVerdict.syntactic_failure("Invalid JSON at line 42")
        assert v.passed is False
        assert len(v.detailed_issues) == 1
        assert v.detailed_issues[0].category == "malformed_json"
        assert v.detailed_issues[0].severity == "critical"

    def test_verdict_serializes(self):
        v = VerificationVerdict.failure(
            issues=["Bad dependency claim."],
            detailed_issues=[
                VerificationIssue(
                    category=IssueCategory.HALLUCINATED_DEPENDENCY.value,
                    severity=IssueSeverity.CRITICAL.value,
                    description="Claimed Redis but not in imports.",
                    section="key_dependencies",
                )
            ],
        )
        data = v.model_dump()
        assert data["passed"] is False
        assert len(data["detailed_issues"]) == 1
        assert data["detailed_issues"][0]["section"] == "key_dependencies"


class TestVerificationEnums:
    def test_issue_severity_values(self):
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.WARNING.value == "warning"

    def test_publication_decision_values(self):
        assert PublicationDecision.PUBLISH.value == "publish"
        assert PublicationDecision.RETRY.value == "retry"
        assert PublicationDecision.FAIL.value == "fail"
