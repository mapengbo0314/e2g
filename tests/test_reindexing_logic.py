"""Tests for re-indexing logic and work unit diffing."""

import unittest
from unittest.mock import MagicMock
from pathlib import Path
import datetime
from indexing import reindexing
from indexing import work_unit as work_unit_lib

class TestReindexingLogic(unittest.TestCase):
    def setUp(self):
        self.mock_storage = MagicMock()
        self.mock_strategy = MagicMock()
        self.differ = reindexing.IndexDiffer(
            work_unit_storage=self.mock_storage,
            change_detection_strategy=self.mock_strategy
        )

    def test_new_directory_needs_reindex(self):
        # Empty old manifest
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[], 
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[]
        )
        
        new_wu = work_unit_lib.WorkUnit(output_path=Path("new/dir"), files_to_index=set())
        diff = self.differ.get_work_units_to_reindex([new_wu])
        
        self.assertIn(new_wu, diff.to_reindex)

    def test_modified_file_needs_reindex(self):
        old_wu = work_unit_lib.WorkUnit(output_path=Path("dir"), files_to_index={Path("f1")})
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[old_wu],
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[]
        )
        
        # New work unit has different files
        new_wu = work_unit_lib.WorkUnit(output_path=Path("dir"), files_to_index={Path("f1"), Path("f2")})
        diff = self.differ.get_work_units_to_reindex([new_wu])
        
        self.assertIn(new_wu, diff.to_reindex)

    def test_removed_directory_triggers_parent_reindex(self):
        old_parent = work_unit_lib.WorkUnit(output_path=Path("parent"), files_to_index=set())
        old_child = work_unit_lib.WorkUnit(output_path=Path("parent/child"), files_to_index=set())
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[old_parent, old_child],
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[]
        )
        
        # Child is gone in new run
        new_parent = work_unit_lib.WorkUnit(output_path=Path("parent"), files_to_index=set())
        diff = self.differ.get_work_units_to_reindex([new_parent])
        
        self.assertIn(Path("parent/child"), diff.to_delete)
        self.assertIn(new_parent, diff.to_reindex) # Parent must update to remove child summary

    def test_propagation_child_to_parent(self):
        old_p = work_unit_lib.WorkUnit(output_path=Path("p"), files_to_index=set())
        old_c = work_unit_lib.WorkUnit(output_path=Path("p/c"), files_to_index={Path("f1")})
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[old_p, old_c],
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[]
        )
        self.mock_strategy.work_unit_needs_reindexing.return_value = False
        
        # Modify child files
        new_p = work_unit_lib.WorkUnit(output_path=Path("p"), files_to_index=set())
        new_c = work_unit_lib.WorkUnit(output_path=Path("p/c"), files_to_index={Path("f1"), Path("f2")})
        
        diff = self.differ.get_work_units_to_reindex([new_p, new_c])
        
        self.assertIn(new_c, diff.to_reindex)
        self.assertIn(new_p, diff.to_reindex) # Propagated

    def test_previous_failure_needs_reindex(self):
        wu = work_unit_lib.WorkUnit(output_path=Path("dir"), files_to_index=set())
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[wu],
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[wu] # Failed last time
        )
        
        diff = self.differ.get_work_units_to_reindex([wu])
        self.assertIn(wu, diff.to_reindex)

    def test_verification_failed_needs_reindex(self):
        wu = work_unit_lib.WorkUnit(output_path=Path("dir"), files_to_index=set())
        wu.last_indexed_info = work_unit_lib.LastIndexedInfo(
            commit_identifier=["v1"],
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            verification_state="FAILED"
        )
        self.mock_storage.read.return_value = work_unit_lib.WorkUnitManifest(
            work_units=[wu],
            last_indexed_info=work_unit_lib.LastIndexedInfo.empty(),
            errored_work_units=[]
        )
        
        diff = self.differ.get_work_units_to_reindex([wu])
        self.assertIn(wu, diff.to_reindex)

if __name__ == '__main__':
    unittest.main()
