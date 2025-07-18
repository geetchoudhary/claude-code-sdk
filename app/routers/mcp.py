"""MCP (Model Context Protocol) server endpoint routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
import structlog

from app.models import CustomConnectorRequest, MCPServer
from app.services.mcp_integration import (
    connect_mcp_server,
    disconnect_mcp_server,
    get_available_mcp_servers,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/servers", response_model=List[MCPServer])
async def list_mcp_servers():
    """List all available MCP servers and their connection status."""
    return get_available_mcp_servers()


@router.post("/connect/{server_id}")
async def connect_server(server_id: str, custom_config: Optional[CustomConnectorRequest] = None):
    """Connect to an MCP server."""
    try:
        custom_config_dict = custom_config.model_dump() if custom_config else None
        result = connect_mcp_server(server_id, custom_config_dict)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to connect MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disconnect/{server_id}")
async def disconnect_server(server_id: str):
    """Disconnect from an MCP server."""
    try:
        result = disconnect_mcp_server(server_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to disconnect MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))