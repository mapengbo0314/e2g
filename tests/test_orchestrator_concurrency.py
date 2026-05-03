"""Tests for Orchestrator concurrency and fail-fast logic."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import threading
import time
import datetime
from indexing import orchestrator
from indexing import work_unit as work_unit_lib

class TestOrchestratorConcurrency(unittest.TestCase):
    def setUp(self):
        self.planner = MagicMock()
        self.indexer = MagicMock()
        self.index_state = MagicMock()
        self.storage = MagicMock()
        self.fs = MagicMock()
        self.fs.normpath = lambda p: p.replace("\\", "/")
        self.fs.sep = lambda: "/"
        self.fs.join = lambda *p: "/".join(p)
        
        self.orch = orchestrator.Orchestrator(
            planner_instance=self.planner,
            indexer=self.indexer,
            num_epochs=1,
            root_map_dir="/root",
            index_state=self.index_state,
            work_unit_storage=self.storage,
            max_workers=4,
            fs_manager=self.fs,
            perform_fs_checkpointing=False # Simplify
        )

    def test_depth_sorting(self):
        # Create work units with different depths
        wu_deep = work_unit_lib.WorkUnit(output_path=Path("a/b/c"), files_to_index=set())
        wu_mid = work_unit_lib.WorkUnit(output_path=Path("a/b"), files_to_index=set())
        wu_shallow = work_unit_lib.WorkUnit(output_path=Path("a"), files_to_index=set())
        
        work_units = [wu_shallow, wu_mid, wu_deep]
        
        # Track order of calls
        call_order = []
        def mock_process(wu, epoch, *args, **kwargs):
            call_order.append(str(wu.output_path))
            return MagicMock(success=True, markdown_result="ok", artifact=None)

        self.indexer.generate_index_for_work_unit.side_effect = mock_process
        
        self.orch._run_epoch(work_units, 0)
        
        # Should be deep -> mid -> shallow
        self.assertEqual(call_order, ["a/b/c", "a/b", "a"])

    def test_fail_fast(self):
        # Create 2 work units
        wu1 = work_unit_lib.WorkUnit(output_path=Path("a"), files_to_index=set())
        wu2 = work_unit_lib.WorkUnit(output_path=Path("b"), files_to_index=set())
        
        def fail_wu(wu, epoch, *args, **kwargs):
            if str(wu.output_path) == "a":
                raise ValueError("Boom")
            time.sleep(0.1)
            return MagicMock(success=True)

        self.indexer.generate_index_for_work_unit.side_effect = fail_wu
        
        with self.assertRaises(ValueError):
            self.orch._run_epoch([wu1, wu2], 0)

    def test_parallel_execution(self):
        # Verify that multiple workers are used
        wu_list = [work_unit_lib.WorkUnit(output_path=Path(f"dir_{i}"), files_to_index=set()) for i in range(5)]
        
        worker_ids = set()
        def track_worker(wu, epoch, *args, **kwargs):
            worker_ids.add(threading.get_ident())
            time.sleep(0.05)
            return MagicMock(success=True, markdown_result="ok", artifact=None)

        self.indexer.generate_index_for_work_unit.side_effect = track_worker
        
        self.orch._run_epoch(wu_list, 0)
        
        # Should have used more than one thread (max_workers=4)
        self.assertTrue(len(worker_ids) > 1)

if __name__ == '__main__':
    unittest.main()
