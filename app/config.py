"""Configuration management using environment variables.

Environment Variables:
    # API Configuration
    API_PORT: Server port (default: 8001)
    API_SERVER_URL: Server URL (default: http://localhost:8001)
    WEBHOOK_TIMEOUT: Webhook timeout in seconds (default: 10.0)
    QUERY_TIMEOUT: Query timeout in seconds (default: 300)
    MAX_RETRIES: Max retry attempts (default: 3)

    # Claude SDK Configuration
    CLAUDE_API_KEY: Your Claude API key
    CLAUDE_MODEL: Claude model to use (default: claude-3-5-sonnet-latest)
    CLAUDE_MAX_TURNS: Max conversation turns (default: 8)

    # MCP Approval Server Configuration
    APPROVAL_WEBHOOK_URL: Webhook URL for approval requests (default: http://localhost:8000/api/approval-request)
    APPROVAL_CALLBACK_HOST: Callback host for approval responses (default: host.docker.internal)
                           Use 'localhost' for local development
                           Use 'host.docker.internal' for Docker environments
                           Use your actual domain/IP for production
    APPROVAL_CALLBACK_PORT_BASE: Base port for approval callback server (default: 8083)
    APPROVAL_TIMEOUT: Timeout for approval requests in seconds (default: 300)

    # Logging & Development
    LOG_LEVEL: Logging level (default: INFO)
    LOG_JSON: Use JSON logging (default: true)
    DEBUG: Enable debug mode (default: false)
"""

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
    project_root: Path = Path.cwd()
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

    # MCP Approval Server Configuration
    approval_webhook_url: str = "http://localhost:8000/api/approval-request"
    approval_callback_host: str = "host.docker.internal"
    approval_callback_port_base: int = 8083
    approval_timeout: int = 300  # 5 minutes

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