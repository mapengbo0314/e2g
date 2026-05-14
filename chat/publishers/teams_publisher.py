# chat/publishers/teams_publisher.py
import requests
import logging

def publish_to_teams(webhook_url: str, report_data: dict) -> bool:
    if not webhook_url:
        logging.error("Missing Teams webhook URL")
        return False
        
    try:
        resp = requests.post(webhook_url, json=report_data, timeout=10)
        # Teams Power Automate webhooks often return 202 Accepted
        if resp.status_code in (200, 202):
            return True
        else:
            logging.error(f"Teams webhook error: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logging.error(f"Failed to post to Teams: {e}")
        return False
