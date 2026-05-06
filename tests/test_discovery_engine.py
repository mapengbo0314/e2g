import pytest
from unittest import mock
from harness.discovery_engine import discover_agents

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
