"""End-to-end dry run test for the indexing pipeline.

Ensures the entire orchestration flow (Chunking -> Indexing -> Merging -> Verification -> Root Mapping)
works correctly in mock mode without real LLM credentials.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from indexing import generate_bundles
from indexing import shared_flags

@pytest.fixture
def temp_workspace():
    """Sets up a temporary directory with a mock codebase structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create a mock codebase
        src = root / "src"
        src.mkdir()
        (src / "main.py").write_text("def main(): print('hello')")
        (src / "utils.py").write_text("def util(): pass")
        
        api = src / "api"
        api.mkdir()
        (api / "routes.py").write_text("class Routes: pass")
        
        # Output directory for index
        out = root / "index_out"
        out.mkdir()
        
        yield src, out

def test_pipeline_dry_run_success(temp_workspace):
    """Verifies that a full indexing run completes successfully in dry-run mode."""
    src_dir, out_dir = temp_workspace
    
    # Configure shared flags for dry run
    shared_flags.config.pipeline.dry_run = True
    shared_flags.config.llm.allow_mock_fallback = True
    shared_flags.config.pipeline.num_epochs = 1
    shared_flags.config.llm.max_parallelization = 1
    
    bundle = generate_bundles.BundleConfig(
        bundle_name="test_bundle",
        input_dirs=[str(src_dir)],
        output_dir=str(out_dir),
    )
    
    # Run the pipeline
    generate_bundles.execute_indexing(bundle)
    
    # Verify outputs
    # 1. Check for directory summaries (JSON artifacts)
    # The output structure is usually relative to the root being indexed.
    # In orchestrator, we use fs_manager.join(root_map_dir, display_path)
    # Our display path for src/api will be 'src/api' or similar.
    
    # Check if root map was created
    root_map = Path(out_dir) / "root_map_v0.md"
    assert root_map.exists(), f"Root map missing at {root_map}"
    content = root_map.read_text()
    assert "# Root Map - Epoch 0" in content
    assert "## Summary" in content
    
    # Check for individual index files
    # Orchestrator uses Path(output_dir) / rel_path / get_index_file_name(epoch)
    # Wait, the current Orchestrator implementation might vary.
    # Let's check where it writes.
    
    # In generate_bundles.py:
    # output_dir = bundle.output_dir or ...
    # index_state = state.LocalState(state_dir=output_dir, ...)
    # indexer_orchestrator = orchestrator.Orchestrator(root_map_dir=output_dir, ...)
    
    # In orchestrator.py:
    # output_path = self._fs_manager.join(self._root_map_dir, work_unit.output_path)
    # Then index_state.write_summary(output_path, epoch, ...)
    
    # Since we are indexing 'src_dir', and it has 'api' subfolder.
    # The work units will have output_path relative to src_dir? No, the planner uses absolute paths currently.
    
    # Let's see how the planner works in generate_bundles.py
    # units.append(work_unit.WorkUnit(output_path=dp, ...)) where dp is Path(dirpath)
    
    # If output_path is absolute, Orchestrator might create a weird nested path if it joins.
    # Actually, LocalFileSystemManager.join(a, b) if b is absolute might just return b? 
    # Usually os.path.join(a, b) where b is absolute returns b.
    
    # Let's verify the actual directory content
    all_files = [str(p) for p in Path(out_dir).rglob("*")]
    print(f"Generated files: {all_files}")
    
    assert any("llm_index_v0.md" in f for f in all_files)
    assert any("llm_index_v0.json" in f for f in all_files)

if __name__ == "__main__":
    pytest.main([__file__])
