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
        gh_text = (
            "🛠️ *Engineering Metrics (GitHub)*\n"
            f"• *PRs Submitted:* {gh.get('prs_submitted', 0)}\n"
            f"• *Lines Added:* {gh.get('lines_added', 0)}\n"
            f"• *Lines Deleted:* {gh.get('lines_deleted', 0)}\n"
            f"• *Bugs Closed:* {gh.get('bugs_closed', 0)}\n"
            f"• *Releases:* {gh.get('releases_done', 0)}"
        )
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": gh_text
            }
        })
        
    # Aggregate AI stats if multiple providers exist
    ai_keys = ["openai", "anthropic", "gemini"]
    ai_lines = []
    for ai_key in ai_keys:
        if ai_key in stats:
            ai = stats[ai_key]
            ai_lines.append(f"• *{ai_key.title()}*: model `{ai.get('model', 'unknown')}` | In: {ai.get('tokens_in', 0)} | Out: {ai.get('tokens_out', 0)} | Cost: ${ai.get('cost', 0.0):.4f}")
            
    if ai_lines:
        ai_text = "🤖 *AI Usage Metrics*\n" + "\n".join(ai_lines)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ai_text
            }
        })
        
    # Aggregate Cloud stats
    cloud_keys = ["aws", "gcp"]
    cloud_lines = []
    for cloud_key in cloud_keys:
        if cloud_key in stats:
            cloud = stats[cloud_key]
            cost_val = cloud.get('cost', 0.0)
            cloud_lines.append(f"• *{cloud_key.upper()}:* ${cost_val:.2f}" if isinstance(cost_val, (int, float)) else f"• *{cloud_key.upper()}:* ${cost_val}")
            
    if cloud_lines:
        cloud_text = "☁️ *Infrastructure Costs*\n" + "\n".join(cloud_lines)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": cloud_text
            }
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
