from unittest.mock import patch
import json
import os
from pathlib import Path
import pytest

@patch('urllib.request.urlopen')
def test_install_workspace_tools_guarantees_superpowers(mock_urlopen, tmp_path):
    target_dir = str(tmp_path)
    
    # Setup mock response for urlopen
    class MockResponse:
        def read(self): return b"# Mock Skill Content"
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    mock_urlopen.return_value = MockResponse()
    
    os.makedirs(os.path.join(target_dir, ".claude"), exist_ok=True)
    with open(os.path.join(target_dir, ".claude", "skills.json"), "w") as f:
        f.write('{"skills": {}}')
    
    from harness.minting_engine import install_workspace_tools
    install_workspace_tools(target_dir, ".claude", [], []) # Pass empty skills
    
    # Verify superpowers skill is downloaded anyway
    skill_path = os.path.join(target_dir, ".claude", "skills", "using-superpowers", "SKILL.md")
    assert os.path.exists(skill_path), f"Skill path {skill_path} does not exist"
    
    with open(os.path.join(target_dir, ".claude", "skills.json"), "r") as f:
        s_data = json.load(f)
        assert "using-superpowers" in s_data["skills"]
