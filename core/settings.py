"""
Application settings using Pydantic BaseSettings.

Loads configuration from environment variables and .env files.
Supports separate dev/staging/production configurations.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = Field(default="development", description="development | staging | production")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/jd_automation.db",
        description="Database connection URL. Use postgresql://... for production."
    )

    # Redis (optional, for caching and rate limiting)
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")

    # Authentication
    jwt_secret: str = Field(
        default="dev-secret-change-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_expiry_hours: int = Field(default=24, description="JWT token expiry in hours")
    github_client_id: Optional[str] = Field(default=None, description="GitHub OAuth App client ID")
    github_client_secret: Optional[str] = Field(default=None, description="GitHub OAuth App client secret")

    # API Keys (platform-provided for SaaS)
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    # GitHub (for platform operations)
    github_token: Optional[str] = Field(default=None, description="GitHub PAT for platform operations")
    github_username: Optional[str] = Field(default=None, description="GitHub username")

    # Application
    project_storage_path: str = Field(default="./projects", description="Local project storage directory")
    log_level: str = Field(default="INFO", description="Logging level")
    claude_code_path: str = Field(default="claude", description="Path to Claude Code CLI")
    code_execution_timeout: int = Field(default=600, description="Claude Code execution timeout in seconds")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins. Use specific origins in production."
    )

    # Rate limiting
    rate_limit_runs_per_day: int = Field(default=10, description="Max pipeline runs per user per day")

    # Server
    host: str = Field(default="127.0.0.1", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")

    @property
    def project_storage(self) -> Path:
        return Path(self.project_storage_path)

    @property
    def cors_origin_list(self) -> list:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
