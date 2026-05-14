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
    
    project_id = report_data.get('project_id', 'Unknown Project')
    
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
    
    if "github" in report_data:
        gh = report_data["github"]
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*GitHub PRs:*\n{gh.get('prs', 0)}"},
                {"type": "mrkdwn", "text": f"*Lines:*\n{gh.get('lines', 0)}"},
                {"type": "mrkdwn", "text": f"*Bugs:*\n{gh.get('bugs', 0)}"}
            ]
        })
        
    if "ai" in report_data:
        ai = report_data["ai"]
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*AI Tokens:*\n{ai.get('tokens', 0)}"},
                {"type": "mrkdwn", "text": f"*AI Cost:*\n${ai.get('cost', 0.0)}"}
            ]
        })
        
    if "cloud" in report_data:
        cloud = report_data["cloud"]
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Cloud Cost:*\n${cloud.get('cost', 0.0)}"}
            ]
        })
        
    if "warnings" in report_data:
        warnings = report_data["warnings"]
        warnings_text = "\n".join(warnings) if isinstance(warnings, list) else str(warnings)
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
