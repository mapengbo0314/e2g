# chat/tests/test_main.py
from chat.main import run_report
from unittest.mock import patch

@patch('chat.main.publish_to_slack')
@patch('chat.main.fetch_github_stats')
@patch('chat.main.load_config')
def test_run_report(mock_load, mock_gh, mock_slack):
    mock_load.return_value = {
        "slack_bot_token": "token",
        "github_token": "gh-token",
        "projects": {
            "proj-1": {
                "slack_channel_id": "C123",
                "repo": "owner/repo"
            }
        }
    }
    mock_gh.return_value = {"recent_prs_count": 5}
    mock_slack.return_value = True
    
    run_report()
    
    mock_gh.assert_called_with("gh-token", "owner/repo")
    mock_slack.assert_called_once()
