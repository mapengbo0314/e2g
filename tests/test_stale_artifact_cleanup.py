"""Focused tests for stale JSON artifact cleanup."""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import MagicMock, call

from indexing import orchestrator
from indexing import state


class TestStaleArtifactCleanup(unittest.TestCase):
    def test_local_state_delete_artifact_matches_summary_delete_semantics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            index_state = state.LocalState(temp_dir)
            path = "pkg/module"

            index_state.write_summary(path, 1, "summary")
            index_state.write_artifact(path, 1, '{"ok": true}')

            index_state.delete_artifact(path, 1)
            index_state.delete_artifact(path, 1)

            self.assertEqual(index_state.read_summary(path, 1), "summary")
            with self.assertRaises(FileNotFoundError):
                index_state.read_artifact(path, 1)

    def test_orchestrator_deletes_stale_artifacts_with_summaries(self):
        planner = MagicMock()
        planner.plan.return_value = SimpleNamespace(
            all_work_units=[],
            work_units_to_process=[],
            paths_to_delete=[Path("stale/package")],
        )
        index_state = MagicMock()
        fs = MagicMock()
        fs.normpath = lambda path: path
        fs.sep = lambda: "/"

        orch = orchestrator.Orchestrator(
            planner_instance=planner,
            indexer=MagicMock(),
            num_epochs=2,
            root_map_dir="/index",
            index_state=index_state,
            work_unit_storage=MagicMock(),
            fs_manager=fs,
            generate_root_map=False,
            perform_fs_checkpointing=False,
        )

        orch.run()

        expected_calls = [call("stale/package", 0), call("stale/package", 1)]
        index_state.delete_summary.assert_has_calls(expected_calls)
        index_state.delete_artifact.assert_has_calls(expected_calls)


if __name__ == "__main__":
    unittest.main()
