from chat.fetchers.ai_usage import fetch_openai_usage, fetch_anthropic_usage, fetch_gemini_usage
from unittest.mock import patch
import requests

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "total_usage": 1500, # Representing cents
        "daily_costs": [
            {
                "timestamp": 1610000000,
                "line_items": [{"name": "Instruct models", "cost": 1500}]
            }
        ]
    } 
    
    stats = fetch_openai_usage("fake-key")
    assert stats["cost"] == 15.0 # 1500 cents
    assert stats["tokens_consumed"] == 0 # we might not get this from dashboard endpoint directly
    assert stats["prompt_count"] == "N/A"
    assert stats["status"] == "success"

def test_fetch_openai_usage_missing_key():
    stats = fetch_openai_usage("")
    assert stats["tokens_consumed"] == 0
    assert stats["cost"] == 0.0
    assert stats["status"] == "error"
    assert stats["error"] == "Missing API key"
    
    stats_none = fetch_openai_usage(None)
    assert stats_none["tokens_consumed"] == 0
    assert stats_none["cost"] == 0.0
    assert stats_none["status"] == "error"

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_timeout(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"total_usage": 1500} 
    
    fetch_openai_usage("fake-key")
    
    # Assert timeout is provided
    kwargs = mock_get.call_args.kwargs
    assert kwargs.get("timeout") == 10

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_api_error(mock_get):
    mock_get.return_value.status_code = 401
    
    stats = fetch_openai_usage("fake-key")
    assert stats["tokens_consumed"] == 0
    assert stats["cost"] == 0.0
    assert stats["status"] == "error"

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    stats = fetch_openai_usage("fake-key")
    assert stats["tokens_consumed"] == 0
    assert stats["cost"] == 0.0
    assert stats["status"] == "error"

def test_fetch_anthropic_usage():
    stats_no_key = fetch_anthropic_usage("")
    assert stats_no_key["status"] == "error"
    assert stats_no_key["error"] == "Missing API key"
    
    stats_with_key = fetch_anthropic_usage("fake-key")
    assert "tokens_consumed" in stats_with_key
    assert "cost" in stats_with_key
    assert "prompt_count" in stats_with_key
    assert stats_with_key["status"] in ["success", "API unsupported"]

def test_fetch_gemini_usage():
    stats_no_key = fetch_gemini_usage("")
    assert stats_no_key["status"] == "error"
    assert stats_no_key["error"] == "Missing API key"
    
    stats_with_key = fetch_gemini_usage("fake-key")
    assert "tokens_consumed" in stats_with_key
    assert "cost" in stats_with_key
    assert "prompt_count" in stats_with_key
    assert stats_with_key["status"] in ["success", "API unsupported"]
