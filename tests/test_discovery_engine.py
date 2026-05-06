import pytest
from unittest import mock
from harness.discovery_engine import discover_agents

@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents(mock_query_llm):
    # Mock the LLM returning a valid JSON string
    mock_query_llm.return_value = '''
    {
      "agents": [
        {"name": "AuthAgent", "role": "Handles authentication logic", "zone": "Security"}
      ]
    }
    '''
    
    # Mock a tiny structural map
    structural_map = {"files": ["src/auth.py"]}
    
    agents = discover_agents(structural_map, "gemini", "fake-key")
    assert len(agents) == 1
    assert agents[0]["name"] == "AuthAgent"
