"""Tests for the _SimpleProgressManager in Orchestrator."""

import json
import os
from pathlib import Path
import tempfile
import unittest
import threading
from indexing.orchestrator import _SimpleProgressManager

class FakeFsManager:
    def delete(self, path):
        if os.path.exists(path):
            os.remove(path)

class TestProgressManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_map_dir = self.temp_dir.name
        self.fs_manager = FakeFsManager()
        self.manager = _SimpleProgressManager(self.root_map_dir, self.fs_manager)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read_progress(self):
        epoch = 0
        data = {"path/a": "PENDING", "path/b": "COMPLETED"}
        self.manager.write_progress(epoch, data)
        
        read_data = self.manager.read_progress(epoch)
        self.assertEqual(read_data, data)
        
        # Verify it's JSONL
        path = self.manager.get_progress_file(epoch)
        with open(path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            json.loads(line) # Should be valid JSON

    def test_mark_completed_append(self):
        epoch = 1
        self.manager.write_progress(epoch, {"a": "PENDING"})
        self.manager.mark_work_unit_completed("a", epoch)
        
        progress = self.manager.read_progress(epoch)
        self.assertEqual(progress["a"], "COMPLETED")
        
        # Verify append (2 lines now)
        path = self.manager.get_progress_file(epoch)
        with open(path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)

    def test_compaction(self):
        epoch = 2
        path = self.manager.get_progress_file(epoch)
        
        # Write many entries to trigger compaction (simulated by making file large or just calling it)
        # We'll just call it explicitly to test logic, or mock getsize
        self.manager.write_progress(epoch, {"a": "PENDING"})
        for _ in range(10):
            self.manager.mark_work_unit_completed("a", epoch)
            
        # Before compaction (many lines)
        with open(path, "r") as f:
            lines = f.readlines()
        self.assertTrue(len(lines) > 2)
        
        # Trigger compaction (forcefully by holding lock and calling private method)
        with self.manager._lock:
            self.manager._compact_jsonl(epoch)
            
        # After compaction (1 line for "a")
        with open(path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        data = json.loads(lines[0])
        self.assertEqual(data["path"], "a")
        self.assertEqual(data["status"], "COMPLETED")

    def test_compaction_threshold(self):
        epoch = 3
        # Fill file with enough data to exceed 1MB
        path = self.manager.get_progress_file(epoch)
        large_data = "x" * 1024
        with open(path, "w") as f:
            for i in range(1100): # > 1MB
                f.write(json.dumps({"path": f"path_{i}", "status": "PENDING", "padding": large_data}) + "\n")
        
        # Mark one as completed should trigger compaction
        self.manager.mark_work_unit_completed("path_0", epoch)
        
        # File should be much smaller now because we only keep unique paths (and padding was lost in re-write of mark_completed logic but wait, _compact_jsonl uses progress dict which only has path/status)
        # Actually mark_work_unit_completed appends a simple {"path":..., "status": "COMPLETED"}
        # But _compact_jsonl reads all lines and appends only unique paths.
        
        with open(path, "r") as f:
            lines = f.readlines()
        
        # Every path_i should be there exactly once, plus the new "COMPLETED" for path_0
        self.assertEqual(len(lines), 1101)

if __name__ == '__main__':
    unittest.main()
