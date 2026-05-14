# chat/fetchers/github_stats.py
import requests
import logging
from datetime import datetime, timedelta

def fetch_github_stats(token: str, repo: str) -> dict:
    default_stats = {
        "prs_submitted": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "bugs_closed": 0,
        "releases_done": 0
    }
    
    if not token or not repo:
        return {**default_stats, "error": "Missing token or repo"}
        
    try:
        owner, name = repo.split('/')
    except ValueError:
        return {**default_stats, "error": "Invalid repo format. Expected owner/repo"}
        
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    
    query = """
    query($owner: String!, $name: String!, $since: DateTime!) {
      repository(owner: $owner, name: $name) {
        pullRequests(states: MERGED, first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            additions
            deletions
          }
        }
        issues(states: CLOSED, labels: ["bug"], first: 100, filterBy: {since: $since}) {
          totalCount
        }
        releases(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
          totalCount
        }
      }
    }
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"owner": owner, "name": name, "since": seven_days_ago}},
            headers=headers
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                return {**default_stats, "error": f"GraphQL error: {data['errors'][0].get('message', 'Unknown error')}"}
                
            repo_data = data.get("data", {}).get("repository", {})
            if not repo_data:
                return {**default_stats, "error": "Repository not found"}
                
            prs = repo_data.get("pullRequests", {}).get("nodes", [])
            lines_added = sum(pr.get("additions", 0) for pr in prs)
            lines_deleted = sum(pr.get("deletions", 0) for pr in prs)
            
            return {
                "prs_submitted": len(prs),
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "bugs_closed": repo_data.get("issues", {}).get("totalCount", 0),
                "releases_done": repo_data.get("releases", {}).get("totalCount", 0)
            }
        else:
            return {**default_stats, "error": f"API error: {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        logging.error(f"GitHub fetch failed: {e}")
        return {**default_stats, "error": str(e)}
