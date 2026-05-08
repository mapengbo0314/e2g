import os
from google import genai

def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback to rough estimation if no key (chars / 4)
        return len(text) // 4
    
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens
    except Exception:
        return len(text) // 4
