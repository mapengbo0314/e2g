import os
import json
from dotenv import load_dotenv

def load_config():
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"
    if test_mode:
        load_dotenv()
        
    projects_json_str = os.environ.get("PROJECTS_JSON")
    if projects_json_str:
        try:
            projects = json.loads(projects_json_str)
        except json.JSONDecodeError:
            projects = {}
    else:
        # Build a single-project config from flat env vars
        project_id = os.environ.get("PROJECT_ID", "default-proj")
        slack_channel_id = os.environ.get("SLACK_CHANNEL_ID")
        teams_url = os.environ.get("TEAMS_URL")
        repo = os.environ.get("REPO")
        
        projects = {
            project_id: {
                "slack_channel_id": slack_channel_id,
                "teams_url": teams_url,
                "repo": repo
            }
        }
    
    return {
        "slack_bot_token": os.environ.get("SLACK_BOT_TOKEN"),
        "github_token": os.environ.get("GITHUB_TOKEN"),
        "openai_api_key": os.environ.get("OPENAI_API_KEY"),
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY"),
        "projects": projects
    }
