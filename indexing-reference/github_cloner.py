"""Minimal placeholder for repository cloning workflows."""


class GithubCloner:
    def clone_plan(self, repo_url: str, destination: str) -> str:
        return f"Clone {repo_url} into {destination}"
