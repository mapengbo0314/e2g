# chat/fetchers/github_stats.py
import requests
import logging

def fetch_github_stats(token: str, repo: str) -> dict:
    if not token or not repo:
        return {"recent_prs_count": 0, "error": "Missing token or repo"}
        
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        # Example: Fetch recent pulls
        resp = requests.get(f"https://api.github.com/repos/{repo}/pulls?state=all&per_page=10", headers=headers)
        if resp.status_code == 200:
            prs = resp.json()
            return {"recent_prs_count": len(prs)}
        else:
            return {"recent_prs_count": 0, "error": f"API error: {resp.status_code}"}
    except Exception as e:
        logging.error(f"GitHub fetch failed: {e}")
        return {"recent_prs_count": 0, "error": str(e)}
