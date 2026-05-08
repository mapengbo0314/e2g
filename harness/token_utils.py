import os
from google import genai

_CLIENT_CACHE = {}

def get_client(api_key: str) -> genai.Client:
    """Returns a cached genai.Client instance for the given API key."""
    if api_key not in _CLIENT_CACHE:
        _CLIENT_CACHE[api_key] = genai.Client(api_key=api_key)
    return _CLIENT_CACHE[api_key]

def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    if not text:
        return 0

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback to rough estimation if no key (chars / 4, min 1 for non-empty)
        return max(1, len(text) // 4)
    
    try:
        client = get_client(api_key)
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens
    except Exception:
        return max(1, len(text) // 4)
