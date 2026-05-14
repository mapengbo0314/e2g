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
    
    project_id = report_data.get('project', 'Unknown Project')
    stats = report_data.get('stats', {})
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Project Report: {project_id}",
                "emoji": True
            }
        }
    ]
    
    if "github" in stats:
        gh = stats["github"]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Engineering Metrics (GitHub)*"
            },
            "fields": [
                {"type": "mrkdwn", "text": f"*PRs Submitted:*\n{gh.get('prs_submitted', 0)}"},
                {"type": "mrkdwn", "text": f"*Lines Added:*\n{gh.get('lines_added', 0)}"},
                {"type": "mrkdwn", "text": f"*Lines Deleted:*\n{gh.get('lines_deleted', 0)}"},
                {"type": "mrkdwn", "text": f"*Bugs Closed:*\n{gh.get('bugs_closed', 0)}"},
                {"type": "mrkdwn", "text": f"*Releases:*\n{gh.get('releases_done', 0)}"}
            ]
        })
        
    # Aggregate AI stats if multiple providers exist
    ai_keys = ["openai", "anthropic", "gemini"]
    ai_blocks = []
    for ai_key in ai_keys:
        if ai_key in stats:
            ai = stats[ai_key]
            ai_blocks.extend([
                {"type": "mrkdwn", "text": f"*{ai_key.title()} Tokens:*\n{ai.get('tokens_consumed', 0)}"},
                {"type": "mrkdwn", "text": f"*{ai_key.title()} Cost:*\n${ai.get('cost', 0.0)}"}
            ])
            
    if ai_blocks:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*AI Usage Metrics*"
            },
            "fields": ai_blocks[:10] # Slack limit is 10 fields per section
        })
        
    # Aggregate Cloud stats
    cloud_keys = ["aws", "gcp"]
    cloud_blocks = []
    for cloud_key in cloud_keys:
        if cloud_key in stats:
            cloud = stats[cloud_key]
            cloud_blocks.append({"type": "mrkdwn", "text": f"*{cloud_key.upper()} Cost:*\n${cloud.get('cost', 0.0)}"})
            
    if cloud_blocks:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Infrastructure Costs*"
            },
            "fields": cloud_blocks
        })
        
    if "warnings" in report_data:
        warnings = report_data["warnings"]
        warnings_list = [f"{k}: {v}" for k, v in warnings.items()] if isinstance(warnings, dict) else [str(warnings)]
        warnings_text = "\n".join(warnings_list)
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":warning: _{warnings_text}_"
                }
            ]
        })
    
    payload = {
        "channel": channel_id,
        "text": f"Report for {project_id}",
        "blocks": blocks
    }
    
    try:
        resp = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload, timeout=10)
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            return True
        else:
            logging.error(f"Slack API error: {data}")
            return False
    except Exception as e:
        logging.error(f"Failed to post to Slack: {e}")
        return False
