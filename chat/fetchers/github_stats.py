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
        
    seven_days_ago_dt = datetime.utcnow() - timedelta(days=7)
    seven_days_ago = seven_days_ago_dt.isoformat() + "Z"
    
    query = """
    query($owner: String!, $name: String!, $since: DateTime!) {
      repository(owner: $owner, name: $name) {
        pullRequests(states: MERGED, first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            additions
            deletions
            mergedAt
          }
        }
        issues(states: CLOSED, labels: ["bug"], first: 100, filterBy: {since: $since}) {
          totalCount
        }
        releases(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            createdAt
          }
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
                
            # Filter PRs merged within the last 7 days
            prs = repo_data.get("pullRequests", {}).get("nodes", [])
            recent_prs = []
            for pr in prs:
                merged_at_str = pr.get("mergedAt")
                if merged_at_str:
                    # Parse ISO format (handling Z timezone)
                    merged_at = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if merged_at >= seven_days_ago_dt:
                        recent_prs.append(pr)
                        
            lines_added = sum(pr.get("additions", 0) for pr in recent_prs)
            lines_deleted = sum(pr.get("deletions", 0) for pr in recent_prs)
            
            # Filter releases within the last 7 days
            releases = repo_data.get("releases", {}).get("nodes", [])
            recent_releases = 0
            for release in releases:
                created_at_str = release.get("createdAt")
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if created_at >= seven_days_ago_dt:
                        recent_releases += 1
            
            return {
                "prs_submitted": len(recent_prs),
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "bugs_closed": repo_data.get("issues", {}).get("totalCount", 0),
                "releases_done": recent_releases
            }
        else:
            return {**default_stats, "error": f"API error: {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        logging.error(f"GitHub fetch failed: {e}")
        return {**default_stats, "error": str(e)}
