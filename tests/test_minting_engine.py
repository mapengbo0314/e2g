import pytest
import shutil
import tempfile
from pathlib import Path
import os
from unittest.mock import patch
from harness.minting_engine import mint_workspace, wait_for_user_review_and_read_domain

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

        # Check root pointer
        gemini_md = project_path / "GEMINI.md"
        assert gemini_md.exists(), "Expected GEMINI.md to exist in project root"
        pointer_content = gemini_md.read_text()
        assert ".gemini/orchestrator.md" in pointer_content

@patch('builtins.input', return_value='')
def test_wait_for_user_review_and_read_domain(mock_input, tmp_path):
    project_path = str(tmp_path)
    doc_path = os.path.join(project_path, "ONBOARDING_DOMAIN.md")
    
    with open(doc_path, 'w') as f:
        f.write("TEST CONTENT")
        
    content = wait_for_user_review_and_read_domain(project_path)
    
    assert mock_input.called
    assert content == "TEST CONTENT"

@patch('harness.discovery_engine.query_llm') 
def test_synthesize_domain_sme_agent(mock_query_llm, tmp_path):
    target_dir = str(tmp_path)
    domain_content = "Proposed Agent Name: @test-sme\nInvariants: None"
    
    # Mock LLM to return valid agent markdown
    mock_query_llm.return_value = "---\nname: test-sme\ndescription: SME\n---\n# Role\nSME"
    
    from harness.minting_engine import synthesize_domain_sme_agent
    
    synthesize_domain_sme_agent(target_dir, domain_content, mock_query_llm, "provider", "key")
    
    agent_file = os.path.join(target_dir, ".gemini", "agents", "test-sme.md")
    assert os.path.exists(agent_file)
    with open(agent_file, 'r') as f:
        assert "name: test-sme" in f.read()
