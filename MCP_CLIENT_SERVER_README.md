# MCP Client Server

A Python HTTP server that exposes MCP (Model Context Protocol) client functionality through a RESTful API.

## Features

- Connect to any MCP server via stdio
- List and call tools
- List and read resources  
- List and get prompts
- Manage multiple concurrent sessions

## Installation

1. Install required dependencies:
```bash
pip install fastapi uvicorn mcp httpx
```

2. Run the server:
```bash
python mcp_client_server.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Root Information
- `GET /` - Get API information and available endpoints

### Session Management
- `POST /connect` - Connect to an MCP server
- `POST /disconnect` - Disconnect from an MCP server
- `GET /sessions` - List all active sessions

### Tools
- `POST /list-tools` - List available tools
- `POST /call-tool` - Call a specific tool

### Resources
- `POST /list-resources` - List available resources
- `POST /read-resource` - Read a specific resource

### Prompts
- `POST /list-prompts` - List available prompts
- `POST /get-prompt` - Get a specific prompt

## Usage Example

### 1. Connect to an MCP Server

```python
import httpx

# Connect to a filesystem MCP server
connect_data = {
    "session_id": "my-session",
    "server_config": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    }
}

response = httpx.post("http://localhost:8000/connect", json=connect_data)
```

### 2. List Available Tools

```python
list_tools_data = {"session_id": "my-session"}
response = httpx.post("http://localhost:8000/list-tools", json=list_tools_data)
tools = response.json()
```

### 3. Call a Tool

```python
call_tool_data = {
    "session_id": "my-session",
    "tool_name": "read_file",
    "arguments": {"path": "/path/to/file.txt"}
}

response = httpx.post("http://localhost:8000/call-tool", json=call_tool_data)
result = response.json()
```

### 4. Disconnect

```python
disconnect_data = {"session_id": "my-session"}
response = httpx.post("http://localhost:8000/disconnect", json=disconnect_data)
```

## Running the Example

```bash
# In one terminal, start the server
python mcp_client_server.py

# In another terminal, run the example
python mcp_client_example.py
```

## Common MCP Servers

Here are some MCP servers you can connect to:

1. **Filesystem Server**
   ```json
   {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
   }
   ```

2. **GitHub Server**
   ```json
   {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-github"],
     "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"}
   }
   ```

3. **SQLite Server**
   ```json
   {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-sqlite", "path/to/database.db"]
   }
   ```

## Error Handling

The server returns appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (e.g., session already exists)
- `404` - Not found (e.g., session not found)
- `500` - Internal server error

All error responses include a detail message explaining the error.

## Session Management

- Each session is identified by a unique `session_id`
- Sessions persist until explicitly disconnected or the server shuts down
- Multiple sessions can be active simultaneously
- Sessions are automatically cleaned up on server shutdown