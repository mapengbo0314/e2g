from chat.fetchers.github_stats import fetch_github_stats
from unittest.mock import patch
import requests
from datetime import datetime

@patch('chat.fetchers.github_stats.requests.post')
def test_fetch_github_stats_success(mock_post):
    today_str = datetime.utcnow().isoformat() + "Z"
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {"additions": 100, "deletions": 50, "mergedAt": today_str},
                        {"additions": 200, "deletions": 10, "mergedAt": today_str}
                    ]
                },
                "issues": {
                    "totalCount": 5
                },
                "releases": {
                    "nodes": [
                        {"createdAt": today_str},
                        {"createdAt": today_str}
                    ]
                }
            }
        }
    }
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    
    assert stats["prs_submitted"] == 2
    assert stats["lines_added"] == 300
    assert stats["lines_deleted"] == 60
    assert stats["bugs_closed"] == 5
    assert stats["releases_done"] == 2

def test_fetch_github_stats_missing_inputs():
    stats = fetch_github_stats("", "owner/repo")
    assert stats == {"prs_submitted": 0, "lines_added": 0, "lines_deleted": 0, "bugs_closed": 0, "releases_done": 0, "error": "Missing token or repo"}
    
    stats = fetch_github_stats("fake-token", "")
    assert stats == {"prs_submitted": 0, "lines_added": 0, "lines_deleted": 0, "bugs_closed": 0, "releases_done": 0, "error": "Missing token or repo"}

@patch('chat.fetchers.github_stats.requests.post')
def test_fetch_github_stats_api_error(mock_post):
    mock_post.return_value.status_code = 404
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats == {"prs_submitted": 0, "lines_added": 0, "lines_deleted": 0, "bugs_closed": 0, "releases_done": 0, "error": "API error: 404"}

@patch('chat.fetchers.github_stats.requests.post')
def test_fetch_github_stats_network_error(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats == {"prs_submitted": 0, "lines_added": 0, "lines_deleted": 0, "bugs_closed": 0, "releases_done": 0, "error": "Connection error"}
