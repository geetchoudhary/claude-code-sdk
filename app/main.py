"""Main FastAPI application setup and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging
from app.routers import health, mcp, project, query, session

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Claude API starting up", version="1.0.0", port=settings.api_port)
    yield
    # Shutdown
    logger.info("Claude API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Claude Code Fire-and-Forget API",
    description="Stateless API for Claude Code SDK with webhook notifications",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(health.router, tags=["health"])
app.include_router(session.router, prefix="/sessions", tags=["sessions"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
app.include_router(project.router, tags=["project"])


@app.get("/")
async def root():
    """API information and available endpoints."""
    return {
        "name": "Claude Code Fire-and-Forget API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/query": "Submit a query with webhook notification",
            "GET /health": "Health check",
            "GET /metrics": "Get performance metrics and session statistics",
            "GET /sessions/{session_id}": "Get information about a specific session",
            "POST /sessions/cleanup": "Clean up old sessions",
            "GET /mcp/servers": "List available MCP servers",
            "POST /mcp/connect/{server_id}": "Connect to an MCP server",
            "DELETE /mcp/disconnect/{server_id}": "Disconnect from an MCP server",
            "POST /init-project": "Initialize a project by cloning a repo and creating a branch",
        },
        "flow": [
            "1. POST /api/query with prompt, webhook_url, and optional session_id",
            "2. Receive task_id immediately",
            "3. Wait for webhook notification",
            "4. Use session_id from webhook for next query",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Claude Code Fire-and-Forget API")
    print(f"📍 Running on http://localhost:{settings.api_port}")
    print(f"📚 Docs at http://localhost:{settings.api_port}/docs")
    print("\nNo session storage - completely stateless!")
    print("Session continuity handled by Claude Code SDK\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
    )