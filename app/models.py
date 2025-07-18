"""Pydantic models for request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Query Models
class QueryRequest(BaseModel):
    """Request model for submitting a query."""

    prompt: str
    session_id: Optional[str] = Field(default=None, description="Resume a previous session")
    conversation_id: Optional[str] = Field(
        default=None, description="Frontend conversation grouping ID"
    )
    webhook_url: str = Field(description="URL to notify when query completes")
    organization_name: str = Field(description="Organization name for project context")
    project_path: str = Field(description="Project path within organization")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional options for Claude"
    )


class QueryResponse(BaseModel):
    """Response model for query submission."""

    task_id: str
    status: str = "accepted"


class WebhookPayload(BaseModel):
    """Webhook notification payload."""

    task_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime


# MCP Models
class MCPServer(BaseModel):
    """MCP server information."""

    id: str
    name: str
    command: str
    args: List[str]
    connected: bool = False
    icon: Optional[str] = None
    description: Optional[str] = None
    env_vars: Optional[List[str]] = None


class MCPServerCommandConfig(BaseModel):
    """MCP server command configuration."""

    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class CustomConnectorRequest(BaseModel):
    """Custom MCP connector configuration."""

    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None


# MCP Server Enum
class MCPServerType(str, Enum):
    """Supported MCP server types."""
    
    APPROVAL_SERVER = "approval-server"
    CONTEXT_MANAGER = "context-manager"
    CONTEXT7 = "context7"
    FIGMA = "figma"
    GITHUB = "github"


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    
    server_type: MCPServerType = Field(description="Type of MCP server")
    access_token: Optional[str] = Field(default=None, description="Access token for servers that require authentication")


# Project Models
class AIInstructionFiles(BaseModel):
    """Configuration for AI instruction files to create."""

    create_claude_md: bool = Field(default=True, description="Create CLAUDE.md using Claude Code SDK")
    create_ai_dos_and_donts: bool = Field(default=True, description="Create AI_DOS_AND_DONTS.md")
    create_ai_figma_to_code: bool = Field(default=True, description="Create AI_FIGMA_TO_CODE.md")
    create_ai_coding_rules: bool = Field(default=True, description="Create AI_CODING_RULES.md")
    update_claude_md: bool = Field(default=True, description="Update CLAUDE.md with references")


class InitProjectRequest(BaseModel):
    """Request model for project initialization."""

    organization_name: str = Field(description="Organization name for project directory structure")
    project_path: str = Field(description="Project path within organization directory")
    github_repo_url: str = Field(description="GitHub repository URL to clone")
    webhook_url: str = Field(description="Webhook URL for notifications")
    mcp_servers: Optional[List[MCPServerConfig]] = Field(
        default=None, description="List of MCP servers to enable for the project"
    )


# Project Initialization Models
class ProjectInitStatus(str, Enum):
    """Project initialization status."""
    
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProjectInitWebhookPayload(BaseModel):
    """Webhook payload for project initialization steps."""
    
    task_id: str
    task: str = "INIT_PROJECT"
    step_name: str
    completion_message: str
    status: ProjectInitStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class InitProjectResponse(BaseModel):
    """Response model for project initialization."""
    
    task_id: str
    status: str = "accepted"
    message: str = "Project initialization started"


# Session Models
class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    created_at: datetime
    last_used: datetime
    query_count: int
    total_tokens: int
    tools_used: List[str]
    status: str


class SessionStats(BaseModel):
    """Overall session statistics."""

    active_sessions: int
    total_queries: int
    sessions_by_status: Dict[str, int]


# Metrics Models
class PerformanceStats(BaseModel):
    """Performance statistics."""

    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float
    average_duration: float
    average_messages_per_query: float


class MetricsResponse(BaseModel):
    """Metrics endpoint response."""

    session_stats: SessionStats
    performance_stats: PerformanceStats
    active_queries: int
    timestamp: datetime