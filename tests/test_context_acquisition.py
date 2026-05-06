import json
import os
import pytest
from unittest import mock
from harness.indexer_wrapper import acquire_context

@mock.patch("subprocess.run")
def test_acquire_context_generates_metadata(mock_run, tmp_path):
    # Setup mock subprocess to pretend it wrote an INDEX.json
    index_file = tmp_path / "INDEX.json"
    index_file.write_text('{"files": []}')
    
    # Mock successful run
    mock_run.return_value = mock.Mock(returncode=0)
    
    result_path = acquire_context(str(tmp_path), bundle_override=None)
    
    assert result_path == str(index_file)
    
    metadata_file = tmp_path / "metadata.json"
    assert metadata_file.exists()
    data = json.loads(metadata_file.read_text())
    assert "timestamp" in data
