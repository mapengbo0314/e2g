"""Tests for the verification subsystem."""

import json
from pathlib import Path
import tempfile
import unittest

from indexing import schema
from indexing import verification
from indexing import verification_types


class FakeLlmPrompter:
    def __init__(self, verdict: verification_types.VerificationVerdict):
        self.verdict = verdict
        self.calls = 0

    def verify_artifact(self, artifact_json: str, source_context: str, is_merger_mode: bool = False) -> verification_types.VerificationVerdict:
        self.calls += 1
        return self.verdict


class VerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_syntactic_validation_success(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        valid_json = json.dumps({
            "overview": {"content": "A good directory"},
            "key_dependencies": None,
            "key_individual_components": None
        })
        
        # skip_semantic=True to just test syntactic
        verdict = verifier.verify(valid_json, "some context", skip_semantic=True)
        self.assertTrue(verdict.passed)
        self.assertEqual(prompter.calls, 0)

    def test_syntactic_validation_failure(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        invalid_json = "{ bad json"
        
        verdict = verifier.verify(invalid_json, "some context")
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.decision, "retry")
        self.assertEqual(prompter.calls, 0)

    def test_schema_validation_failure(self):
        prompter = FakeLlmPrompter(verification_types.VerificationVerdict.success())
        verifier = verification.ArtifactVerifier(prompter, self.cache_dir)
        
        # Valid JSON but misses required schema fields or wrong types
        schema_invalid_json = json.dumps({
            "overview": "Should be an object, not a string"
        })
        
        verdict = verifier.verify(schema_invalid_json, "some context")
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.decision, "retry")
        self.assertTrue(len(verdict.issues) > 0)
        self.assertEqual(prompter.calls, 0)

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
        
        # Second call should hit cache
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
        self.assertEqual(verdict.issues, ["Hallucination!"])
        self.assertEqual(prompter.calls, 1)


if __name__ == '__main__':
    unittest.main()
