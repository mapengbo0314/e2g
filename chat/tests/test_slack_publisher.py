# chat/tests/test_slack_publisher.py
from chat.publishers.slack_publisher import publish_to_slack
from unittest.mock import patch

@patch('chat.publishers.slack_publisher.requests.post')
def test_publish_to_slack(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"ok": True}
    
    result = publish_to_slack("token", "C123", {"report": "data"})
    assert result is True
    mock_post.assert_called_once()
