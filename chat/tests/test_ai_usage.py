# chat/tests/test_ai_usage.py
from chat.fetchers.ai_usage import fetch_openai_usage, fetch_anthropic_usage, fetch_gemini_usage
from unittest.mock import patch
import requests

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"total_usage": 1500} 
    
    stats = fetch_openai_usage("fake-key")
    assert stats["total_usage"] == 1500

def test_fetch_openai_usage_missing_key():
    stats = fetch_openai_usage("")
    assert stats["total_usage"] == 0
    assert stats["error"] == "Missing API key"
    
    stats_none = fetch_openai_usage(None)
    assert stats_none["total_usage"] == 0
    assert stats_none["error"] == "Missing API key"

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
    assert stats["total_usage"] == 0
    assert stats["error"] == "API error: 401"

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    stats = fetch_openai_usage("fake-key")
    assert stats["total_usage"] == 0
    assert stats["error"] == "Connection error"

def test_fetch_anthropic_usage():
    stats_no_key = fetch_anthropic_usage("")
    assert stats_no_key["error"] == "Missing API key"
    
    stats_with_key = fetch_anthropic_usage("fake-key")
    assert stats_with_key["status"] == "stubbed"

def test_fetch_gemini_usage():
    stats_no_key = fetch_gemini_usage("")
    assert stats_no_key["error"] == "Missing API key"
    
    stats_with_key = fetch_gemini_usage("fake-key")
    assert stats_with_key["status"] == "stubbed"
