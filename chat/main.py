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
