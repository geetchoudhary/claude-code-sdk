"""Configuration management using environment variables."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Configuration
    api_port: int = 8001
    api_server_url: str = "http://localhost:8001"
    webhook_timeout: float = 10.0
    query_timeout: int = 300
    max_retries: int = 3

    # Paths
    project_root: Path = Path("/Users/mastergeet/Repos/claude_test")
    mcp_config_file: str = "mcp-servers.json"

    # Claude SDK Configuration
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-latest"
    claude_max_turns: int = 8
    claude_default_tools: List[str] = ["Read", "Write", "LS", "Task"]

    # CORS Configuration
    cors_origins: List[str] = ["*"]  # In production, specify your frontend URL

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    # Development
    debug: bool = False

    @property
    def mcp_config_path(self) -> Path:
        """Get the full path to MCP configuration file."""
        return self.project_root / self.mcp_config_file

    @property
    def projects_dir(self) -> Path:
        """Get the projects directory path."""
        return self.project_root / "projects"


# Create global settings instance
settings = Settings()