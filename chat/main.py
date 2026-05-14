from chat.config import load_config
from chat.fetchers.github_stats import fetch_github_stats
from chat.fetchers.ai_usage import fetch_openai_usage
from chat.publishers.slack_publisher import publish_to_slack
from chat.publishers.teams_publisher import publish_to_teams
import logging

def run_report():
    config = load_config()
    
    # Fetch global stats once
    global_openai_stats = None
    if config.get("openai_api_key"):
        try:
            global_openai_stats = fetch_openai_usage(config["openai_api_key"])
        except Exception as e:
            logging.error(f"Failed to fetch global OpenAI usage: {e}")
    
    for project_id, proj_config in config.get("projects", {}).items():
        logging.info(f"Processing project: {project_id}")
        
        try:
            report_data = {"project": project_id, "stats": {}}
            
            # Fetch data
            if "repo" in proj_config and config.get("github_token"):
                report_data["stats"]["github"] = fetch_github_stats(config["github_token"], proj_config["repo"])
                
            if global_openai_stats:
                report_data["stats"]["openai"] = global_openai_stats
                
            # Publish
            if proj_config.get("slack_channel_id"):
                publish_to_slack(config.get("slack_bot_token"), proj_config["slack_channel_id"], report_data)
                
            if proj_config.get("teams_url"):
                publish_to_teams(proj_config["teams_url"], report_data)
        except Exception as e:
            logging.error(f"Failed to process project {project_id}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_report()
