#!/usr/bin/env python3
"""
Demo MCP server with various tools for testing permission system
"""

from mcp.server.fastmcp import FastMCP
import datetime
import sys
from pathlib import Path

# Create MCP server
mcp = FastMCP("demo-server")

@mcp.tool()
async def safe_file_read() -> dict:
    """Read a safe file (should be auto-approved)"""
    try:
        content = Path("README.md").read_text() if Path("README.md").exists() else "File not found"
        return {
            "status": "success",
            "message": "Successfully read README.md",
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading file: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
async def dangerous_file_write() -> dict:
    """Write to a sensitive file (should require approval)"""
    return {
        "status": "would_execute",
        "message": "This would write to /etc/hosts - a sensitive system file",
        "action": "write",
        "target": "/etc/hosts",
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.tool()
async def safe_command() -> dict:
    """Execute a safe command (should be auto-approved)"""
    return {
        "status": "would_execute",
        "message": "This would run: ls -la",
        "command": "ls -la",
        "risk_level": "low",
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.tool()
async def dangerous_command() -> dict:
    """Execute a dangerous command (should be denied)"""
    return {
        "status": "would_execute",
        "message": "This would run: rm -rf /important/data",
        "command": "rm -rf /important/data",
        "risk_level": "critical",
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.tool()
async def test_operation(operation_type: str = "info") -> dict:
    """Generic test operation with configurable behavior"""
    operations = {
        "info": {
            "status": "success",
            "message": "Information retrieved successfully",
            "risk_level": "none"
        },
        "modify": {
            "status": "would_modify",
            "message": "This would modify system settings",
            "risk_level": "medium"
        },
        "delete": {
            "status": "would_delete",
            "message": "This would delete important data",
            "risk_level": "high"
        }
    }
    
    result = operations.get(operation_type, operations["info"])
    result["timestamp"] = datetime.datetime.now().isoformat()
    result["operation_type"] = operation_type
    
    return result

if __name__ == "__main__":
    # Run as stdio server
    import asyncio
    import sys
    print("MCP Demo Server starting...", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    print("  - safe_file_read", file=sys.stderr)
    print("  - dangerous_file_write", file=sys.stderr)
    print("  - safe_command", file=sys.stderr)
    print("  - dangerous_command", file=sys.stderr)
    print("  - test_operation", file=sys.stderr)
    asyncio.run(mcp.run())