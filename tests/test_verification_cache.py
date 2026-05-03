"""Tests for the VerificationCache subsystem."""

import json
import os
from pathlib import Path
import tempfile
import unittest
import logging
from indexing.verification import VerificationCache

class TestVerificationCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.cache_file = self.temp_path / "test_cache.jsonl"
        # Ensure we don't have leftover files
        if self.cache_file.exists(): self.cache_file.unlink()
        legacy = self.cache_file.with_suffix(".json")
        if legacy.exists(): legacy.unlink()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_legacy_migration(self):
        # Create legacy JSON file
        legacy_file = self.cache_file.with_suffix(".json")
        legacy_data = {
            "hash1": {"passed": True, "confidence": 1.0},
            "hash2": {"passed": False, "confidence": 0.0}
        }
        with open(legacy_file, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)
        
        # Init cache should trigger migration
        cache = VerificationCache(self.cache_file)
        
        self.assertEqual(cache.cache["hash1"]["passed"], True)
        self.assertEqual(cache.cache["hash2"]["passed"], False)
        
        # Legacy file should be unlinked
        self.assertFalse(legacy_file.exists())
        # JSONL should exist
        self.assertTrue(self.cache_file.exists())

    def test_orphaned_legacy_cleanup(self):
        # Create both legacy and jsonl
        legacy_file = self.cache_file.with_suffix(".json")
        with open(legacy_file, "w", encoding="utf-8") as f:
            json.dump({"old": "data"}, f)
        
        with open(self.cache_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"key": "new", "verdict": {"passed": True}}) + "\n")
            
        # Init cache should detect both and cleanup legacy
        cache = VerificationCache(self.cache_file)
        
        self.assertIn("new", cache.cache)
        self.assertNotIn("old", cache.cache)
        self.assertFalse(legacy_file.exists())

    def test_compaction_on_load(self):
        # Create JSONL with duplicate keys
        with open(self.cache_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"key": "h1", "verdict": {"v": 1}}) + "\n")
            f.write(json.dumps({"key": "h1", "verdict": {"v": 2}}) + "\n")
            f.write(json.dumps({"key": "h2", "verdict": {"v": 3}}) + "\n")
            
        # Init cache should load and compact
        cache = VerificationCache(self.cache_file)
        
        self.assertEqual(cache.cache["h1"]["v"], 2) # Last write wins
        self.assertEqual(cache.cache["h2"]["v"], 3)
        
        # Verify file content is compacted
        with open(self.cache_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)

    def test_store_verdict_atomic_append(self):
        cache = VerificationCache(self.cache_file)
        
        class FakeVerdict:
            def model_dump(self): return {"passed": True}
        
        cache.store_verdict("art", "ctx", FakeVerdict())
        
        # Verify it's in memory
        key = cache._compute_hash("art", "ctx")
        self.assertIn(key, cache.cache)
        
        # Verify it's in file
        with open(self.cache_file, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            self.assertEqual(data["key"], key)

if __name__ == '__main__':
    unittest.main()
