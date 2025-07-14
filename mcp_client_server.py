#!/usr/bin/env python3
"""
MCP Client Server - Exposes MCP client functionality via HTTP API
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="MCP Client Server", version="1.0.0")

# Global storage for MCP sessions
mcp_sessions: Dict[str, ClientSession] = {}
mcp_processes: Dict[str, subprocess.Popen] = {}


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    command: str
    args: List[str] = []
    env: Optional[Dict[str, str]] = None


class ConnectRequest(BaseModel):
    """Request to connect to an MCP server"""
    session_id: str
    server_config: MCPServerConfig


class DisconnectRequest(BaseModel):
    """Request to disconnect from an MCP server"""
    session_id: str


class ListToolsRequest(BaseModel):
    """Request to list available tools"""
    session_id: str


class CallToolRequest(BaseModel):
    """Request to call a tool"""
    session_id: str
    tool_name: str
    arguments: Dict[str, Any] = {}


class ListResourcesRequest(BaseModel):
    """Request to list available resources"""
    session_id: str


class ReadResourceRequest(BaseModel):
    """Request to read a resource"""
    session_id: str
    uri: str


class ListPromptsRequest(BaseModel):
    """Request to list available prompts"""
    session_id: str


class GetPromptRequest(BaseModel):
    """Request to get a prompt"""
    session_id: str
    name: str
    arguments: Dict[str, Any] = {}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "MCP Client Server",
        "version": "1.0.0",
        "description": "HTTP API for interacting with MCP servers",
        "endpoints": {
            "POST /connect": "Connect to an MCP server",
            "POST /disconnect": "Disconnect from an MCP server",
            "POST /list-tools": "List available tools",
            "POST /call-tool": "Call a tool",
            "POST /list-resources": "List available resources",
            "POST /read-resource": "Read a resource",
            "POST /list-prompts": "List available prompts",
            "POST /get-prompt": "Get a prompt",
            "GET /sessions": "List active sessions"
        }
    }


@app.post("/connect")
async def connect_to_server(request: ConnectRequest):
    """Connect to an MCP server"""
    session_id = request.session_id
    config = request.server_config
    
    if session_id in mcp_sessions:
        raise HTTPException(status_code=400, detail=f"Session {session_id} already exists")
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env
        )
        
        # Start the MCP server process and create client session
        session = await stdio_client(server_params)
        
        # Initialize the session
        await session.__aenter__()
        
        # Store the session
        mcp_sessions[session_id] = session
        
        # Get server information
        server_info = {
            "name": session.server.name if session.server else "Unknown",
            "version": session.server.version if session.server else "Unknown"
        }
        
        return {
            "status": "connected",
            "session_id": session_id,
            "server_info": server_info
        }
        
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect")
async def disconnect_from_server(request: DisconnectRequest):
    """Disconnect from an MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        # Close the session
        session = mcp_sessions[session_id]
        await session.__aexit__(None, None, None)
        
        # Remove from storage
        del mcp_sessions[session_id]
        
        return {"status": "disconnected", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Failed to disconnect from MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions = []
    for session_id, session in mcp_sessions.items():
        sessions.append({
            "session_id": session_id,
            "server_name": session.server.name if session.server else "Unknown",
            "server_version": session.server.version if session.server else "Unknown"
        })
    return {"sessions": sessions}


@app.post("/list-tools")
async def list_tools(request: ListToolsRequest):
    """List available tools from the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.list_tools()
        
        tools = []
        for tool in result.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        return {"tools": tools}
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call-tool")
async def call_tool(request: CallToolRequest):
    """Call a tool on the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.call_tool(
            name=request.tool_name,
            arguments=request.arguments
        )
        
        # Convert the result to a serializable format
        if result.content:
            content = []
            for item in result.content:
                if hasattr(item, 'text'):
                    content.append({"type": "text", "text": item.text})
                else:
                    content.append({"type": "unknown", "data": str(item)})
        else:
            content = []
        
        return {
            "tool_name": request.tool_name,
            "arguments": request.arguments,
            "result": content,
            "is_error": result.isError if hasattr(result, 'isError') else False
        }
        
    except Exception as e:
        logger.error(f"Failed to call tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/list-resources")
async def list_resources(request: ListResourcesRequest):
    """List available resources from the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.list_resources()
        
        resources = []
        for resource in result.resources:
            resources.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mimeType
            })
        
        return {"resources": resources}
        
    except Exception as e:
        logger.error(f"Failed to list resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/read-resource")
async def read_resource(request: ReadResourceRequest):
    """Read a resource from the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.read_resource(uri=request.uri)
        
        # Convert the contents to a serializable format
        contents = []
        for item in result.contents:
            if hasattr(item, 'text'):
                contents.append({"type": "text", "text": item.text, "uri": item.uri})
            elif hasattr(item, 'blob'):
                contents.append({"type": "blob", "data": item.blob, "uri": item.uri})
            else:
                contents.append({"type": "unknown", "data": str(item)})
        
        return {
            "uri": request.uri,
            "contents": contents
        }
        
    except Exception as e:
        logger.error(f"Failed to read resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/list-prompts")
async def list_prompts(request: ListPromptsRequest):
    """List available prompts from the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.list_prompts()
        
        prompts = []
        for prompt in result.prompts:
            prompts.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments if hasattr(prompt, 'arguments') else []
            })
        
        return {"prompts": prompts}
        
    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-prompt")
async def get_prompt(request: GetPromptRequest):
    """Get a prompt from the MCP server"""
    session_id = request.session_id
    
    if session_id not in mcp_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        session = mcp_sessions[session_id]
        result = await session.get_prompt(
            name=request.name,
            arguments=request.arguments
        )
        
        # Convert messages to serializable format
        messages = []
        for msg in result.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return {
            "name": request.name,
            "arguments": request.arguments,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all sessions on shutdown"""
    for session_id in list(mcp_sessions.keys()):
        try:
            session = mcp_sessions[session_id]
            await session.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")


if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)