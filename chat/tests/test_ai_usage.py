from chat.fetchers.ai_usage import fetch_openai_usage, fetch_anthropic_usage, fetch_gemini_usage
from unittest.mock import patch
import requests

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_comprehensive(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "tokens_in": 1000, "tokens_out": 500, "prompts": 10, "cost": 0.05
    } 
    stats = fetch_openai_usage("fake-key")
    assert stats["tokens_in"] == 1000
    assert stats["cost"] == 0.05

def test_fetch_openai_usage_missing_key():
    stats = fetch_openai_usage("")
    assert stats["tokens_in"] == 0
    assert stats["cost"] == 0.0
    assert "error" in stats
    assert stats["error"] == "Missing API key"
    
    stats_none = fetch_openai_usage(None)
    assert stats_none["tokens_in"] == 0
    assert stats_none["cost"] == 0.0
    assert "error" in stats_none

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_timeout(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"tokens_in": 1000} 
    
    fetch_openai_usage("fake-key")
    
    # Assert timeout is provided
    kwargs = mock_get.call_args.kwargs
    assert kwargs.get("timeout") == 10

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_api_error(mock_get):
    mock_get.return_value.status_code = 401
    
    stats = fetch_openai_usage("fake-key")
    assert stats["tokens_in"] == 0
    assert stats["cost"] == 0.0
    assert "error" in stats

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    stats = fetch_openai_usage("fake-key")
    assert stats["tokens_in"] == 0
    assert stats["cost"] == 0.0
    assert "error" in stats

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_anthropic_usage_real(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "tokens_in": 2000, "tokens_out": 800, "prompts": 12, "cost": 0.08
    }
    stats = fetch_anthropic_usage("fake-key")
    assert stats["tokens_in"] == 2000
    assert stats["cost"] == 0.08

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_gemini_usage_real(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "tokens_in": 3000, "tokens_out": 1000, "prompts": 15, "cost": 0.01
    }
    stats = fetch_gemini_usage("fake-key")
    assert stats["tokens_in"] == 3000
    assert stats["cost"] == 0.01
