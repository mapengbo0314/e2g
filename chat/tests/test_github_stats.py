from chat.fetchers.github_stats import fetch_github_stats
from unittest.mock import patch
import requests
from datetime import datetime, timedelta

@patch('chat.fetchers.github_stats.requests.post')
def test_fetch_github_stats_success(mock_post):
    today_str = datetime.utcnow().isoformat() + "Z"
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {"createdAt": today_str, "additions": 100, "deletions": 50, "mergedAt": today_str},
                        {"createdAt": today_str, "additions": 200, "deletions": 10, "mergedAt": today_str}
                    ]
                },
                "issues": {
                    "nodes": [
                        {"closedAt": today_str},
                        {"closedAt": today_str},
                        {"closedAt": today_str},
                        {"closedAt": today_str},
                        {"closedAt": today_str}
                    ]
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

@patch('chat.fetchers.github_stats.requests.post')
def test_fetch_github_stats_date_filtering(mock_post):
    today_dt = datetime.utcnow()
    today_str = today_dt.isoformat() + "Z"
    eight_days_ago_dt = today_dt - timedelta(days=8)
    eight_days_ago_str = eight_days_ago_dt.isoformat() + "Z"

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        # PR 1: Created 8 days ago, merged today. Counts for lines, not prs_submitted
                        {"createdAt": eight_days_ago_str, "mergedAt": today_str, "additions": 100, "deletions": 50},
                        # PR 2: Created today, not merged. Counts for prs_submitted, not lines
                        {"createdAt": today_str, "mergedAt": None, "additions": 200, "deletions": 10},
                        # PR 3: Created today, merged today. Counts for both
                        {"createdAt": today_str, "mergedAt": today_str, "additions": 300, "deletions": 20},
                        # PR 4: Created today, not merged. Counts for prs_submitted, not lines
                        {"createdAt": today_str, "mergedAt": None, "additions": 50, "deletions": 5}
                    ]
                },
                "issues": {
                    "nodes": [
                        # Issue 1: Closed today. Counts
                        {"closedAt": today_str},
                        # Issue 2: Closed 8 days ago. Does not count
                        {"closedAt": eight_days_ago_str}
                    ]
                },
                "releases": {
                    "nodes": []
                }
            }
        }
    }

    stats = fetch_github_stats("fake-token", "owner/repo")
    
    # 3 PRs created today (PR 2, 3, 4)
    assert stats["prs_submitted"] == 3
    # 2 PRs merged today (PR 1 and PR 3)
    assert stats["lines_added"] == 400
    assert stats["lines_deleted"] == 70
    # 1 bug closed today
    assert stats["bugs_closed"] == 1

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
