"""Tests for Merger verification and retry logic in LlmIndexer."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from indexing import llm_indexer
from indexing import schema
from indexing import work_unit as work_unit_lib

class TestMergerVerification(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.indexer = llm_indexer.LlmIndexer(self.mock_config)
        self.work_unit = work_unit_lib.WorkUnit(
            output_path=Path("test/dir"),
            files_to_index=set()
        )
        self.chunk_docs = [
            schema.IndexDocument(overview=schema.Overview(content="c1")),
            schema.IndexDocument(overview=schema.Overview(content="c2"))
        ]

    def test_merge_happy_path(self):
        merged = schema.IndexDocument(overview=schema.Overview(content="merged"))
        self.mock_config.summary_merger.merge.return_value = merged
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(passed=True, issues=[], is_empty_bypass=False)
        
        result = self.indexer._merge_with_retries(self.chunk_docs, self.work_unit, mock_verifier)
        
        self.assertEqual(result.overview.content, "merged")
        self.assertTrue(result.verification_state.verified)
        self.assertEqual(result.verification_state.confidence, 1.0)
        self.mock_config.summary_merger.merge.assert_called_once()

    def test_merge_retry_success(self):
        merged_v1 = schema.IndexDocument(overview=schema.Overview(content="merged v1"))
        merged_v2 = schema.IndexDocument(overview=schema.Overview(content="merged v2"))
        
        self.mock_config.summary_merger.merge.side_effect = [merged_v1, merged_v2]
        
        mock_verifier = MagicMock()
        mock_verifier.verify.side_effect = [
            MagicMock(passed=False, issues=["typo"]),
            MagicMock(passed=True, issues=[])
        ]
        
        with patch('time.sleep'): # Avoid waiting
            result = self.indexer._merge_with_retries(self.chunk_docs, self.work_unit, mock_verifier)
            
        self.assertEqual(result.overview.content, "merged v2")
        self.assertEqual(self.mock_config.summary_merger.merge.call_count, 2)
        # Check that second call included error prompt
        args, kwargs = self.mock_config.summary_merger.merge.call_args
        self.assertIn("typo", kwargs["error_prompt"])

    def test_merge_exhaust_retries(self):
        merged_fail = schema.IndexDocument(overview=schema.Overview(content="failed attempt"))
        self.mock_config.summary_merger.merge.return_value = merged_fail
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(passed=False, issues=["still broken"])
        
        with patch('time.sleep'):
            result = self.indexer._merge_with_retries(self.chunk_docs, self.work_unit, mock_verifier)
            
        self.assertFalse(result.verification_state.verified)
        self.assertEqual(result.verification_state.confidence, 0.0)
        self.assertIn("still broken", result.verification_state.issues)
        self.assertEqual(self.mock_config.summary_merger.merge.call_count, 3)

    def test_context_limit_skips_verification(self):
        # Create very large chunk docs to exceed 24000
        large_content = "x" * 15000
        large_docs = [
            schema.IndexDocument(overview=schema.Overview(content=large_content)),
            schema.IndexDocument(overview=schema.Overview(content=large_content))
        ]
        
        merged = schema.IndexDocument(overview=schema.Overview(content="merged large"))
        self.mock_config.summary_merger.merge.return_value = merged
        
        mock_verifier = MagicMock()
        
        result = self.indexer._merge_with_retries(large_docs, self.work_unit, mock_verifier)
        
        self.assertTrue(result.verification_state.verified)
        self.assertEqual(result.verification_state.confidence, 0.5)
        self.assertIn("skipped", result.verification_state.issues[0])
        mock_verifier.verify.assert_not_called()

if __name__ == '__main__':
    unittest.main()
