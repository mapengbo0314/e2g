import pytest
import shutil
import tempfile
from pathlib import Path
import os
from harness.minting_engine import mint_workspace

def test_mint_workspace_agent_naming():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_dir = tmp_path / "target"
        project_path = tmp_path / "project"
        boilerplate_dir = tmp_path / "boilerplate"
        
        # Create dummy directories
        project_path.mkdir()
        boilerplate_dir.mkdir()
        
        selected_agents = [
            {
                "name": "ArchitectureDeepener",
                "role": "Deepens architecture",
                "system_prompt": "You are a deepener."
            }
        ]
        
        # Call mint_workspace
        mint_workspace(
            target_dir=str(target_dir),
            selected_agents=selected_agents,
            project_path=str(project_path),
            platform_choice="gemini",
            boilerplate_dir=str(boilerplate_dir)
        )
        
        # Check filename
        agent_file = target_dir / "agents" / "architecture-deepener.md"
        assert agent_file.exists(), f"Expected {agent_file} to exist"
        
        # Check frontmatter name
        content = agent_file.read_text()
        assert "name: architecture-deepener" in content
        assert "name: ArchitectureDeepener" not in content
