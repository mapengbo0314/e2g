"""Utility for cloning GitHub repositories for indexing."""

import logging
import subprocess
import os
from typing import Optional

class GithubCloner:
    """Handles cloning remote repositories to local temporary storage."""

    def clone(self, repo_url: str, destination: str, depth: int = 1) -> bool:
        """Clones a repository to the specified destination.
        
        Args:
            repo_url: The URL of the GitHub repository.
            destination: The local directory to clone into.
            depth: The depth of the shallow clone (default 1).
            
        Returns:
            True if successful, False otherwise.
        """
        logging.info("Cloning %s into %s (depth=%d)...", repo_url, destination, depth)
        
        try:
            # Use git CLI to perform a shallow clone for efficiency.
            cmd = ["git", "clone", "--depth", str(depth), repo_url, destination]
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True
            )
            logging.info("Clone successful: %s", result.stdout.strip())
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Failed to clone repository: %s", e.stderr.strip())
            return False
        except Exception as e:
            logging.error("Unexpected error during clone: %s", str(e))
            return False

    def clone_plan(self, repo_url: str, destination: str) -> str:
        """Returns a human-readable description of the clone operation."""
        return f"git clone --depth 1 {repo_url} {destination}"
