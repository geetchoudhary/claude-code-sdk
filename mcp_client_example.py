#!/usr/bin/env python3
"""
Example usage of the MCP Client Server
"""

import asyncio
import httpx
import json

# Server base URL
BASE_URL = "http://localhost:8000"

async def main():
    """Example of using the MCP Client Server"""
    async with httpx.AsyncClient() as client:
        # 1. Check server status
        print("1. Checking server status...")
        response = await client.get(f"{BASE_URL}/")
        print(json.dumps(response.json(), indent=2))
        
        # 2. Connect to an MCP server (example with filesystem server)
        print("\n2. Connecting to MCP server...")
        connect_data = {
            "session_id": "demo-session",
            "server_config": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
        
        try:
            response = await client.post(f"{BASE_URL}/connect", json=connect_data)
            print(json.dumps(response.json(), indent=2))
        except httpx.HTTPStatusError as e:
            print(f"Connection failed: {e}")
            return
        
        # 3. List available tools
        print("\n3. Listing available tools...")
        list_tools_data = {"session_id": "demo-session"}
        response = await client.post(f"{BASE_URL}/list-tools", json=list_tools_data)
        tools = response.json()
        print(json.dumps(tools, indent=2))
        
        # 4. Call a tool (example: read directory)
        if tools.get("tools"):
            print("\n4. Calling a tool...")
            call_tool_data = {
                "session_id": "demo-session",
                "tool_name": "read_file",  # Adjust based on available tools
                "arguments": {"path": "/tmp/test.txt"}
            }
            
            try:
                response = await client.post(f"{BASE_URL}/call-tool", json=call_tool_data)
                print(json.dumps(response.json(), indent=2))
            except httpx.HTTPStatusError as e:
                print(f"Tool call failed: {e}")
        
        # 5. List resources
        print("\n5. Listing resources...")
        list_resources_data = {"session_id": "demo-session"}
        response = await client.post(f"{BASE_URL}/list-resources", json=list_resources_data)
        print(json.dumps(response.json(), indent=2))
        
        # 6. Disconnect
        print("\n6. Disconnecting...")
        disconnect_data = {"session_id": "demo-session"}
        response = await client.post(f"{BASE_URL}/disconnect", json=disconnect_data)
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())