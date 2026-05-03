"""Tests for root map generation and Map-Reduce summarization."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from indexing import root_map
from indexing import work_unit as work_unit_lib

class TestRootMapSummary(unittest.TestCase):
    def test_calculate_project_health(self):
        data = [
            {"confidence": 1.0, "size_bytes": 100, "is_empty_bypass": False},
            {"confidence": 0.5, "size_bytes": 100, "is_empty_bypass": False},
            {"confidence": 0.8, "size_bytes": 0, "is_empty_bypass": False}, # Effective size 1
        ]
        # (1.0*100 + 0.5*100 + 0.8*1) / (100 + 100 + 1) = 150.8 / 201 = ~0.75
        health = root_map.calculate_project_health(data)
        self.assertAlmostEqual(health, 150.8 / 201)

    def test_recursive_summarize_batching(self):
        mock_prompter = MagicMock()
        mock_prompter.prompt_for_root_map_summary.side_effect = lambda x: f"summary of {len(x.splitlines())//2 + 1} items" # Rough mock
        
        items = [f"item {i}\ncontent {i}" for i in range(25)]
        # chunk_size = 10
        # Round 1: 25 items -> 3 summaries (10, 10, 5)
        # Round 2: 3 items -> 1 summary
        
        result = root_map._recursive_summarize(items, mock_prompter, chunk_size=10)
        
        # 3 calls in round 1, 1 call in round 2
        self.assertEqual(mock_prompter.prompt_for_root_map_summary.call_count, 4)

    def test_recursive_summarize_truncation(self):
        mock_prompter = MagicMock()
        mock_prompter.prompt_for_root_map_summary.return_value = "summary"
        
        large_item = "x" * 30000
        items = [large_item]
        
        # Should NOT truncate if only 1 item (it just returns items[0])
        result = root_map._recursive_summarize(items, mock_prompter, max_item_chars=24000)
        self.assertEqual(len(result), 30000)
        
        # Should truncate if > 1 item
        items = [large_item, "another item"]
        result = root_map._recursive_summarize(items, mock_prompter, max_item_chars=24000)
        
        # Check that the prompter was called with a truncated string
        args, _ = mock_prompter.prompt_for_root_map_summary.call_args
        chunk_text = args[0]
        self.assertIn("[TRUNCATED]", chunk_text)
        self.assertTrue(len(chunk_text.split("\n\n")[0]) <= 24000 + len("\n...[TRUNCATED]"))

    def test_regenerate_root_map_flow(self):
        mock_fs = MagicMock()
        mock_state = MagicMock()
        mock_prompter = MagicMock()
        
        wu1 = work_unit_lib.WorkUnit(output_path=Path("dir/a"), files_to_index=set())
        wu1.size_bytes = 100
        wu2 = work_unit_lib.WorkUnit(output_path=Path("dir/b"), files_to_index=set())
        wu2.size_bytes = 100
        
        # Mock index_state.read_artifact to return valid JSON
        mock_state.read_artifact.side_effect = [
            '{"overview": {"content": "overview a"}, "verification_state": {"verified": true, "confidence": 1.0, "issues": []}}',
            '{"overview": {"content": "overview b"}, "verification_state": {"verified": true, "confidence": 1.0, "issues": []}}'
        ]
        mock_state.get_display_path.side_effect = ["dir/a", "dir/b"]
        mock_prompter.prompt_for_root_map_summary.return_value = "final project summary"
        
        with patch("pathlib.Path.write_text") as mock_write:
            with patch("pathlib.Path.mkdir"):
                root_map.regenerate_root_map([wu1, wu2], "/out", mock_state, 0, mock_fs, mock_prompter)
                
                # Check that final content contains the health bar and summary
                args, _ = mock_write.call_args
                content = args[0]
                self.assertIn("Root Map - Epoch 0", content)
                self.assertIn("final project summary", content)
                self.assertIn("100%", content) # Health bar

if __name__ == '__main__':
    unittest.main()
