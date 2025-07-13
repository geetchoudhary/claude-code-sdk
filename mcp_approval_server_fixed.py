#!/usr/bin/env python3
"""
MCP approval server with file-based interaction for permissions
"""

from mcp.server.fastmcp import FastMCP
import datetime
import json
import sys
import os
import time
from pathlib import Path

# Create MCP server
mcp = FastMCP("approval-server")

# File-based interaction paths
PENDING_FILE = Path("pending_approval.json")
RESPONSE_FILE = Path("approval_response.txt")

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

def write_pending_approval(tool_name: str, tool_input: dict):
    """Write pending approval to file for external handling"""
    pending_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "status": "pending"
    }
    
    with open(PENDING_FILE, "w") as f:
        json.dump(pending_data, f, indent=2)
    
    # Also write a human-readable prompt
    with open("APPROVAL_NEEDED.txt", "w") as f:
        f.write("="*60 + "\n")
        f.write("🔒 PERMISSION REQUEST\n")
        f.write("="*60 + "\n")
        f.write(f"Tool: {tool_name}\n")
        
        if tool_name == "Bash":
            command = tool_input.get("command", "Unknown command")
            f.write(f"Command: {command}\n")
            for dangerous in DANGEROUS_COMMANDS:
                if dangerous in command:
                    f.write(f"⚠️  WARNING: This command contains '{dangerous}'\n")
        
        elif tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
            file_path = tool_input.get("file_path", "Unknown file")
            f.write(f"File: {file_path}\n")
            if tool_name == "Write":
                f.write("Action: Create or overwrite file\n")
            elif tool_name == "Edit":
                f.write("Action: Modify file contents\n")
        
        elif tool_name == "WebFetch":
            url = tool_input.get("url", "Unknown URL")
            f.write(f"URL: {url}\n")
        
        f.write("\nTo approve: echo 'y' > approval_response.txt\n")
        f.write("To deny: echo 'n' > approval_response.txt\n")
        f.write("To approve all: echo 'a' > approval_response.txt\n")

def get_file_based_decision(tool_name: str, tool_input: dict, timeout: int = 300) -> dict:
    """Wait for file-based approval decision"""
    
    # Clear any existing response file
    if RESPONSE_FILE.exists():
        RESPONSE_FILE.unlink()
    
    # Write the pending approval
    write_pending_approval(tool_name, tool_input)
    
    # Print to stderr so it shows in the MCP server terminal
    print(f"\n⚠️  APPROVAL NEEDED for {tool_name}", file=sys.stderr)
    print(f"Check APPROVAL_NEEDED.txt and respond with:", file=sys.stderr)
    print(f"  echo 'y' > approval_response.txt  # to approve", file=sys.stderr)
    print(f"  echo 'n' > approval_response.txt  # to deny", file=sys.stderr)
    print(f"  echo 'a' > approval_response.txt  # to approve all\n", file=sys.stderr)
    
    # Wait for response
    start_time = time.time()
    while time.time() - start_time < timeout:
        if RESPONSE_FILE.exists():
            try:
                response = RESPONSE_FILE.read_text().strip().lower()
                RESPONSE_FILE.unlink()  # Clean up
                
                if response in ['y', 'yes']:
                    return {
                        "behavior": "allow",
                        "updatedInput": tool_input
                    }
                elif response in ['n', 'no']:
                    return {
                        "behavior": "deny",
                        "message": f"User denied permission for {tool_name}"
                    }
                elif response in ['a', 'all']:
                    # Add to auto-approve
                    if tool_name not in AUTO_APPROVE_PATTERNS:
                        AUTO_APPROVE_PATTERNS[tool_name] = ["*"]
                    return {
                        "behavior": "allow",
                        "updatedInput": tool_input
                    }
            except Exception as e:
                print(f"Error reading response: {e}", file=sys.stderr)
        
        time.sleep(0.5)  # Check every 500ms
    
    # Timeout
    return {
        "behavior": "deny",
        "message": f"Approval timeout ({timeout}s) for {tool_name}"
    }

@mcp.tool()
async def permissions__approve(tool_name: str, input: dict, reason: str = "") -> dict:
    """
    Approve or deny permission requests from Claude.
    
    This uses file-based interaction to avoid stdio conflicts.
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
    
    # If not auto-approved, use file-based decision
    decision = get_file_based_decision(tool_name, input)
    
    # Log the decision
    if decision["behavior"] == "allow":
        log_to_file(f"USER APPROVED: {tool_name}")
    else:
        log_to_file(f"USER DENIED: {tool_name} - {decision.get('message', 'No reason')}")
    
    # Clean up approval files
    if PENDING_FILE.exists():
        PENDING_FILE.unlink()
    if Path("APPROVAL_NEEDED.txt").exists():
        Path("APPROVAL_NEEDED.txt").unlink()
    
    return decision

if __name__ == "__main__":
    # Run as stdio server
    import asyncio
    print("MCP Approval Server (File-based) starting...", file=sys.stderr)
    print("This server uses file-based interaction for approvals", file=sys.stderr)
    print("Watch for APPROVAL_NEEDED.txt files", file=sys.stderr)
    asyncio.run(mcp.run())