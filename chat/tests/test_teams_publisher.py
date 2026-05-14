# chat/tests/test_teams_publisher.py
import requests
from chat.publishers.teams_publisher import publish_to_teams
from unittest.mock import patch

@patch('chat.publishers.teams_publisher.requests.post')
def test_publish_to_teams_success_200(mock_post):
    mock_post.return_value.status_code = 200
    
    result = publish_to_teams("http://fake-webhook.com", {"report": "data"})
    assert result is True
    mock_post.assert_called_once()
    # Ensure timeout=10 is used
    args, kwargs = mock_post.call_args
    assert kwargs.get('timeout') == 10

@patch('chat.publishers.teams_publisher.requests.post')
def test_publish_to_teams_success_202(mock_post):
    mock_post.return_value.status_code = 202
    
    result = publish_to_teams("http://fake-webhook.com", {"report": "data"})
    assert result is True
    mock_post.assert_called_once()

def test_publish_to_teams_missing_url():
    assert publish_to_teams("", {"report": "data"}) is False
    assert publish_to_teams(None, {"report": "data"}) is False

@patch('chat.publishers.teams_publisher.requests.post')
def test_publish_to_teams_network_exception(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    result = publish_to_teams("http://fake-webhook.com", {"report": "data"})
    assert result is False
    mock_post.assert_called_once()

@patch('chat.publishers.teams_publisher.requests.post')
def test_publish_to_teams_non_success_status(mock_post):
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"
    
    result = publish_to_teams("http://fake-webhook.com", {"report": "data"})
    assert result is False
    mock_post.assert_called_once()
