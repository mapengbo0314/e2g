import pytest
from unittest import mock
from harness.discovery_engine import discover_agents, discover_ddd_context

@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents(mock_query_llm, mock_fetch_skill):
    mock_fetch_skill.return_value = "Mocked skill"
    # Mock the LLM returning a valid JSON string
    mock_query_llm.return_value = '''
    {
      "agents": [
        {"name": "AuthAgent", "role": "Handles authentication logic", "zone": "Security"}
      ]
    }
    '''
    
    agents = discover_agents("Mocked context", "/fake/feature-fetcher.yaml", "gemini", "fake-key")
    assert len(agents) == 1
    assert agents[0]["name"] == "AuthAgent"
    mock_query_llm.assert_called_once()
    assert mock_fetch_skill.call_count == 2

@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents_with_ddd_context(mock_query_llm, mock_fetch_skill):
    mock_fetch_skill.return_value = "Mocked skill"
    mock_query_llm.return_value = '''
    {
      "agents": [
        {"name": "DomainExpert", "role": "Knows DDD", "zone": "Domain"}
      ]
    }
    '''
    
    ddd_ctx = {
        "ubiquitous_language": "Foo means Bar",
        "translation_map": {"Q": "A"},
        "legacy_hints": {}
    }
    
    agents = discover_agents("Mocked context", "/fake/feature-fetcher.yaml", "gemini", "fake-key", ddd_context=ddd_ctx)
    assert len(agents) == 1
    assert agents[0]["name"] == "DomainExpert"
    
    # Check if DDD context was injected in prompt
    call_args = mock_query_llm.call_args[0][0]
    assert "DOMAIN-DRIVEN DESIGN (DDD) CONTEXT" in call_args
    assert "Foo means Bar" in call_args

@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_ddd_context(mock_query_llm, mock_fetch_skill):
    mock_fetch_skill.return_value = "Mocked skill"
    
    # Mock LLM response
    mock_query_llm.return_value = '''
    {
      "context_draft": "Mocked Ubiquitous Language",
      "questions": ["Question 1?", "Question 2?"],
      "legacy_hints": {"deprecated": "old_module"}
    }
    '''
    
    result = discover_ddd_context("Mocked context", "gemini", "fake-key")
    
    assert result["context_draft"] == "Mocked Ubiquitous Language"
    assert len(result["questions"]) == 2
    assert "legacy_hints" in result
    mock_query_llm.assert_called_once()
    assert mock_fetch_skill.call_count == 2
