# chat/tests/test_main.py
from chat.main import run_report
from unittest.mock import patch, MagicMock

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

@patch('chat.main.publish_to_teams')
@patch('chat.main.load_config')
def test_run_report_teams(mock_load, mock_teams):
    mock_load.return_value = {
        "projects": {
            "proj-teams": {
                "teams_url": "https://teams.webhook.url"
            }
        }
    }
    mock_teams.return_value = True

    run_report()

    mock_teams.assert_called_once_with("https://teams.webhook.url", {"project": "proj-teams", "stats": {}})

@patch('chat.main.fetch_openai_usage')
@patch('chat.main.load_config')
def test_run_report_openai_fetched_once(mock_load, mock_openai):
    mock_load.return_value = {
        "openai_api_key": "openai-key",
        "projects": {
            "proj-1": {},
            "proj-2": {}
        }
    }
    mock_openai.return_value = {"usage": 100}

    run_report()

    # Should only be called once, outside the project loop
    mock_openai.assert_called_once_with("openai-key")

@patch('chat.main.publish_to_slack')
@patch('chat.main.fetch_github_stats')
@patch('chat.main.load_config')
def test_run_report_partial_failure(mock_load, mock_gh, mock_slack):
    mock_load.return_value = {
        "slack_bot_token": "token",
        "github_token": "gh-token",
        "projects": {
            "proj-fail": {
                "slack_channel_id": "C123",
                "repo": "owner/repo-fail"
            },
            "proj-success": {
                "slack_channel_id": "C456",
                "repo": "owner/repo-success"
            }
        }
    }
    
    # Make the first repo fail, and the second succeed
    def mock_gh_side_effect(token, repo):
        if repo == "owner/repo-fail":
            raise Exception("GitHub API down")
        return {"recent_prs_count": 10}
        
    mock_gh.side_effect = mock_gh_side_effect

    run_report()

    # The loop should have continued and processed the second project
    assert mock_gh.call_count == 2
    mock_slack.assert_called_once_with("token", "C456", {"project": "proj-success", "stats": {"github": {"recent_prs_count": 10}}})

@patch('chat.main.publish_to_slack')
@patch('chat.main.fetch_github_stats')
@patch('chat.main.load_config')
def test_run_report_error_filtering(mock_load, mock_gh, mock_slack):
    mock_load.return_value = {
        "slack_bot_token": "token",
        "github_token": "gh-token",
        "projects": {
            "proj-error": {
                "slack_channel_id": "C123",
                "repo": "owner/repo"
            }
        }
    }
    
    # Return a dictionary with an "error" key
    mock_gh.return_value = {"error": "API limit exceeded", "partial_data": True}

    run_report()

    # The error should be moved to warnings
    mock_slack.assert_called_once_with(
        "token", 
        "C123", 
        {
            "project": "proj-error", 
            "stats": {"github": {"partial_data": True}},
            "warnings": {"github": "API limit exceeded"}
        }
    )
