"""Tests for the verification subsystem."""

import json
from pathlib import Path
import tempfile
import unittest
from typing import List, Optional

from indexing import schema
from indexing import verification
from indexing import verification_types


class FakeLlmPrompter:
    def __init__(self, verdict: verification_types.VerificationVerdict):
        self.verdict = verdict
        self.calls = 0

    def verify_artifact(self, artifact_json: str, source_context: str, directory_files: Optional[List[str]] = None, is_merger_mode: bool = False) -> verification_types.VerificationVerdict:
        self.calls += 1
        return self.verdict


class VerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stage1_syntactic_validation_success(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        valid_json = json.dumps({
            "overview": {"content": "A good directory"}
        })
        
        # Stage 1 returns the parsed doc if valid
        doc = verifier._stage1_syntactic_validation(valid_json)
        self.assertIsInstance(doc, schema.IndexDocument)
        self.assertEqual(doc.overview.content, "A good directory")

    def test_stage1_syntactic_validation_failure(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        invalid_json = '{"overview": "not a dict"}'
        
        # Stage 1 returns a verdict if invalid
        verdict = verifier._stage1_syntactic_validation(invalid_json)
        self.assertIsInstance(verdict, verification_types.VerificationVerdict)
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.decision, verification_types.PublicationDecision.RETRY.value)

    def test_semantic_verification_success_with_caching(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        valid_json = json.dumps({
            "overview": {"content": "A good directory"}
        })
        
        # First call
        verdict1 = verifier.verify(valid_json, "some context")
        self.assertTrue(verdict1.passed)
        self.assertEqual(prompter.calls, 1)
        
        # Second call (same content) should hit cache
        verdict2 = verifier.verify(valid_json, "some context")
        self.assertTrue(verdict2.passed)
        self.assertEqual(prompter.calls, 1)

    def test_semantic_verification_failure(self):
        failing_verdict = verification_types.VerificationVerdict.failure(["Hallucination!"])
        prompter = FakeLlmPrompter(failing_verdict)
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        valid_json = json.dumps({
            "overview": {"content": "A good directory"}
        })
        
        verdict = verifier.verify(valid_json, "some context")
        self.assertFalse(verdict.passed)
        self.assertIn("Hallucination!", verdict.issues)

    def test_infrastructure_bypass(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        valid_json = json.dumps({
            "overview": {"content": "A good directory"}
        })
        
        # skip_semantic=True should trigger infrastructure_bypass
        verdict = verifier.verify(valid_json, "some context", skip_semantic=True)
        self.assertTrue(verdict.passed)
        self.assertTrue(verdict.is_infrastructure_bypass)
        self.assertEqual(prompter.calls, 0)

if __name__ == '__main__':
    unittest.main()
