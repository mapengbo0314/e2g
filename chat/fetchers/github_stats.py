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
        pullRequests(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            createdAt
            mergedAt
            additions
            deletions
          }
        }
        issues(states: CLOSED, labels: ["bug"], first: 100, filterBy: {since: $since}) {
          nodes {
            closedAt
          }
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
                
            # Parse PRs for submitted and merged
            prs = repo_data.get("pullRequests", {}).get("nodes", [])
            prs_submitted = 0
            lines_added = 0
            lines_deleted = 0
            
            for pr in prs:
                # Check if submitted in the window
                created_at_str = pr.get("createdAt")
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if created_at >= seven_days_ago_dt:
                        prs_submitted += 1
                        
                # Check if merged in the window
                merged_at_str = pr.get("mergedAt")
                if merged_at_str:
                    merged_at = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if merged_at >= seven_days_ago_dt:
                        lines_added += pr.get("additions", 0)
                        lines_deleted += pr.get("deletions", 0)
                        
            # Parse Issues for closed
            issues = repo_data.get("issues", {}).get("nodes", [])
            bugs_closed = 0
            for issue in issues:
                closed_at_str = issue.get("closedAt")
                if closed_at_str:
                    closed_at = datetime.fromisoformat(closed_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if closed_at >= seven_days_ago_dt:
                        bugs_closed += 1
            
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
                "prs_submitted": prs_submitted,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "bugs_closed": bugs_closed,
                "releases_done": recent_releases
            }
        else:
            return {**default_stats, "error": f"API error: {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        logging.error(f"GitHub fetch failed: {e}")
        return {**default_stats, "error": str(e)}
