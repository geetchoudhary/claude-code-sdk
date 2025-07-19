# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Start both servers for local development
python api_server_final.py          # Terminal 1 - API Server (port 8001)
python webhook_frontend_unified.py  # Terminal 2 - Frontend Server (port 8002)

# Access the application at http://localhost:8002
```

### Production Commands
```bash
# Check service status
sudo systemctl status claude-api
sudo systemctl status claude-frontend

# View logs
sudo journalctl -u claude-api -f
sudo journalctl -u claude-frontend -f

# Restart services
sudo systemctl restart claude-api
sudo systemctl restart claude-frontend
```

## Architecture Overview

This is a Claude Code SDK implementation with an approval system for tool permissions. The architecture consists of:

### Core Components

1. **API Server (`api_server_final.py:8001`)**
   - Handles Claude AI queries via the `claude-code-sdk` package
   - Manages MCP server connections and custom connectors
   - Processes async queries with webhook notifications
   - Supports session resumption and conversation tracking
   - Routes: `/query`, `/mcp/*`, `/projects/init`

2. **Frontend Server (`webhook_frontend_unified.py:8002`)**
   - Serves the web UI (`frontend_unified.html`)
   - Proxies API requests to the API server
   - Handles approval webhooks and SSE for real-time updates
   - Manages approval UI for MCP permission requests
   - Routes: `/`, `/api/*`, `/approval-request`, `/approval-decision`

3. **MCP Approval Server (`mcp_approval_webhook_server.py`)**
   - FastMCP server for permission management
   - Sends approval requests via webhooks
   - Implements auto-approval patterns for safe operations
   - Logs all permission decisions for audit

### Key Concepts

**MCP (Model Context Protocol) Integration**
- Configuration in `mcp-servers.json`
- Multiple MCP servers supported (approval-server, context-manager, github, etc.)
- Dynamic server connection management via `/mcp/servers` endpoints

**Approval Flow**
1. Claude requests tool usage → MCP approval server intercepts
2. Server checks auto-approval patterns or sends webhook to frontend
3. User approves/denies in web UI → Decision sent back to MCP server
4. Tool execution proceeds or is blocked based on decision

**Session Management**
- Sessions can be resumed using `session_id` parameter
- Conversations grouped with `conversation_id` for frontend organization
- Async processing with task IDs and webhook notifications

### Custom Claude Commands

The `.claude/commands/` directory contains specialized commands:
- `/create-task`: Interactive task definition with codebase analysis
- `/plan-task`: Comprehensive implementation planning
- `/implement-task`: Executes plans from `/plan-task`

## Important Files and Patterns

### Configuration Files
- `mcp-servers.json`: MCP server configurations
- `requirements.txt`: Python dependencies (FastAPI, claude-code-sdk, mcp, etc.)
- `.claude/settings.local.json`: Claude permissions configuration

### API Patterns
- All API responses follow consistent error handling with HTTPException
- Webhook payloads include task_id, status, result/error, and timestamp
- CORS enabled for cross-origin requests

### Security Considerations
- Auto-approval patterns defined in `AUTO_APPROVE_PATTERNS`
- Dangerous commands list in `DANGEROUS_COMMANDS` always require approval
- All permission decisions logged to `permission_decisions.log`
- Environment variables for sensitive configuration

## Development Tips

1. **Adding New MCP Servers**: Update `mcp-servers.json` and restart the API server
2. **Modifying Auto-Approval**: Edit patterns in `mcp_approval_webhook_server.py`
3. **Frontend Changes**: Edit `frontend_unified.html` - changes reflect on refresh
4. **API Changes**: Restart `api_server_final.py` after modifications
5. **Debug Logging**: Check console output and journalctl logs for troubleshooting