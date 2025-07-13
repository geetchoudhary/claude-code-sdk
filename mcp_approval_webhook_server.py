#!/usr/bin/env python3
"""
MCP approval server with webhook notifications for permissions
"""

from mcp.server.fastmcp import FastMCP
import datetime
import json
import sys
import os
import time
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Optional
import aiohttp
from aiohttp import web
import threading

# Create MCP server
mcp = FastMCP("approval-server")

# Configuration
WEBHOOK_URL = "http://localhost:8002/approval-request"
CALLBACK_PORT = 8083
APPROVAL_TIMEOUT = 300  # 5 minutes

# Store pending approvals
pending_approvals: Dict[str, dict] = {}
approval_responses: Dict[str, dict] = {}

# Configuration for auto-approval patterns
AUTO_APPROVE_PATTERNS = {
    "Read": ["*.py", "*.js", "*.json", "*.md", "*.txt"],
    "Write": ["*.py", "*.js", "*.json"],
    "Edit": ["*.py", "*.js", "*.json"],
    "LS": ["*"],
    "Task": ["*"],
}

# Dangerous commands that always require approval
DANGEROUS_COMMANDS = [
    "rm -rf",
    "sudo",
    "dd if=",
    "format",
    "> /dev/",
    "chmod 777",
    "killall",
    "pkill",
]

def log_to_file(message):
    """Log to file for audit trail"""
    with open("permission_decisions.log", "a") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

def matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file path matches a pattern"""
    import fnmatch
    return fnmatch.fnmatch(file_path, pattern)

def check_auto_approval(tool_name: str, tool_input: dict) -> bool:
    """Check if the tool request should be auto-approved"""
    
    # Check if tool has auto-approval patterns
    if tool_name in AUTO_APPROVE_PATTERNS:
        patterns = AUTO_APPROVE_PATTERNS[tool_name]
        
        # For file-based tools, check file patterns
        if tool_name in ["Read", "Write", "Edit"]:
            file_path = tool_input.get("file_path", "")
            if any(matches_pattern(file_path, pattern) for pattern in patterns):
                return True
        
        # For LS and Task, check patterns
        elif tool_name in ["LS", "Task"]:
            if "*" in patterns:
                return True
    
    # For Bash commands, check for dangerous patterns
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Check dangerous commands
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                return False  # Explicitly deny
        
        # Auto-approve safe commands
        safe_commands = ["ls", "pwd", "echo", "cat", "grep", "find", "git status", "git diff"]
        if any(command.startswith(safe) for safe in safe_commands):
            return True
    
    return False

async def send_webhook_notification(request_id: str, tool_name: str, tool_input: dict):
    """Send approval request to webhook"""
    payload = {
        "request_id": request_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "callback_url": f"http://localhost:{CALLBACK_PORT}/approval-callback"
    }
    
    # Add context for better UI display
    if tool_name == "Bash":
        payload["display_text"] = f"Execute command: {tool_input.get('command', 'Unknown')}"
    elif tool_name in ["Read", "Write", "Edit"]:
        action = {"Read": "Read", "Write": "Create/Overwrite", "Edit": "Modify"}[tool_name]
        payload["display_text"] = f"{action} file: {tool_input.get('file_path', 'Unknown')}"
    elif tool_name == "WebFetch":
        payload["display_text"] = f"Fetch URL: {tool_input.get('url', 'Unknown')}"
    else:
        payload["display_text"] = f"Use tool: {tool_name}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 400:
                    print(f"Webhook notification failed: {resp.status}", file=sys.stderr)
                else:
                    print(f"Webhook notification sent for {tool_name}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to send webhook: {e}", file=sys.stderr)

async def wait_for_approval(request_id: str, timeout: int = APPROVAL_TIMEOUT) -> Optional[dict]:
    """Wait for approval response"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if request_id in approval_responses:
            response = approval_responses.pop(request_id)
            return response
        
        await asyncio.sleep(0.5)
    
    return None

# Callback server for receiving approval decisions
async def handle_approval_callback(request):
    """Handle approval callback from webhook service"""
    try:
        data = await request.json()
        request_id = data.get("request_id")
        decision = data.get("decision")
        reason = data.get("reason", "")
        
        if request_id and decision:
            approval_responses[request_id] = {
                "decision": decision,
                "reason": reason,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            print(f"Received approval decision for {request_id}: {decision}", file=sys.stderr)
            return web.json_response({"status": "received"})
        else:
            return web.json_response({"error": "Missing request_id or decision"}, status=400)
    
    except Exception as e:
        print(f"Error handling callback: {e}", file=sys.stderr)
        return web.json_response({"error": str(e)}, status=500)

# Start callback server in background
callback_app = web.Application()
callback_app.router.add_post('/approval-callback', handle_approval_callback)

async def start_callback_server():
    """Start the callback server"""
    runner = web.AppRunner(callback_app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', CALLBACK_PORT)
    await site.start()
    print(f"Callback server started on port {CALLBACK_PORT}", file=sys.stderr)

@mcp.tool()
async def permissions__approve(tool_name: str, input: dict, reason: str = "") -> dict:
    """
    Approve or deny permission requests from Claude.
    
    This uses webhook notifications to get approval decisions.
    """
    
    # Log the request
    log_to_file(f"PERMISSION REQUEST: tool_name={tool_name}, input={json.dumps(input)}")
    
    # First check auto-approval rules
    if check_auto_approval(tool_name, input):
        log_to_file(f"AUTO-APPROVED: {tool_name}")
        return {
            "behavior": "allow",
            "updatedInput": input
        }
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Send webhook notification
    print(f"\n⚠️  APPROVAL NEEDED for {tool_name}", file=sys.stderr)
    print(f"Sending webhook notification to port 8082...", file=sys.stderr)
    
    await send_webhook_notification(request_id, tool_name, input)
    
    # Wait for approval response
    response = await wait_for_approval(request_id)
    
    if response:
        decision = response["decision"]
        if decision == "allow":
            log_to_file(f"WEBHOOK APPROVED: {tool_name}")
            return {
                "behavior": "allow",
                "updatedInput": input
            }
        else:
            log_to_file(f"WEBHOOK DENIED: {tool_name} - {response.get('reason', 'No reason')}")
            return {
                "behavior": "deny",
                "message": f"Permission denied: {response.get('reason', 'User denied permission')}"
            }
    else:
        # Timeout
        log_to_file(f"APPROVAL TIMEOUT: {tool_name}")
        return {
            "behavior": "deny",
            "message": f"Approval timeout ({APPROVAL_TIMEOUT}s) for {tool_name}"
        }

async def main():
    """Main entry point"""
    # Start callback server
    await start_callback_server()
    
    # Run MCP server
    print("MCP Approval Server (Webhook-based) starting...", file=sys.stderr)
    print(f"Webhook notifications will be sent to: {WEBHOOK_URL}", file=sys.stderr)
    print(f"Callback server listening on port: {CALLBACK_PORT}", file=sys.stderr)
    
    # Keep the server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)

if __name__ == "__main__":
    # Run the MCP server directly since it handles stdio
    import sys
    
    # Start callback server in a thread
    def run_callback_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_callback_server())
        loop.run_forever()
    
    import threading
    callback_thread = threading.Thread(target=run_callback_server, daemon=True)
    callback_thread.start()
    
    print("MCP Approval Server (Webhook-based) starting...", file=sys.stderr)
    print(f"Webhook notifications will be sent to: {WEBHOOK_URL}", file=sys.stderr)
    print(f"Callback server listening on port: {CALLBACK_PORT}", file=sys.stderr)
    
    # Run MCP server (it will handle its own event loop)
    asyncio.run(mcp.run())