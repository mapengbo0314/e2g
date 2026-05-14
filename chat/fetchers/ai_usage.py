import requests
import logging
from datetime import datetime, timedelta
from typing import Optional

def fetch_openai_usage(api_key: Optional[str]) -> dict:
    default_stats = {
        "tokens_consumed": 0,
        "cost": 0.0,
        "prompt_count": "N/A",
        "status": "error"
    }
    
    if not api_key:
        default_stats["error"] = "Missing API key"
        return default_stats
        
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
            data = resp.json()
            total_usage_cents = data.get("total_usage", 0)
            return {
                "tokens_consumed": 0,
                "cost": total_usage_cents / 100.0,
                "prompt_count": "N/A",
                "status": "success"
            }
        else:
            default_stats["error"] = f"API error: {resp.status_code}"
            return default_stats
    except Exception as e:
        logging.error(f"OpenAI fetch failed: {e}")
        default_stats["error"] = str(e)
        return default_stats

def fetch_anthropic_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return {
            "tokens_consumed": 0,
            "cost": 0.0,
            "prompt_count": "N/A",
            "status": "error",
            "error": "Missing API key"
        }
    return {
        "tokens_consumed": 0,
        "cost": 0.0,
        "prompt_count": "N/A",
        "status": "API unsupported"
    }

def fetch_gemini_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return {
            "tokens_consumed": 0,
            "cost": 0.0,
            "prompt_count": "N/A",
            "status": "error",
            "error": "Missing API key"
        }
    return {
        "tokens_consumed": 0,
        "cost": 0.0,
        "prompt_count": "N/A",
        "status": "API unsupported"
    }
