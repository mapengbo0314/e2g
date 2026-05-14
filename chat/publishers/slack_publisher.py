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
