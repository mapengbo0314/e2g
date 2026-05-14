# Project Reporting Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a serverless bot that fetches AI/GitHub stats and publishes aggregated reports to Slack and Teams.

**Architecture:** Python application with decoupled fetchers (AI APIs, GitHub), publishers (Slack, Teams), and a central orchestrator. Uses `config.py` with `TEST_MODE` for local `.env` overriding of Secrets Manager/DynamoDB.

**Tech Stack:** Python 3.11+, `requests` (for API calls), `pytest` (for testing), `python-dotenv` (for local testing).

---

### Task 1: Project Setup and Configuration Module

**Files:**
- Create: `chat/requirements.txt`
- Create: `chat/config.py`
- Create: `chat/tests/test_config.py`

- [ ] **Step 1: Write the failing test for Config loading**
```python
# chat/tests/test_config.py
import os
from chat.config import load_config

def test_load_config_test_mode(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("PROJECT_ID", "proj-1")
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123")
    
    config = load_config()
    assert config["slack_bot_token"] == "xoxb-test"
    assert "proj-1" in config["projects"]
    assert config["projects"]["proj-1"]["slack_channel_id"] == "C123"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_config.py -v`
Expected: FAIL (module not found or function not defined)

- [ ] **Step 3: Write minimal implementation**
```python
# chat/requirements.txt
requests
pytest
python-dotenv

# chat/config.py
import os
from dotenv import load_dotenv

def load_config():
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"
    if test_mode:
        load_dotenv()
        
    # In test mode, build a dummy project config from env vars
    project_id = os.environ.get("PROJECT_ID", "default-proj")
    slack_channel_id = os.environ.get("SLACK_CHANNEL_ID")
    teams_url = os.environ.get("TEAMS_URL")
    
    projects = {
        project_id: {
            "slack_channel_id": slack_channel_id,
            "teams_url": teams_url
        }
    }
    
    return {
        "slack_bot_token": os.environ.get("SLACK_BOT_TOKEN"),
        "github_token": os.environ.get("GITHUB_TOKEN"),
        "openai_api_key": os.environ.get("OPENAI_API_KEY"),
        "projects": projects
    }
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pip install -r chat/requirements.txt && PYTHONPATH=. pytest chat/tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/requirements.txt chat/config.py chat/tests/test_config.py
git commit -m "feat: add config loader with test mode support"
```

### Task 2: GitHub Stats Fetcher

**Files:**
- Create: `chat/fetchers/github_stats.py`
- Create: `chat/tests/test_github_stats.py`

- [ ] **Step 1: Write the failing test**
```python
# chat/tests/test_github_stats.py
from chat.fetchers.github_stats import fetch_github_stats
from unittest.mock import patch

@patch('chat.fetchers.github_stats.requests.get')
def test_fetch_github_stats(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"id": 1}, {"id": 2}] # Mocking 2 recent PRs
    
    stats = fetch_github_stats("fake-token", "owner/repo")
    assert stats["recent_prs_count"] == 2
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_github_stats.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
# chat/fetchers/github_stats.py
import requests
import logging

def fetch_github_stats(token: str, repo: str) -> dict:
    if not token or not repo:
        return {"recent_prs_count": 0, "error": "Missing token or repo"}
        
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        # Example: Fetch recent pulls
        resp = requests.get(f"https://api.github.com/repos/{repo}/pulls?state=all&per_page=10", headers=headers)
        if resp.status_code == 200:
            prs = resp.json()
            return {"recent_prs_count": len(prs)}
        else:
            return {"recent_prs_count": 0, "error": f"API error: {resp.status_code}"}
    except Exception as e:
        logging.error(f"GitHub fetch failed: {e}")
        return {"recent_prs_count": 0, "error": str(e)}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. pytest chat/tests/test_github_stats.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/fetchers/github_stats.py chat/tests/test_github_stats.py
git commit -m "feat: add github stats fetcher"
```

### Task 3: AI Usage Fetcher (OpenAI Stub)

**Files:**
- Create: `chat/fetchers/ai_usage.py`
- Create: `chat/tests/test_ai_usage.py`

- [ ] **Step 1: Write the failing test**
```python
# chat/tests/test_ai_usage.py
from chat.fetchers.ai_usage import fetch_openai_usage
from unittest.mock import patch

@patch('chat.fetchers.ai_usage.requests.get')
def test_fetch_openai_usage(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"total_usage": 1500} 
    
    stats = fetch_openai_usage("fake-key")
    assert stats["total_usage"] == 1500
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_ai_usage.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
# chat/fetchers/ai_usage.py
import requests
import logging
from datetime import datetime, timedelta

def fetch_openai_usage(api_key: str) -> dict:
    if not api_key:
        return {"total_usage": 0, "error": "Missing API key"}
        
    headers = {"Authorization": f"Bearer {api_key}"}
    # For a real implementation, you'd calculate dates. Stubbing for now.
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        resp = requests.get(
            f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"total_usage": 0, "error": f"API error: {resp.status_code}"}
    except Exception as e:
        logging.error(f"OpenAI fetch failed: {e}")
        return {"total_usage": 0, "error": str(e)}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. pytest chat/tests/test_ai_usage.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/fetchers/ai_usage.py chat/tests/test_ai_usage.py
git commit -m "feat: add openai usage fetcher"
```

### Task 4: Slack Publisher

**Files:**
- Create: `chat/publishers/slack_publisher.py`
- Create: `chat/tests/test_slack_publisher.py`

- [ ] **Step 1: Write the failing test**
```python
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_slack_publisher.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
# chat/publishers/slack_publisher.py
import requests
import json
import logging

def publish_to_slack(bot_token: str, channel_id: str, report_data: dict) -> bool:
    if not bot_token or not channel_id:
        logging.error("Missing Slack credentials")
        return False
        
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Very basic formatting for the proof of concept
    text = f"*Weekly Report*\n```\n{json.dumps(report_data, indent=2)}\n```"
    payload = {
        "channel": channel_id,
        "text": text
    }
    
    try:
        resp = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            return True
        else:
            logging.error(f"Slack API error: {data}")
            return False
    except Exception as e:
        logging.error(f"Failed to post to Slack: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. pytest chat/tests/test_slack_publisher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/publishers/slack_publisher.py chat/tests/test_slack_publisher.py
git commit -m "feat: add slack publisher"
```

### Task 5: Teams Publisher

**Files:**
- Create: `chat/publishers/teams_publisher.py`
- Create: `chat/tests/test_teams_publisher.py`

- [ ] **Step 1: Write the failing test**
```python
# chat/tests/test_teams_publisher.py
from chat.publishers.teams_publisher import publish_to_teams
from unittest.mock import patch

@patch('chat.publishers.teams_publisher.requests.post')
def test_publish_to_teams(mock_post):
    mock_post.return_value.status_code = 202
    
    result = publish_to_teams("http://fake-webhook.com", {"report": "data"})
    assert result is True
    mock_post.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_teams_publisher.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
# chat/publishers/teams_publisher.py
import requests
import logging

def publish_to_teams(webhook_url: str, report_data: dict) -> bool:
    if not webhook_url:
        logging.error("Missing Teams webhook URL")
        return False
        
    try:
        resp = requests.post(webhook_url, json=report_data)
        # Teams Power Automate webhooks often return 202 Accepted
        if resp.status_code in (200, 202):
            return True
        else:
            logging.error(f"Teams webhook error: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logging.error(f"Failed to post to Teams: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. pytest chat/tests/test_teams_publisher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/publishers/teams_publisher.py chat/tests/test_teams_publisher.py
git commit -m "feat: add teams publisher"
```

### Task 6: Main Orchestrator

**Files:**
- Create: `chat/main.py`
- Create: `chat/tests/test_main.py`

- [ ] **Step 1: Write the failing test**
```python
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. pytest chat/tests/test_main.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
# chat/main.py
from chat.config import load_config
from chat.fetchers.github_stats import fetch_github_stats
from chat.fetchers.ai_usage import fetch_openai_usage
from chat.publishers.slack_publisher import publish_to_slack
from chat.publishers.teams_publisher import publish_to_teams
import logging

logging.basicConfig(level=logging.INFO)

def run_report():
    config = load_config()
    
    for project_id, proj_config in config.get("projects", {}).items():
        logging.info(f"Processing project: {project_id}")
        
        report_data = {"project": project_id, "stats": {}}
        
        # Fetch data
        if "repo" in proj_config and config.get("github_token"):
            report_data["stats"]["github"] = fetch_github_stats(config["github_token"], proj_config["repo"])
            
        if config.get("openai_api_key"):
            report_data["stats"]["openai"] = fetch_openai_usage(config["openai_api_key"])
            
        # Publish
        if proj_config.get("slack_channel_id"):
            publish_to_slack(config.get("slack_bot_token"), proj_config["slack_channel_id"], report_data)
            
        if proj_config.get("teams_url"):
            publish_to_teams(proj_config["teams_url"], report_data)

if __name__ == "__main__":
    run_report()
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. pytest chat/tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add chat/main.py chat/tests/test_main.py
git commit -m "feat: add main orchestrator logic"
```