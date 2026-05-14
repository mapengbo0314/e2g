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
