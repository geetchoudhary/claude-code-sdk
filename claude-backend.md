# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude Backend Server Documentation

This document provides comprehensive guidance for working with the backend server (`api_server_final.py`) in isolation from the rest of the Claude web interface.

## Quick Start

### Running the Backend Server

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
echo 'API_SERVER_URL=http://localhost:8001
PROJECT_ROOT=/Users/mastergeet/Repos/claude_test
CLAUDE_API_KEY=your-api-key-here' > .env

# Start the backend server
python api_server_final.py  # Runs on port 8001
```

### Development Commands

```bash
# Check for syntax errors
python -m py_compile api_server_final.py

# Format Python code (if black is installed)
black api_server_final.py

# Type checking (if mypy is installed)
mypy api_server_final.py

# View logs
tail -f logs/api_server.log  # If logging to file
# Server uses structured JSON logging to stdout by default
```

## Backend Architecture

The backend server is a **FastAPI REST API** that processes Claude AI queries asynchronously using a fire-and-forget pattern with webhook notifications.

### Core Components

1. **ClaudeQueryProcessor** - Main query processing engine
   - Handles Claude SDK integration
   - Manages message streaming
   - Implements timeout and retry logic

2. **SessionManager** - Session lifecycle management
   - Tracks active Claude sessions
   - Manages session statistics
   - Handles cleanup of expired sessions

3. **QueryMonitor** - Performance tracking
   - Monitors query duration and resource usage
   - Tracks error rates and patterns
   - Provides metrics endpoint

4. **ErrorRecoveryManager** - Intelligent retry system
   - Implements exponential backoff
   - Error-specific recovery strategies
   - Maximum 3 retries by default

### API Endpoints

#### Core Query Processing
```
POST /query
Body: {
    "prompt": str,
    "session_id": str (optional),
    "conversation_id": str (optional),
    "webhook_url": str,
    "options": dict (optional)
}
Returns: {"task_id": str}
```

#### Health & Monitoring
```
GET /health                        # Health check
GET /metrics                      # Performance metrics
GET /sessions/{session_id}        # Session details
POST /sessions/cleanup            # Clean old sessions
```

#### MCP Server Management
```
GET /mcp/servers                  # List MCP servers
POST /mcp/connect/{server_id}     # Connect MCP server
DELETE /mcp/disconnect/{server_id} # Disconnect MCP server
```

#### Project Initialization
```
POST /init-project
Body: {
    "github_url": str,
    "branch_name": str,
    "mcp_servers": list,
    "figma_api_key": str (optional),
    "github_personal_access_token": str (optional)
}
```

### Query Processing Flow

1. **Submission**: Client sends query with webhook URL → Immediate task_id response
2. **Processing**: Background task processes with Claude SDK
3. **Streaming**: Messages streamed and sent via webhook
4. **Completion**: Final result or error sent via webhook

### Webhook Payload Format

```python
{
    "task_id": str,
    "session_id": str,
    "conversation_id": str,
    "type": "user_message" | "processing" | "final_result" | "error",
    "content": str | dict,
    "timestamp": str,
    "metadata": dict (optional)
}
```

### Error Handling

The server implements sophisticated error recovery:

- **timeout_error**: Retry with increased timeout
- **process_error**: Retry with fresh session
- **sdk_error**: Retry after delay
- **cli_not_found**: Fail immediately
- **webhook_error**: Continue processing, log failure

### MCP Integration

The backend integrates with Model Context Protocol servers:

```json
{
    "approval-server": "Handles permission requests",
    "context-manager": "Manages conversation context",
    "context7": "Documentation access",
    "github": "Repository access (requires token)",
    "figma": "Design access (requires API key)"
}
```

#### MCP Approval Server (`mcp_approval_webhook_server.py`)

The approval server is a critical security component that intercepts tool calls and manages permissions:

**Architecture**:
- FastMCP server that intercepts all tool calls from Claude
- Runs a callback server on port 8083 for approval responses
- Sends webhook notifications to frontend on port 8002
- Maintains approval audit log in `permission_decisions.log`

**Auto-Approval Rules**:
```python
AUTO_APPROVE_PATTERNS = {
    "Read": ["*.py", "*.js", "*.json", "*.md", "*.txt"],
    "Write": ["*.py", "*.js", "*.json"],
    "Edit": ["*.py", "*.js", "*.json"],
    "LS": ["*"],
    "Task": ["*"],
}
```

**Dangerous Commands** (always require manual approval):
- `rm -rf`, `sudo`, `dd if=`, `format`
- `> /dev/`, `chmod 777`, `killall`, `pkill`

**Safe Bash Commands** (auto-approved):
- `ls`, `pwd`, `echo`, `cat`, `grep`, `find`
- `git status`, `git diff`

**Approval Flow**:
1. Claude requests tool usage → MCP server intercepts
2. Server checks auto-approval rules
3. If manual approval needed:
   - Generates unique request_id
   - Sends webhook to frontend with tool details
   - Waits for callback response (5-minute timeout)
4. Logs decision to `permission_decisions.log`
5. Returns allow/deny to Claude

**Webhook Payload**:
```json
{
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00",
    "tool_name": "Bash",
    "tool_input": {"command": "git commit -m 'message'"},
    "callback_url": "http://localhost:8083/approval-callback",
    "display_text": "Execute command: git commit -m 'message'"
}
```

**Callback Response**:
```json
{
    "request_id": "uuid",
    "decision": "allow" | "deny",
    "reason": "User approved the action"
}
```

### Key Configuration

#### Environment Variables
```bash
API_SERVER_URL=http://localhost:8001
PROJECT_ROOT=/path/to/project
CLAUDE_API_KEY=your-api-key
```

#### MCP Server Configuration
Edit `mcp-servers.json` to configure available MCP servers and their settings.

### Performance Considerations

- **Async Processing**: All operations are async for high concurrency
- **Fire-and-Forget**: Non-blocking query submission
- **Connection Pooling**: Efficient HTTP client usage
- **In-Memory Storage**: Fast but requires database for production
- **Structured Logging**: JSON logs for easy parsing

### Security Notes

- CORS enabled for all origins (restrict in production)
- No built-in authentication (implement as needed)
- Dangerous operations require MCP approval
- Store sensitive tokens in environment variables
- Log sanitization for sensitive data

## Development Workflow

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Add endpoint to FastAPI app
3. Implement async handler with error handling
4. Add structured logging
5. Update webhook notifications if needed

### Testing the Backend

```bash
# Health check
curl http://localhost:8001/health

# Submit query (webhook URL must be accessible)
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello Claude",
    "webhook_url": "http://localhost:8002/webhook"
  }'

# Get metrics
curl http://localhost:8001/metrics
```

### Common Patterns

#### Async Error Handling
```python
try:
    result = await async_operation()
except Exception as e:
    logger.error("Operation failed", error=str(e), exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

#### Webhook Notification
```python
await send_webhook_notification(
    webhook_url=webhook_url,
    payload={
        "task_id": task_id,
        "type": "processing",
        "content": message_content
    }
)
```

## Extracting the Backend

To run the backend independently:

1. **Minimal Dependencies**:
   - Copy `api_server_final.py`
   - Copy `requirements.txt`
   - Copy `mcp-servers.json` (or create minimal version)
   - Copy `mcp_approval_webhook_server.py` (if using approvals)

2. **Remove Frontend Dependencies**:
   - Update webhook URLs to your own endpoints
   - Remove hardcoded localhost:8002 references
   - Configure CORS for your frontend

3. **Database Integration**:
   - Replace in-memory storage with database
   - Add connection pooling
   - Implement proper session persistence

4. **Production Considerations**:
   - Add authentication/authorization
   - Implement rate limiting
   - Add request validation
   - Set up proper logging infrastructure
   - Configure HTTPS/TLS

### Minimal Standalone Configuration

```python
# Minimal mcp-servers.json for backend-only operation
{
    "mcpServers": {
        "approval-server": {
            "command": "python",
            "args": ["mcp_approval_webhook_server.py"],
            "disabled": true  # Disable if not using approvals
        }
    }
}
```

### Running with Approval Server

If you need the approval server for security:

1. **Start the approval server**:
   ```bash
   python mcp_approval_webhook_server.py
   ```

2. **Configure your webhook endpoint**:
   - Update `WEBHOOK_URL` in `mcp_approval_webhook_server.py`
   - Implement `/approval-request` endpoint in your frontend
   - Send approval decisions to `http://localhost:8083/approval-callback`

3. **Monitor approvals**:
   ```bash
   tail -f permission_decisions.log
   ```

## Important Notes

- The backend is designed to be stateless (except for in-memory session tracking)
- All long-running operations are handled asynchronously
- Webhook URLs must be accessible from the backend server
- The fire-and-forget pattern means clients must handle webhook results
- Session IDs are critical for conversation continuity