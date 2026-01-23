"""
GitHub Integration Module.

Handles repository creation, management, and publishing.
"""

import re
from pathlib import Path
from github import Github, GithubException
from loguru import logger
from typing import Dict, Any

from core.config import config


class GitHubService:
    """Manages GitHub repository operations."""
    
    def __init__(self):
        if not config.github_token:
            raise ValueError("GitHub token not configured")
        
        self.client = Github(config.github_token)
        self.user = self.client.get_user()
        
    def create_repository(self, project_name: str, description: str) -> Dict[str, Any]:
        """
        Create a new GitHub repository.
        
        Args:
            project_name: Name of the project
            description: Project description
            
        Returns:
            Repository information dict
        """
        # Sanitize repo name
        repo_name = self._sanitize_repo_name(project_name)
        
        # Check if repo exists, append number if needed
        base_name = repo_name
        counter = 1
        while self._repo_exists(repo_name):
            repo_name = f"{base_name}-{counter}"
            counter += 1
        
        logger.info(f"Creating repository: {repo_name}")
        
        try:
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=(config.default_repo_visibility == "private"),
                auto_init=False  # We'll initialize locally
            )
            
            return {
                "name": repo_name,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "full_name": repo.full_name
            }
            
        except GithubException as e:
            logger.error(f"Failed to create repository: {e}")
            raise
    
    def publish_project(self, local_path: Path, repo_info: Dict[str, Any]):
        """
        Publish local project to GitHub.

        Args:
            local_path: Path to local project directory
            repo_info: Repository information from create_repository
        """
        import subprocess
        import os

        logger.info(f"Publishing project to {repo_info['url']}")

        try:
            # Initialize git if not already
            if not (local_path / ".git").exists():
                subprocess.run(["git", "init"], cwd=local_path, check=True, capture_output=True)
                subprocess.run(["git", "branch", "-M", "main"], cwd=local_path, check=True, capture_output=True)

            # Add remote
            try:
                subprocess.run(
                    ["git", "remote", "add", "origin", repo_info['clone_url']],
                    cwd=local_path,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                # Remote might already exist
                subprocess.run(
                    ["git", "remote", "set-url", "origin", repo_info['clone_url']],
                    cwd=local_path,
                    check=True,
                    capture_output=True
                )

            # Add all files
            subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)

            # Commit
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: AI-generated project from JD automation"],
                cwd=local_path,
                check=True,
                capture_output=True
            )

            # Push using GIT_ASKPASS to securely provide credentials
            # This avoids exposing the token in URLs, command line args, or logs
            env = os.environ.copy()
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = self.user.login
            env["GIT_PASSWORD"] = config.github_token

            # Use credential helper via environment to avoid token in URL
            result = subprocess.run(
                ["git", "-c", f"credential.helper=!f() {{ echo username={self.user.login}; echo password={config.github_token}; }}; f",
                 "push", "-u", "origin", "main"],
                cwd=local_path,
                check=True,
                capture_output=True,
                env=env
            )

            logger.info(f"Successfully published to {repo_info['url']}")

        except subprocess.CalledProcessError as e:
            # Log error without exposing sensitive data
            error_msg = e.stderr.decode() if e.stderr else str(e)
            # Sanitize any accidental token leakage in error messages
            if config.github_token and config.github_token in error_msg:
                error_msg = error_msg.replace(config.github_token, "[REDACTED]")
            logger.error(f"Failed to publish: {error_msg}")
            raise RuntimeError(f"Git push failed: {error_msg}") from e
    
    def _sanitize_repo_name(self, name: str) -> str:
        """Sanitize project name to valid GitHub repo name."""
        # Convert to lowercase
        name = name.lower()
        
        # Replace spaces and special chars with hyphens
        name = re.sub(r'[^a-z0-9-]', '-', name)
        
        # Remove consecutive hyphens
        name = re.sub(r'-+', '-', name)
        
        # Remove leading/trailing hyphens
        name = name.strip('-')
        
        # Limit length
        name = name[:100]
        
        return name or "generated-project"
    
    def _repo_exists(self, repo_name: str) -> bool:
        """Check if repository already exists."""
        try:
            self.user.get_repo(repo_name)
            return True
        except GithubException:
            return False
