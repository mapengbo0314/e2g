from chat.fetchers.github_stats import fetch_github_stats
from unittest.mock import patch
import requests

@patch('chat.fetchers.github_stats.requests.get')
def test_fetch_github_stats_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"id": 1}, {"id": 2}] # Mocking 2 recent PRs
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats["recent_prs_count"] == 2

def test_fetch_github_stats_missing_inputs():
    stats = fetch_github_stats("", "owner/repo")
    assert stats["recent_prs_count"] == 0
    assert stats["error"] == "Missing token or repo"
    
    stats = fetch_github_stats("fake-token", "")
    assert stats["recent_prs_count"] == 0
    assert stats["error"] == "Missing token or repo"

@patch('chat.fetchers.github_stats.requests.get')
def test_fetch_github_stats_api_error(mock_get):
    mock_get.return_value.status_code = 404
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats["recent_prs_count"] == 0
    assert stats["error"] == "API error: 404"

@patch('chat.fetchers.github_stats.requests.get')
def test_fetch_github_stats_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats["recent_prs_count"] == 0
    assert stats["error"] == "Connection error"
