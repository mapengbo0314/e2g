"""Tests for chunk-level retry logic and repair prompt generation."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from indexing import llm_indexer
from indexing import schema

class TestChunkRetryLogic(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.indexer = llm_indexer.LlmIndexer(self.mock_config)
        self.dir_path = Path("test/dir")
        self.contents = {Path("f1.py"): "code"}

    def test_chunk_happy_path(self):
        doc = schema.IndexDocument(overview=schema.Overview(content="ok"))
        self.mock_config.llm_prompter.prompt_for_indexing.return_value = doc
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(passed=True, issues=[], is_empty_bypass=False)
        
        result = self.indexer._generate_index_for_chunk(
            self.dir_path, 0, "", self.contents, {}, "", False, mock_verifier
        )
        
        self.assertEqual(result.overview.content, "ok")
        self.assertTrue(result.verification_state.verified)
        self.mock_config.llm_prompter.prompt_for_indexing.assert_called_once()

    def test_chunk_retry_success(self):
        doc_v1 = schema.IndexDocument(overview=schema.Overview(content="v1"))
        doc_v2 = schema.IndexDocument(overview=schema.Overview(content="v2"))
        
        self.mock_config.llm_prompter.prompt_for_indexing.side_effect = [doc_v1, doc_v2]
        
        mock_verifier = MagicMock()
        mock_verifier.verify.side_effect = [
            MagicMock(passed=False, issues=["issue1"]),
            MagicMock(passed=True, issues=[])
        ]
        
        with patch('time.sleep'):
            result = self.indexer._generate_index_for_chunk(
                self.dir_path, 0, "", self.contents, {}, "", False, mock_verifier
            )
            
        self.assertEqual(result.overview.content, "v2")
        self.assertEqual(self.mock_config.llm_prompter.prompt_for_indexing.call_count, 2)
        
        # Verify second call's user prompt includes the issue
        args, kwargs = self.mock_config.llm_prompter.prompt_for_indexing.call_args
        self.assertIn("issue1", kwargs["initial_user_prompt"])

    def test_chunk_exhaust_retries(self):
        doc_fail = schema.IndexDocument(overview=schema.Overview(content="failed"))
        self.mock_config.llm_prompter.prompt_for_indexing.return_value = doc_fail
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(passed=False, issues=["still failing"])
        
        with patch('time.sleep'):
            result = self.indexer._generate_index_for_chunk(
                self.dir_path, 0, "", self.contents, {}, "", False, mock_verifier
            )
            
        self.assertFalse(result.verification_state.verified)
        self.assertEqual(result.verification_state.confidence, 0.0)
        self.assertEqual(self.mock_config.llm_prompter.prompt_for_indexing.call_count, 3)

    def test_infrastructure_error_bubbles_up(self):
        self.mock_config.llm_prompter.prompt_for_indexing.side_effect = RuntimeError("Quota exceeded")
        
        with self.assertRaises(RuntimeError):
            self.indexer._generate_index_for_chunk(
                self.dir_path, 0, "", self.contents, {}, "", False, None
            )

if __name__ == '__main__':
    unittest.main()
