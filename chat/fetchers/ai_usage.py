import requests
import logging
from typing import Optional

def _default_stats(error: str = None):
    stats = {"tokens_in": 0, "tokens_out": 0, "prompts": 0, "cost": 0.0, "model": "unknown"}
    if error:
        stats["error"] = error
    return stats

def fetch_openai_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return _default_stats("Missing API key")
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get("https://api.openai.com/v1/dashboard/billing/usage", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "tokens_in": data.get("tokens_in", 0),
                "tokens_out": data.get("tokens_out", 0),
                "prompts": data.get("prompts", 0),
                "cost": data.get("cost", 0.0),
                "model": data.get("model", "gpt-4-turbo")
            }
        return _default_stats(f"API error: {resp.status_code}")
    except Exception as e:
        logging.error(f"OpenAI fetch failed: {e}")
        return _default_stats(str(e))

def fetch_anthropic_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return _default_stats("Missing API key")
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    try:
        resp = requests.get("https://api.anthropic.com/v1/usage", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "tokens_in": data.get("tokens_in", 0),
                "tokens_out": data.get("tokens_out", 0),
                "prompts": data.get("prompts", 0),
                "cost": data.get("cost", 0.0),
                "model": data.get("model", "claude-3-opus")
            }
        return _default_stats(f"API error: {resp.status_code}")
    except Exception as e:
        logging.error(f"Anthropic fetch failed: {e}")
        return _default_stats(str(e))

def fetch_gemini_usage(api_key: Optional[str]) -> dict:
    if not api_key:
        return _default_stats("Missing API key")
    try:
        resp = requests.get(f"https://generativelanguage.googleapis.com/v1beta/usage?key={api_key}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "tokens_in": data.get("tokens_in", 0),
                "tokens_out": data.get("tokens_out", 0),
                "prompts": data.get("prompts", 0),
                "cost": data.get("cost", 0.0),
                "model": data.get("model", "gemini-1.5-pro")
            }
        return _default_stats(f"API error: {resp.status_code}")
    except Exception as e:
        logging.error(f"Gemini fetch failed: {e}")
        return _default_stats(str(e))
