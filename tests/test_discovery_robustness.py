import pytest
from unittest import mock
from harness.discovery_engine import discover_agents, discover_ddd_context, discover_custom_agent

@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents_robustness(mock_query_llm, mock_fetch_skill):
    mock_fetch_skill.return_value = "Mocked skill"
    # Mock the LLM returning INVALID JSON with unescaped quotes in system_prompt
    mock_query_llm.return_value = '''
    {
      "agents": [
        {
          "name": "AuthAgent", 
          "role": "Handles auth", 
          "zone": "Security",
          "system_prompt": "Operating in the "Goldfish" phase, you begin every session..."
        },
        {
          "name": "DataAgent", 
          "role": "Handles data", 
          "zone": "Data",
          "system_prompt": "You are the "Data" expert."
        }
      ]
    }
    '''
    
    # This should now succeed because of the fallback logic
    agents = discover_agents("Mocked context", "/fake/feature-fetcher.yaml", "gemini", "fake-key")
    assert len(agents) == 2
    assert agents[0]["name"] == "AuthAgent"
    assert 'Operating in the "Goldfish" phase' in agents[0]["system_prompt"]
    assert agents[1]["name"] == "DataAgent"
    assert 'You are the "Data" expert.' in agents[1]["system_prompt"]

@mock.patch("harness.discovery_engine.query_llm")
def test_discover_custom_agent_robustness(mock_query_llm):
    # Mock unescaped quotes
    mock_query_llm.return_value = '''
    {
      "name": "CustomAgent",
      "role": "Custom Role",
      "zone": "Core",
      "system_prompt": "I am a "special" agent with "many" quotes."
    }
    '''
    
    agent = discover_custom_agent("CustomAgent", "Specs", "Context", None, "gemini", "key")
    assert agent["name"] == "CustomAgent"
    assert 'I am a "special" agent with "many" quotes.' in agent["system_prompt"]

@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_ddd_context_robustness(mock_query_llm, mock_fetch_skill):
    mock_fetch_skill.return_value = "Mocked skill"
    
    # Mock LLM response with unescaped quotes in context_draft
    mock_query_llm.return_value = '''
    {
      "context_draft": "The "Domain" is complex.",
      "questions": ["Is it "really" complex?", "How "big" is it?"],
      "legacy_hints": {}
    }
    '''
    
    result = discover_ddd_context("Mocked context", "gemini", "fake-key")
    
    assert 'The "Domain" is complex.' in result["context_draft"]
    assert len(result["questions"]) == 2
    assert 'Is it "really" complex?' in result["questions"][0]
    assert 'How "big" is it?' in result["questions"][1]
