# chat/fetchers/ai_usage.py
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional

def fetch_openai_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return {"total_usage": 0, "error": "Missing API key"}
        
    headers = {"Authorization": f"Bearer {api_key}"}
    # For a real implementation, you'd calculate dates. Stubbing for now.
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        resp = requests.get(
            f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}", 
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"total_usage": 0, "error": f"API error: {resp.status_code}"}
    except Exception as e:
        logging.error(f"OpenAI fetch failed: {e}")
        return {"total_usage": 0, "error": str(e)}
