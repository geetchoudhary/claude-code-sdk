import asyncio
import logging
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

from claude_code_sdk import (
    query, 
    ClaudeCodeOptions, 
    Message,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = "/Users/mastergeet/Repos/claude_test"

def get_mcp_config():
    """Get MCP configuration from mcp-servers.json"""
    mcp_config_path = Path(__file__).parent / "mcp-servers.json"
    if mcp_config_path.exists():
        with open(mcp_config_path) as f:
            return json.load(f)
    return None

class QueryRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = Field(default=None, description="Resume a previous session")
    conversation_id: Optional[str] = Field(default=None, description="Frontend conversation grouping ID")
    webhook_url: str = Field(description="URL to notify when query completes")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options for Claude")

class QueryResponse(BaseModel):
    task_id: str
    status: str = "accepted"

class WebhookPayload(BaseModel):
    task_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime

app = FastAPI(
    title="Claude Code Fire-and-Forget API", 
    description="Stateless API for Claude Code SDK with webhook notifications"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_webhook(webhook_url: str, payload: WebhookPayload):
    """Send webhook notification"""
    logger.info(f"Attempting to send webhook to URL: {webhook_url}")
    logger.info(f"Webhook payload: task_id={payload.task_id}, session_id={payload.session_id}, status={payload.status}")
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Creating HTTP POST request to {webhook_url}")
            response = await client.post(
                webhook_url,
                json=payload.model_dump(mode='json'),
                timeout=10.0
            )
            if response.status_code >= 400:
                logger.error(f"Webhook failed: {response.status_code} - {response.text}")
            else:
                logger.info(f"Webhook sent successfully to {webhook_url} - Status: {response.status_code}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error sending webhook to {webhook_url}: {e}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout sending webhook to {webhook_url}: {e}")
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {type(e).__name__}: {e}")

async def process_query(
    task_id: str,
    prompt: str,
    webhook_url: str,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
):
    """Process Claude query and send webhook when complete"""
    logger.info(f"Processing task {task_id} - Prompt: {prompt[:50]}...")
    
    try:
        # Get permission mode from options
        permission_mode = options.get('permission_mode', 'acceptEdits') if options else 'acceptEdits'
        use_mcp = permission_mode == 'interactive'
        
        # Base Claude options
        claude_options_dict = {
            'cwd': options.get('cwd', PROJECT_ROOT) if options else PROJECT_ROOT,
            'allowed_tools': options.get('allowed_tools', ["Read", "Write", "LS", "Task"]) if options else ["Read", "Write", "LS", "Task"],
            'max_turns': options.get('max_turns', 8) if options else 8,
            'resume': session_id  # Resume session if provided
        }
        
        # Handle interactive permission mode with MCP
        if use_mcp:
            mcp_config = get_mcp_config()
            if mcp_config:
                logger.info(f"Task {task_id}: Using MCP interactive permissions")
                claude_options_dict['permission_mode'] = None  # Let MCP handle permissions
                claude_options_dict['permission_prompt_tool_name'] = "mcp__approval-server__permissions__approve"
                claude_options_dict['mcp_servers'] = mcp_config.get("mcpServers", {})
            else:
                logger.warning(f"Task {task_id}: MCP config not found, falling back to acceptEdits")
                claude_options_dict['permission_mode'] = 'acceptEdits'
        else:
            # Use standard permission modes
            claude_options_dict['permission_mode'] = permission_mode
        
        # Create Claude options
        claude_options = ClaudeCodeOptions(**claude_options_dict)
        
        messages = []
        result_session_id = session_id
        final_result = None
        
        # Execute query
        async for message in query(prompt=prompt, options=claude_options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            messages.append(block.text)
                            logger.info(f"Task {task_id}: Received message chunk")
            
            # Capture session ID and final result from ResultMessage
            if isinstance(message, ResultMessage):
                if hasattr(message, 'session_id'):
                    result_session_id = message.session_id
                    logger.info(f"Task {task_id}: Session ID captured: {result_session_id}")
                if hasattr(message, 'result'):
                    final_result = message.result
                    logger.info(f"Task {task_id}: Final result captured")
        
        # Use final_result if available, otherwise join messages
        result_text = final_result if final_result else "\n".join(messages)
        
        # Send success webhook
        await send_webhook(webhook_url, WebhookPayload(
            task_id=task_id,
            session_id=result_session_id,
            conversation_id=conversation_id,
            status="completed",
            result=result_text,
            timestamp=datetime.utcnow()
        ))
        
    except CLINotFoundError:
        error_msg = "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        logger.error(f"Task {task_id}: {error_msg}")
        await send_webhook(webhook_url, WebhookPayload(
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            status="failed",
            error=error_msg,
            timestamp=datetime.utcnow()
        ))
        
    except ProcessError as e:
        error_msg = f"Process failed with exit code {e.exit_code}"
        logger.error(f"Task {task_id}: {error_msg}")
        await send_webhook(webhook_url, WebhookPayload(
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            status="failed",
            error=error_msg,
            timestamp=datetime.utcnow()
        ))
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id}: Unexpected error - {error_msg}")
        await send_webhook(webhook_url, WebhookPayload(
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            status="failed",
            error=error_msg,
            timestamp=datetime.utcnow()
        ))

@app.post("/query", response_model=QueryResponse)
async def submit_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Submit a fire-and-forget query to Claude.
    
    Flow:
    1. Receive query with webhook URL and optional session_id
    2. Return task_id immediately
    3. Process query in background
    4. Send webhook notification when complete with session_id for continuation
    """
    task_id = str(uuid4())
    
    logger.info(f"New query submitted - Task: {task_id}, Session: {request.session_id}")
    logger.info(f"Webhook URL received: {request.webhook_url}")
    logger.info(f"Prompt: {request.prompt[:100]}...")
    
    # Add task to background
    background_tasks.add_task(
        process_query,
        task_id=task_id,
        prompt=request.prompt,
        webhook_url=request.webhook_url,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        options=request.options
    )
    
    return QueryResponse(task_id=task_id, status="accepted")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Claude Code Fire-and-Forget API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Submit a query with webhook notification",
            "GET /health": "Health check"
        },
        "flow": [
            "1. POST /query with prompt, webhook_url, and optional session_id",
            "2. Receive task_id immediately",
            "3. Wait for webhook notification",
            "4. Use session_id from webhook for next query"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Claude Code Fire-and-Forget API")
    print("📍 Running on http://localhost:8001")
    print("📚 Docs at http://localhost:8001/docs")
    print("\nNo session storage - completely stateless!")
    print("Session continuity handled by Claude Code SDK\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)