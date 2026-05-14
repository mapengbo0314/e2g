# chat/tests/test_ai_usage.py
from chat.fetchers.ai_usage import fetch_openai_usage
from unittest.mock import patch

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"total_usage": 1500} 
    
    stats = fetch_openai_usage("fake-key")
    assert stats["total_usage"] == 1500
