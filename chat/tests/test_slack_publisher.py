# chat/tests/test_slack_publisher.py
import requests
from chat.publishers.slack_publisher import publish_to_slack
from unittest.mock import patch

@patch('chat.publishers.slack_publisher.requests.post')
def test_publish_to_slack_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"ok": True}
    
    result = publish_to_slack("token", "C123", {"report": "data"})
    assert result is True
    mock_post.assert_called_once()

def test_publish_to_slack_missing_credentials():
    # Empty credentials
    assert publish_to_slack("", "C123", {"report": "data"}) is False
    assert publish_to_slack("token", "", {"report": "data"}) is False
    # None credentials
    assert publish_to_slack(None, "C123", {"report": "data"}) is False
    assert publish_to_slack("token", None, {"report": "data"}) is False

@patch('chat.publishers.slack_publisher.requests.post')
def test_publish_to_slack_network_exception(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    result = publish_to_slack("token", "C123", {"report": "data"})
    assert result is False
    mock_post.assert_called_once()

@patch('chat.publishers.slack_publisher.requests.post')
def test_publish_to_slack_non_200_status(mock_post):
    mock_post.return_value.status_code = 500
    mock_post.return_value.json.return_value = {"ok": False}
    
    result = publish_to_slack("token", "C123", {"report": "data"})
    assert result is False
    mock_post.assert_called_once()

@patch('chat.publishers.slack_publisher.requests.post')
def test_publish_to_slack_api_returns_not_ok(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"ok": False, "error": "invalid_auth"}
    
    result = publish_to_slack("token", "C123", {"report": "data"})
    assert result is False
    mock_post.assert_called_once()
