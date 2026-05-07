import pytest
from unittest import mock
from harness.discovery_engine import discover_agents, discover_ddd_context

@mock.patch("harness.discovery_engine.acquire_mcp_context")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents(mock_query_llm, mock_acquire):
    # Mock the MCP context
    mock_acquire.return_value = "Mocked context"
    
    # Mock the LLM returning a valid JSON string
    mock_query_llm.return_value = '''
    {
      "agents": [
        {"name": "AuthAgent", "role": "Handles authentication logic", "zone": "Security"}
      ]
    }
    '''
    
    agents = discover_agents("/fake/path", "/fake/feature-fetcher.yaml", "gemini", "fake-key")
    assert len(agents) == 1
    assert agents[0]["name"] == "AuthAgent"
    mock_acquire.assert_called_once_with("/fake/path")

@mock.patch("harness.discovery_engine.query_llm")
def test_discover_ddd_context(mock_query_llm):
    # Mock LLM response
    mock_query_llm.return_value = '''
    {
      "ul_draft": "Mocked Ubiquitous Language",
      "questions": ["Question 1?", "Question 2?"],
      "legacy_hints": {"deprecated": "old_module"}
    }
    '''
    
    index_data = {"files": ["main.py", "utils.py"]}
    result = discover_ddd_context(index_data, "gemini", "fake-key")
    
    assert result["ul_draft"] == "Mocked Ubiquitous Language"
    assert len(result["questions"]) == 2
    assert "legacy_hints" in result
    mock_query_llm.assert_called_once()
