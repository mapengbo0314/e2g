import os
import json
from chat.config import load_config

def test_load_config_test_mode(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("PROJECT_ID", "proj-1")
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123")
    monkeypatch.setenv("REPO", "owner/repo")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    
    config = load_config()
    assert config["slack_bot_token"] == "xoxb-test"
    assert config["anthropic_api_key"] == "sk-ant-test"
    assert config["gemini_api_key"] == "gemini-test"
    assert "proj-1" in config["projects"]
    assert config["projects"]["proj-1"]["slack_channel_id"] == "C123"
    assert config["projects"]["proj-1"]["repo"] == "owner/repo"

def test_load_config_projects_json(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    projects_data = {
        "proj-1": {"slack_channel_id": "C1", "repo": "o/r1"},
        "proj-2": {"teams_url": "http://teams", "repo": "o/r2"}
    }
    monkeypatch.setenv("PROJECTS_JSON", json.dumps(projects_data))
    
    config = load_config()
    assert len(config["projects"]) == 2
    assert config["projects"]["proj-1"]["slack_channel_id"] == "C1"
    assert config["projects"]["proj-2"]["teams_url"] == "http://teams"

def test_load_config_cloud_credentials(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "aws-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws-secret")
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", '{"type": "service_account"}')
    
    from chat.config import load_config
    config = load_config()
    
    assert config["aws_access_key_id"] == "aws-key"
    assert config["aws_secret_access_key"] == "aws-secret"
    assert config["gcp_service_account_json"] == '{"type": "service_account"}'
