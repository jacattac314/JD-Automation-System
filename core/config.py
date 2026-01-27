"""
Core configuration and secrets management for JD Automation System.

Handles loading environment variables and secure credential storage.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import keyring
from loguru import logger

# Load environment variables
load_dotenv()

class Config:
    """Central configuration management."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.project_storage = Path(os.getenv("PROJECT_STORAGE_PATH", "./projects"))

        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.project_storage.mkdir(exist_ok=True)

        # API Keys (prefer keyring, fallback to env)
        self.gemini_api_key = self._get_secret("GEMINI_API_KEY")
        self.github_token = self._get_secret("GITHUB_TOKEN")
        self.github_username = os.getenv("GITHUB_USERNAME", "")
        self.anthropic_api_key = self._get_secret("ANTHROPIC_API_KEY")

        # Settings
        self.default_repo_visibility = os.getenv("DEFAULT_REPO_VISIBILITY", "private")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.claude_code_path = os.getenv("CLAUDE_CODE_PATH", "claude")
        self.code_execution_timeout = int(os.getenv("CODE_EXECUTION_TIMEOUT", "600"))

    def _get_secret(self, key: str) -> str:
        """Get secret from keyring or environment variable."""
        try:
            # Try keyring first
            secret = keyring.get_password("jd_automation", key)
            if secret:
                return secret
        except Exception as e:
            logger.debug(f"Keyring not available for {key}: {e}")

        # Fallback to environment variable
        return os.getenv(key, "")

    def set_secret(self, key: str, value: str):
        """Store secret in keyring."""
        try:
            keyring.set_password("jd_automation", key, value)
            logger.info(f"Stored {key} in keyring")
        except Exception as e:
            logger.warning(f"Could not store {key} in keyring: {e}")

    def validate(self) -> tuple[bool, list[str]]:
        """Validate that required configuration is present."""
        errors = []

        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required")

        if not self.github_token:
            errors.append("GITHUB_TOKEN is required")

        if not self.github_username:
            errors.append("GITHUB_USERNAME is required")

        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")

        return len(errors) == 0, errors

# Global config instance
config = Config()
