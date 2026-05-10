import pytest
import shutil
import tempfile
import json
from pathlib import Path
import os
from unittest.mock import patch
from harness.minting_engine import (
    mint_workspace,
    wait_for_user_review_and_read_domain,
    patch_orchestrator_rules,
    parse_tool_checklists,
)

def test_parse_tool_checklists():
    content = """
## Proposed Skills
- [x] pytest (http://pytest)
- [ ] ignore_me (http://ignore)
- [x] debug (http://debug)

## Proposed MCP Tools
- [x] sql (npx -y sql)
- [ ] bad (npx bad)
    """

    skills, mcps = parse_tool_checklists(content)

    assert len(skills) == 2
    assert skills[0] == {"name": "pytest", "url": "http://pytest"}
    assert skills[1] == {"name": "debug", "url": "http://debug"}

    assert len(mcps) == 1
    assert mcps[0] == {"name": "sql", "command": "npx -y sql"}

def test_patch_orchestrator_rules(tmp_path):
    target_dir = str(tmp_path)
    rules_dir = os.path.join(target_dir, ".gemini", "rules")
    os.makedirs(rules_dir)
    rules_path = os.path.join(rules_dir, "dispatch_rules.md")
    
    with open(rules_path, "w") as f:
        f.write("# Rules\nSome generic rules.\n<orchestration_hierarchy>\nRules here\n</orchestration_hierarchy>")
        
    patch_orchestrator_rules(target_dir, "test-sme")
    
    with open(rules_path, "r") as f:
        content = f.read()
        assert "@test-sme" in content
        assert "Domain SME Gateway" in content

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

@patch('urllib.request.urlopen')
def test_install_workspace_tools(mock_urlopen, tmp_path):
    target_dir = str(tmp_path)
    
    # Setup mock response for urlopen
    class MockResponse:
        def read(self): return b"# Mock Skill Content"
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    mock_urlopen.return_value = MockResponse()
    
    # Create empty skills.json and mcp.json to simulate boilerplate
    os.makedirs(os.path.join(target_dir, ".gemini"), exist_ok=True)
    with open(os.path.join(target_dir, ".gemini", "skills.json"), "w") as f:
        f.write('{"skills": {}}')
    with open(os.path.join(target_dir, ".gemini", "mcp.json"), "w") as f:
         f.write('{"mcpServers": {}}')
         
    skills = [{"name": "test-skill", "url": "http://mock"}]
    mcps = [{"name": "test-mcp", "command": "npx mock"}]
    
    from harness.minting_engine import install_workspace_tools
    install_workspace_tools(target_dir, ".gemini", skills, mcps)
    
    # Verify Skill downloaded
    skill_path = os.path.join(target_dir, ".gemini", "skills", "test-skill", "SKILL.md")
    assert os.path.exists(skill_path)
    
    # Verify Configs updated
    with open(os.path.join(target_dir, ".gemini", "skills.json"), "r") as f:
        s_data = json.load(f)
        assert "test-skill" in s_data["skills"]
        
    with open(os.path.join(target_dir, ".gemini", "mcp.json"), "r") as f:
        m_data = json.load(f)
        assert "test-mcp" in m_data["mcpServers"]
        assert m_data["mcpServers"]["test-mcp"]["command"] == "bash"
        assert "npx mock" in m_data["mcpServers"]["test-mcp"]["args"][1]
