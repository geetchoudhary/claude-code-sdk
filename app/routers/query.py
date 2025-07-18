"""Query endpoint routes."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks
import structlog

from app.config import settings
from app.core.query_processor import ClaudeQueryProcessor
from app.models import QueryRequest, QueryResponse

router = APIRouter()
logger = structlog.get_logger(__name__)

# Global query processor instance
query_processor = ClaudeQueryProcessor()


async def process_query(
    task_id: str,
    prompt: str,
    webhook_url: str,
    org: str,
    project_path: str,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    options: Optional[dict] = None,
):
    """Process Claude query using the structured query processor with retry logic."""
    # Construct project directory path from org and project_path
    project_dir = settings.projects_dir / org / project_path
    
    # Update options with project-specific cwd
    if options is None:
        options = {}
    
    # Set the cwd to the project directory
    options["cwd"] = str(project_dir)
    options["permission_mode"] = "interactive"
    
    logger.info(f"Using project directory: {project_dir}")
    
    await query_processor.process_query_with_retry(
        task_id, prompt, webhook_url, session_id, conversation_id, options
    )


@router.post("/query", response_model=QueryResponse)
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

    logger.info(
        f"New query submitted - Task: {task_id}, Session: {request.session_id}, "
        f"Project: {request.org}/{request.project_path}"
    )
    logger.info(f"Webhook URL received: {request.webhook_url}")
    logger.info(f"Prompt: {request.prompt[:100]}...")

    # Add task to background
    background_tasks.add_task(
        process_query,
        task_id=task_id,
        prompt=request.prompt,
        webhook_url=request.webhook_url,
        org=request.org,
        project_path=request.project_path,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        options=request.options,
    )

    return QueryResponse(task_id=task_id, status="accepted")