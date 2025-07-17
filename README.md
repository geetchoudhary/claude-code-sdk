# Claude Code Production API

A production-ready API for Claude Code integration with comprehensive architecture, proper error handling, and enterprise-grade features.

## ✨ Features

- **🏗️ Clean Architecture**: Layered architecture with proper separation of concerns
- **🔒 Type Safety**: Full type hints and validation with Pydantic
- **📊 Structured Logging**: JSON-structured logging with context tracking
- **🚀 Async Performance**: Fully asynchronous with background task processing
- **🛡️ Error Handling**: Comprehensive error handling with custom exceptions
- **💊 Health Checks**: Ready/live endpoints for Kubernetes/container orchestration
- **📋 API Documentation**: OpenAPI/Swagger documentation
- **🔄 Background Processing**: Fire-and-forget pattern with webhook notifications
- **🔧 MCP Integration**: Model Context Protocol server management
- **📦 Project Management**: Automated project initialization and setup
- **🌍 Production Ready**: Proper configuration management and deployment support

## 🏗️ Architecture

```
src/
├── core/              # Core application components
│   ├── config.py      # Configuration management
│   ├── exceptions.py  # Custom exceptions
│   └── logging.py     # Structured logging
├── models/            # Data models
│   └── schemas.py     # Pydantic schemas
├── services/          # Business logic layer
│   ├── claude_service.py    # Claude Code SDK integration
│   ├── mcp_service.py       # MCP server management
│   └── project_service.py   # Project management
├── api/               # API layer
│   ├── dependencies.py      # Dependency injection
│   ├── middleware.py        # Request/response middleware
│   ├── health.py           # Health check endpoints
│   └── routes/             # API routes
│       ├── claude.py       # Claude API routes
│       ├── mcp.py          # MCP API routes
│       └── projects.py     # Project API routes
├── app.py             # FastAPI application
└── main.py            # Entry point
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js (for Claude Code CLI)
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd claude_test
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements-prod.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

   Or using uvicorn directly:
   ```bash
   cd src
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

### Legacy System (Original)

The original system is still available:
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run original servers
python api_server_final.py          # Terminal 1
python webhook_frontend_unified.py  # Terminal 2

# Access at http://localhost:8002
```

## 📋 API Documentation

### Core Endpoints

#### Health Checks
- `GET /api/v1/health` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness check for K8s
- `GET /api/v1/health/live` - Liveness check for K8s

#### Claude Operations
- `POST /api/v1/claude/query` - Submit query to Claude
- `GET /api/v1/claude/query/{task_id}/status` - Get task status
- `DELETE /api/v1/claude/query/{task_id}` - Cancel task
- `GET /api/v1/claude/tasks` - List active tasks

#### MCP Server Management
- `GET /api/v1/mcp/servers` - List available MCP servers
- `POST /api/v1/mcp/servers/{server_id}/connect` - Connect to MCP server
- `DELETE /api/v1/mcp/servers/{server_id}/disconnect` - Disconnect from MCP server
- `GET /api/v1/mcp/config` - Get MCP configuration

#### Project Management
- `POST /api/v1/projects/init` - Initialize new project
- `GET /api/v1/projects/` - List projects
- `GET /api/v1/projects/{project_name}` - Get project info

### Usage Examples

#### Submit a Claude Query

```bash
curl -X POST "http://localhost:8001/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello Claude, analyze this code",
    "webhook_url": "http://localhost:8002/webhook",
    "options": {
      "max_turns": 5,
      "permission_mode": "acceptEdits"
    }
  }'
```

#### Initialize a Project

```bash
curl -X POST "http://localhost:8001/api/v1/projects/init" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo_url": "https://github.com/user/repo.git",
    "path": "my-project",
    "project_name": "feature-branch",
    "ai_instruction_files": {
      "create_claude_md": true,
      "create_ai_dos_and_donts": true
    }
  }'
```

## ⚙️ Configuration

### Environment Variables

The application uses a hierarchical configuration system with environment variables:

```bash
# Core Settings
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8001

# Project Settings
PROJECT_ROOT=/path/to/project
PROJECTS_DIR=projects

# Claude Settings
CLAUDE__MAX_TURNS=8
CLAUDE__TIMEOUT_SECONDS=300
CLAUDE__PERMISSION_MODE=acceptEdits

# Security Settings
SECURITY__SECRET_KEY=your-secret-key
SECURITY__CORS_ORIGINS=["http://localhost:3000"]

# Logging Settings
LOGGING__LEVEL=INFO
LOGGING__FILE_PATH=./logs/api.log
```

### Configuration Files

- `.env` - Environment-specific configuration
- `.env.example` - Example configuration file
- `mcp-servers.json` - MCP server configuration (auto-generated)

## 🔧 Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-prod.txt pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Type checking
mypy src/

# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/
```

### Development Mode

```bash
# Run with auto-reload
python src/main.py

# Or with uvicorn
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 🚢 Production Deployment

### Production Ready Features

- **Structured Logging**: JSON logs with request tracking
- **Health Checks**: Kubernetes-ready endpoints
- **Error Handling**: Comprehensive error responses
- **Security**: CORS, security headers, input validation
- **Configuration**: Environment-based configuration
- **Monitoring**: Built-in metrics and observability
- **Performance**: Async processing with background tasks

### Docker Deployment

```bash
# Build image
docker build -t claude-code-api .

# Run container
docker run -p 8001:8001 -e ENVIRONMENT=production claude-code-api
```

### Legacy Production Deployment (Ubuntu 24.04)

```bash
# Clone and setup
git clone <your-repo>
cd claude_test
./setup_ubuntu_24.sh

# Access at http://your-server-ip
```

## 🔒 Security

### Authentication & Authorization

- JWT token-based authentication (configurable)
- CORS configuration
- Rate limiting
- Input validation

### Security Headers

- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Referrer-Policy
- Strict-Transport-Security (production)

### Error Handling

- Custom exception hierarchy
- Secure error responses
- No sensitive data in error messages
- Proper HTTP status codes

## 📊 Monitoring

### Logging

The application uses structured JSON logging with context tracking:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "src.services.claude_service",
  "message": "Query completed successfully",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "task_id": "task-456",
  "session_id": "session-789",
  "processing_time": 2.5
}
```

### Health Checks

- `/api/v1/health` - Comprehensive health check
- `/api/v1/health/ready` - Readiness check
- `/api/v1/health/live` - Liveness check

### Metrics

The API provides built-in metrics and monitoring:

- Request/response times
- Error rates
- Active task counts
- Resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Claude Code](https://claude.ai/code) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/) framework
- [Pydantic](https://pydantic.dev/) for data validation
- [Uvicorn](https://www.uvicorn.org/) ASGI server