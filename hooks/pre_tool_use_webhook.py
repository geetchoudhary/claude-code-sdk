#!/usr/bin/env python3
"""
PreToolUse hook that sends events to the frontend via webhook
Logs tool usage and provides real-time notifications
"""
import json
import sys
import httpx
import asyncio
from typing import Dict, Any
import datetime
import os

FRONTEND_WEBHOOK_URL = "http://localhost:8002/webhook"
LOG_FILE = "logs/pre_tool_use.log"

def log_event(event_data: Dict[str, Any]) -> None:
    """Log event to file for debugging"""
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event": "pre_tool_use",
            "tool_name": event_data.get("tool_name", "unknown"),
            "session_id": event_data.get("session_id", "unknown"),
            "tool_input": event_data.get("tool_input", {}),
            "transcript_path": event_data.get("transcript_path", "")
        }
        
        # Append to log file
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    except Exception as e:
        print(f"Failed to log event: {e}", file=sys.stderr)

async def send_to_frontend(event_data: Dict[str, Any]) -> None:
    """Send PreToolUse event to frontend"""
    try:
        webhook_payload = {
            "event": "pre_tool_use",
            "data": event_data,
            "timestamp": event_data.get("timestamp", ""),
            "session_id": event_data.get("session_id", "")
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FRONTEND_WEBHOOK_URL,
                json=webhook_payload,
                timeout=5.0
            )
            response.raise_for_status()
            
        # Success message to stdout (shown in transcript mode)
        tool_name = event_data.get("tool_name", "unknown")
        print(f"🔥 PreToolUse hook: {tool_name} event sent to frontend")
            
    except Exception as e:
        # Log error but don't fail the hook
        print(f"Failed to send PreToolUse event to frontend: {e}", file=sys.stderr)

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Add timestamp
        input_data["timestamp"] = datetime.datetime.now().isoformat()
        
        # Log the event
        log_event(input_data)
        
        # Send to frontend asynchronously
        asyncio.run(send_to_frontend(input_data))
        
        # Exit successfully
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error in PreToolUse hook: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()