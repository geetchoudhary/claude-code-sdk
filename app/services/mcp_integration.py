"""MCP (Model Context Protocol) server integration and management."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.models import MCPServer

logger = structlog.get_logger(__name__)


def get_mcp_config() -> Optional[Dict[str, Any]]:
    """Get MCP configuration from mcp-servers.json."""
    if settings.mcp_config_path.exists():
        with open(settings.mcp_config_path) as f:
            return json.load(f)
    return None


def save_mcp_config(config: Dict[str, Any]):
    """Save MCP configuration to mcp-servers.json."""
    with open(settings.mcp_config_path, "w") as f:
        json.dump(config, f, indent=2)


def get_available_mcp_servers() -> List[MCPServer]:
    """Get list of available MCP servers with their connection status."""
    # Predefined MCP servers that can be connected
    available_servers = [
        MCPServer(
            id="context-manager",
            name="Context Manager",
            command="npx",
            args=["mcp-context-manager"],
            icon="📋",
            description="Manage context across conversations",
        ),
        MCPServer(
            id="context7",
            name="Context7",
            command="npx",
            args=["-y", "@upstash/context7-mcp"],
            icon="📚",
            description="Access documentation and code examples",
        ),
        MCPServer(
            id="github",
            name="GitHub",
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server",
            ],
            icon="https://github.githubassets.com/favicon.ico",
            description="Access GitHub repositories and issues",
            env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"],
        ),
        MCPServer(
            id="figma",
            name="Figma",
            command="npx",
            args=["-y", "figma-developer-mcp"],
            icon="https://static.figma.com/app/icon/1/favicon.svg",
            description="Access Figma designs and components",
            env_vars=["FIGMA_API_KEY"],
        ),
    ]

    # Check current configuration to see which are connected
    current_config = get_mcp_config()
    if current_config and "mcpServers" in current_config:
        connected_ids = set()
        for server_id, config in current_config["mcpServers"].items():
            # Skip the approval server
            if server_id == "approval-server":
                continue

            connected_ids.add(server_id)

            # If this server is not in our predefined list, add it as a custom server
            if not any(s.id == server_id for s in available_servers):
                custom_server = MCPServer(
                    id=server_id,
                    name=server_id.replace("-", " ").title(),
                    command=config.get("command", ""),
                    args=config.get("args", []),
                    connected=True,
                    icon="🔧",  # Custom connector icon
                    description="Custom MCP connector",
                )
                available_servers.append(custom_server)

        # Update connection status for predefined servers
        for server in available_servers:
            if server.id in connected_ids:
                server.connected = True

    return available_servers


def connect_mcp_server(
    server_id: str, custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Connect to an MCP server."""
    # Get current configuration
    config = get_mcp_config() or {"mcpServers": {}}

    # Always keep approval server
    if "approval-server" not in config["mcpServers"]:
        config["mcpServers"]["approval-server"] = {
            "command": "python",
            "args": ["mcp_approval_webhook_server.py"],
        }

    # Check if this is a custom connector (has command and args)
    if custom_config and custom_config.get("command") and custom_config.get("args"):
        # Use custom configuration provided
        server_config = {
            "command": custom_config["command"],
            "args": custom_config["args"],
        }
        if custom_config.get("env"):
            server_config["env"] = custom_config["env"]
        config["mcpServers"][server_id] = server_config
    else:
        # Find the server in predefined list
        available_servers = get_available_mcp_servers()
        server = next((s for s in available_servers if s.id == server_id), None)

        if not server:
            raise ValueError(f"MCP server '{server_id}' not found")

        # Add the server configuration
        server_config = {
            "command": server.command,
            "args": server.args.copy(),  # Copy to avoid modifying original
        }

        # Special handling for Figma
        if (
            server_id == "figma"
            and custom_config
            and custom_config.get("env")
            and "FIGMA_API_KEY" in custom_config["env"]
        ):
            server_config["args"].extend(
                [
                    f"--figma-api-key={custom_config['env']['FIGMA_API_KEY']}",
                    "--stdio",
                ]
            )
        else:
            # Add env if provided in request for other servers
            if custom_config and custom_config.get("env"):
                server_config["env"] = custom_config["env"]

        config["mcpServers"][server_id] = server_config

    # Save configuration
    save_mcp_config(config)
    logger.info(f"Connected MCP server: {server_id}")

    return {"status": "connected", "server_id": server_id}


def disconnect_mcp_server(server_id: str) -> Dict[str, Any]:
    """Disconnect from an MCP server."""
    config = get_mcp_config()
    if not config or "mcpServers" not in config:
        raise ValueError("No MCP configuration found")

    if server_id not in config["mcpServers"]:
        raise ValueError(f"MCP server '{server_id}' not connected")

    # Don't allow disconnecting the approval server
    if server_id == "approval-server":
        raise ValueError("Cannot disconnect approval server")

    # Remove the server from configuration
    del config["mcpServers"][server_id]

    # Save configuration
    save_mcp_config(config)
    logger.info(f"Disconnected MCP server: {server_id}")

    return {"status": "disconnected", "server_id": server_id}