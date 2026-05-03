"""Tests for the IndexerErrorPromptGenerator."""

import unittest
from indexing.error_prompt_generator import IndexerErrorPromptGenerator

class TestErrorPromptGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IndexerErrorPromptGenerator()

    def test_generate_error_prompt_with_schema_issues(self):
        error_msg = "Timeout occurred"
        issues = ["Schema violation: missing overview", "Syntactic issue: invalid JSON"]
        prompt = self.generator.generate_error_prompt(error_msg, issues)
        
        self.assertIn("=== SCHEMA / SYNTACTIC ISSUES ===", prompt)
        self.assertIn("1. Schema violation: missing overview", prompt)
        self.assertIn("2. Syntactic issue: invalid JSON", prompt)
        self.assertIn("Please fix the structural issues first.", prompt)
        self.assertIn("Timeout occurred", prompt)

    def test_generate_error_prompt_with_semantic_issues(self):
        error_msg = "Verification failed"
        issues = ["Hallucination detected in file A", "Missing dependency B"]
        prompt = self.generator.generate_error_prompt(error_msg, issues)
        
        self.assertIn("=== VERIFICATION / SEMANTIC ISSUES ===", prompt)
        self.assertIn("1. Hallucination detected in file A", prompt)
        self.assertIn("Please try again. Focus on fixing the reported issues.", prompt)

    def test_generate_error_prompt_with_structured_issues(self):
        error_msg = "Issues found"
        issues = [
            {"category": "Hallucination", "message": "Claim about X is false"},
            {"category": "Missing", "message": "File Y is not mentioned"}
        ]
        prompt = self.generator.generate_error_prompt(error_msg, issues)
        
        self.assertIn("1. [Hallucination] Claim about X is false", prompt)
        self.assertIn("2. [Missing] File Y is not mentioned", prompt)

    def test_generate_error_prompt_no_issues(self):
        error_msg = "Infrastructure failure"
        prompt = self.generator.generate_error_prompt(error_msg, None)
        
        self.assertIn("=== CONTEXTUAL ERROR ===", prompt)
        self.assertIn("Infrastructure failure", prompt)
        self.assertNotIn("=== SCHEMA / SYNTACTIC ISSUES ===", prompt)
        self.assertNotIn("=== VERIFICATION / SEMANTIC ISSUES ===", prompt)

if __name__ == '__main__':
    unittest.main()
