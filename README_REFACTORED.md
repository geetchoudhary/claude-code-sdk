# Claude API - Modular FastAPI Service

A well-structured, modular FastAPI application for integrating with Claude AI SDK, featuring fire-and-forget query processing, webhook notifications, and MCP (Model Context Protocol) server integration.

## Features

- **Modular Architecture**: Clean separation of concerns following SOLID principles
- **Asynchronous Processing**: Fire-and-forget pattern with webhook notifications
- **Session Management**: Track and manage Claude conversation sessions
- **Performance Monitoring**: Built-in query performance tracking and metrics
- **Error Recovery**: Sophisticated retry logic with strategy-based recovery
- **MCP Integration**: Support for Model Context Protocol servers
- **Project Initialization**: Automated project setup with AI instruction files

## Project Structure

```
claude_api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Main FastAPI app setup
│   ├── config.py                  # Configuration management
│   ├── logging_config.py          # Structured logging setup
│   ├── models.py                  # Pydantic models
│   ├── core/                      # Core business logic
│   │   ├── session_manager.py     # Session lifecycle management
│   │   ├── query_monitor.py       # Query performance monitoring
│   │   ├── error_recovery.py      # Error recovery strategies
│   │   └── query_processor.py     # Main query processing logic
│   ├── services/                  # Service layer
│   │   ├── mcp_integration.py     # MCP server management
│   │   ├── webhook_utils.py       # Webhook utilities
│   │   └── project_utils.py       # Project initialization
│   └── routers/                   # API endpoints
│       ├── query.py               # Query endpoints
│       ├── health.py              # Health & monitoring
│       ├── session.py             # Session management
│       ├── mcp.py                 # MCP server endpoints
│       └── project.py             # Project initialization
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
API_PORT=8001
PROJECT_ROOT=/Users/mastergeet/Repos/claude_test
CLAUDE_API_KEY=your-claude-api-key
EOF
```

### 2. Run the Application

```bash
# Development mode with auto-reload
python -m app.main

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 3. Access the API

- API Documentation: http://localhost:8001/docs
- Health Check: http://localhost:8001/health
- Metrics: http://localhost:8001/metrics

## API Endpoints

### Core Endpoints

- `POST /api/query` - Submit a query to Claude
- `GET /health` - Health check
- `GET /metrics` - Performance metrics

### Session Management

- `GET /sessions/{session_id}` - Get session information
- `POST /sessions/cleanup` - Clean up old sessions

### MCP Server Management

- `GET /mcp/servers` - List available MCP servers
- `POST /mcp/connect/{server_id}` - Connect to an MCP server
- `DELETE /mcp/disconnect/{server_id}` - Disconnect from an MCP server

### Project Management

- `POST /init-project` - Initialize a new project

## Configuration

Configuration is managed through environment variables or `.env` file:

```env
# API Configuration
API_PORT=8001
API_SERVER_URL=http://localhost:8001
WEBHOOK_TIMEOUT=10.0
QUERY_TIMEOUT=300
MAX_RETRIES=3

# Paths
PROJECT_ROOT=/path/to/your/project
MCP_CONFIG_FILE=mcp-servers.json

# Claude SDK
CLAUDE_API_KEY=your-api-key
CLAUDE_MODEL=claude-3-5-sonnet-latest
CLAUDE_MAX_TURNS=8

# CORS (comma-separated origins)
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
LOG_JSON=true

# Development
DEBUG=false
```

## Testing

```bash
# Run tests (when implemented)
pytest

# Type checking
mypy app/

# Code formatting
black app/

# Linting
ruff app/
```

## Development Workflow

1. **Make Changes**: Edit code in the modular structure
2. **Type Check**: Run `mypy app/` to catch type errors
3. **Format Code**: Run `black app/` for consistent formatting
4. **Test**: Run tests to ensure functionality
5. **Run Locally**: Test with `python -m app.main`

## Key Design Decisions

1. **Modular Structure**: Each component has a single responsibility
2. **Dependency Injection**: Components are loosely coupled
3. **Type Safety**: Full type hints for better IDE support and error catching
4. **Async First**: All I/O operations are asynchronous
5. **Structured Logging**: JSON logs with contextual information
6. **Configuration Management**: Environment-based configuration with Pydantic
7. **Error Recovery**: Strategy pattern for different error types
8. **Clean Architecture**: Clear separation between API, business logic, and services

## Production Deployment

For production deployment:

1. Set appropriate environment variables
2. Use a process manager like systemd or supervisor
3. Put behind a reverse proxy (nginx/caddy)
4. Enable HTTPS
5. Configure proper CORS origins
6. Set up monitoring and alerting
7. Use a production database for session storage (current implementation is in-memory)

## Migration from Monolithic Code

To migrate from the old `api_server_final.py`:

1. Stop the old service
2. Install new dependencies: `pip install -r requirements.txt`
3. Update your `.env` file with the new configuration
4. Run the new service: `python -m app.main`
5. Update any webhook URLs or integrations to use the same endpoints

All API endpoints remain the same, so no client-side changes are needed.

## Contributing

1. Follow the existing code structure and patterns
2. Add type hints to all functions
3. Write docstrings for all modules, classes, and functions
4. Keep functions small and focused
5. Add appropriate error handling
6. Update tests for new functionality

## License

[Your License Here]