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
