import os
import json
from dotenv import load_dotenv

def _clean_env_val(val):
    if not val or not str(val).strip():
        return None
    v = str(val).lower()
    if "your" in v or "..." in v or "aizasy..." in v:
        return None
    return val

def load_config():
    # Attempt to load from chat/.env if it exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        
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
        "github_token": _clean_env_val(os.environ.get("GITHUB_TOKEN")),
        "openai_api_key": _clean_env_val(os.environ.get("OPENAI_API_KEY")),
        "anthropic_api_key": _clean_env_val(os.environ.get("ANTHROPIC_API_KEY")),
        "gemini_api_key": _clean_env_val(os.environ.get("GEMINI_API_KEY")),
        "aws_access_key_id": _clean_env_val(os.environ.get("AWS_ACCESS_KEY_ID")),
        "aws_secret_access_key": _clean_env_val(os.environ.get("AWS_SECRET_ACCESS_KEY")),
        "gcp_service_account_json": _clean_env_val(os.environ.get("GCP_SERVICE_ACCOUNT_JSON")),
        "projects": projects
    }
