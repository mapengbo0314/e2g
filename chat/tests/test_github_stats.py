# chat/tests/test_github_stats.py
from chat.fetchers.github_stats import fetch_github_stats
from unittest.mock import patch

@patch('chat.fetchers.github_stats.requests.get')
def test_fetch_github_stats(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"id": 1}, {"id": 2}] # Mocking 2 recent PRs
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats["recent_prs_count"] == 2
