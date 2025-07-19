"""Project initialization endpoint routes."""

import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
import structlog

from app.config import settings
from app.models import InitProjectRequest, InitProjectResponse, ProjectInitStatus
from app.services.project_utils import (
    checkout_new_branch,
    clone_repository,
    copy_default_ai_files,
    copy_mcp_approval_server,
    create_mcp_config_for_project,
    create_slash_commands,
    run_claude_init_with_query_processor,
    run_default_mcp_commands,
    setup_claude_directory,
    update_gitignore,
)
from app.services.webhook_utils import send_project_init_webhook

router = APIRouter()
logger = structlog.get_logger(__name__)


async def init_project_background(
    task_id: str,
    request: InitProjectRequest,
):
    """Background task to initialize a project with webhook notifications."""
    webhook_url = request.webhook_url
    
    try:
        # Step 1: Create directory structure
        await send_project_init_webhook(
            webhook_url, task_id, "create_directory", 
            "Creating project directory structure...", 
            ProjectInitStatus.IN_PROGRESS
        )
        
        projects_dir = settings.projects_dir
        projects_dir.mkdir(exist_ok=True)
        
        org_path = projects_dir / request.organization_name
        org_path.mkdir(exist_ok=True)
        
        project_path = org_path / request.project_path
        
        if project_path.exists():
            await send_project_init_webhook(
                webhook_url, task_id, "create_directory",
                f"Directory already exists: {project_path}",
                ProjectInitStatus.FAILED,
                error=f"Directory already exists: {project_path}"
            )
            return
            
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {project_path}")
        
        await send_project_init_webhook(
            webhook_url, task_id, "create_directory",
            f"Created directory structure: {request.organization_name}/{request.project_path}",
            ProjectInitStatus.IN_PROGRESS
        )
        
        # Step 2: Clone repository
        await send_project_init_webhook(
            webhook_url, task_id, "clone_repository",
            f"Cloning repository from {request.github_repo_url}...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        clone_result = clone_repository(request.github_repo_url, project_path)
        
        if clone_result.returncode != 0:
            if project_path.exists():
                shutil.rmtree(project_path)
            await send_project_init_webhook(
                webhook_url, task_id, "clone_repository",
                f"Failed to clone repository: {clone_result.stderr}",
                ProjectInitStatus.FAILED,
                error=clone_result.stderr
            )
            return
            
        logger.info(f"Cloned repository: {request.github_repo_url} to {project_path}")
        
        await send_project_init_webhook(
            webhook_url, task_id, "clone_repository",
            "Repository cloned successfully",
            ProjectInitStatus.IN_PROGRESS
        )
        
        # Step 2.5: Update .gitignore to exclude .claude directory
        gitignore_result = update_gitignore(project_path)
        if not gitignore_result:
            logger.warning("Failed to update .gitignore, continuing...")
        else:
            logger.info("Updated .gitignore to exclude .claude directory")
        
        # Step 3: Checkout new branch
        await send_project_init_webhook(
            webhook_url, task_id, "checkout_branch",
            f"Creating and checking out new branch: {request.project_path}...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        branch_result = checkout_new_branch(project_path, request.project_path)
        
        if branch_result["success"]:
            await send_project_init_webhook(
                webhook_url, task_id, "checkout_branch",
                f"Successfully checked out new branch: {request.project_path}",
                ProjectInitStatus.IN_PROGRESS,
                metadata={"branch_name": branch_result["branch_name"]}
            )
        else:
            await send_project_init_webhook(
                webhook_url, task_id, "checkout_branch",
                f"Warning: Failed to create branch: {branch_result.get('error', 'Unknown error')}",
                ProjectInitStatus.IN_PROGRESS,
                metadata={"branch_creation_failed": True, "error": branch_result.get('error')}
            )
        
        # Step 4: Setup .claude directory (moved from Step 5)
        await send_project_init_webhook(
            webhook_url, task_id, "setup_claude_directory",
            "Setting up .claude directory with hooks and settings...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        claude_setup_success = setup_claude_directory(project_path, webhook_url)
        if not claude_setup_success:
            logger.warning("Failed to setup .claude directory completely")
            
        await send_project_init_webhook(
            webhook_url, task_id, "setup_claude_directory",
            ".claude directory setup completed",
            ProjectInitStatus.IN_PROGRESS
        )
        
        # Step 5: Setup MCP servers (moved from Step 4)
        await send_project_init_webhook(
            webhook_url, task_id, "setup_mcp",
            "Setting up MCP servers configuration...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        mcp_servers = request.mcp_servers or []
        approval_server_path = Path(__file__).parent.parent.parent / "mcp_approval_webhook_server.py"
        
        create_mcp_config_for_project(project_path, mcp_servers, approval_server_path)
        
        copy_success = copy_mcp_approval_server(project_path, approval_server_path)
        if not copy_success:
            logger.warning("Failed to copy MCP approval server, continuing...")
            
        await send_project_init_webhook(
            webhook_url, task_id, "setup_mcp",
            f"MCP configuration created with {len(mcp_servers)} servers",
            ProjectInitStatus.IN_PROGRESS,
            metadata={"mcp_servers": [s.server_type.value for s in mcp_servers]}
        )
        
        # Step 6: Create slash commands
        await send_project_init_webhook(
            webhook_url, task_id, "create_slash_commands",
            "Creating slash commands...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        slash_commands_success = create_slash_commands(project_path)
        if not slash_commands_success:
            logger.warning("Failed to create slash commands")
            
        await send_project_init_webhook(
            webhook_url, task_id, "create_slash_commands",
            "Slash commands created successfully",
            ProjectInitStatus.IN_PROGRESS
        )
        
        # Step 7: Copy default AI instruction files
        await send_project_init_webhook(
            webhook_url, task_id, "copy_ai_files",
            "Copying default AI instruction files...",
            ProjectInitStatus.IN_PROGRESS
        )
        
        ai_files_result = copy_default_ai_files(project_path)
        
        await send_project_init_webhook(
            webhook_url, task_id, "copy_ai_files",
            f"AI instruction files copied: {ai_files_result['files_copied']}/{ai_files_result['total_files']} succeeded",
            ProjectInitStatus.IN_PROGRESS,
            metadata=ai_files_result
        )
        
        # Step 8: Run Claude /init command
        # await send_project_init_webhook(
        #     webhook_url, task_id, "claude_init",
        #     "Running Claude /init command...",
        #     ProjectInitStatus.IN_PROGRESS
        # )
        
        # claude_init_result = await run_claude_init_with_query_processor(
        #     project_path, task_id, webhook_url
        # )
        
        # await send_project_init_webhook(
        #     webhook_url, task_id, "claude_init",
        #     "Claude /init command completed" if claude_init_result["success"] else "Claude /init command failed",
        #     ProjectInitStatus.IN_PROGRESS,
        #     metadata=claude_init_result
        # )
        
        # Step 9: Run default MCP commands
        mcp_results = []
        if mcp_servers:
            await send_project_init_webhook(
                webhook_url, task_id, "mcp_initialization",
                "Running default MCP server commands...",
                ProjectInitStatus.IN_PROGRESS
            )
            
            # mcp_config_path = project_path / "mcp-servers.json"
            # if mcp_config_path.exists():
            #     with open(mcp_config_path, "r") as f:
            #         full_mcp_config = json.load(f)
            #         full_mcp_servers = full_mcp_config.get("mcpServers", {})
                    
            #     mcp_results = await run_default_mcp_commands(
            #         project_path, 
            #         full_mcp_servers,
            #         webhook_url
            #     )
                
            await send_project_init_webhook(
                webhook_url, task_id, "mcp_initialization",
                f"MCP initialization completed: {len([r for r in mcp_results if r.get('success')])} succeeded",
                ProjectInitStatus.IN_PROGRESS,
                metadata={"mcp_results": mcp_results}
            )
        
        # Final success webhook
        await send_project_init_webhook(
            webhook_url, task_id, "initialization_complete",
            "Project initialization completed successfully",
            ProjectInitStatus.COMPLETED,
            metadata={
                "organization": request.organization_name,
                "project_path": str(project_path),
                "mcp_servers_count": len(mcp_servers) + 1,
                "mcp_servers_enabled": [s.server_type.value for s in mcp_servers],
                "setup_results": {
                    "mcp_approval_copied": copy_success,
                    "claude_directory_setup": claude_setup_success,
                    "slash_commands_created": slash_commands_success,
                    "branch_checkout_success": branch_result["success"],
                    "ai_files_copied": ai_files_result["files_copied"],
                    # "claude_init_success": claude_init_result["success"],
                },
                # "mcp_initialization_results": mcp_results
            }
        )
        
        logger.info(f"Project initialization completed successfully for task {task_id}")
        
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        await send_project_init_webhook(
            webhook_url, task_id, "initialization_failed",
            f"Project initialization failed: {str(e)}",
            ProjectInitStatus.FAILED,
            error=str(e)
        )


@router.post("/init-project", response_model=InitProjectResponse)
async def init_project(request: InitProjectRequest, background_tasks: BackgroundTasks):
    """Initialize a new project by cloning a repository with full Claude setup.
    
    Returns task_id immediately and processes initialization in background.
    Sends webhook notifications for each step of the process.
    """
    task_id = str(uuid4())
    
    logger.info(
        f"New project initialization request - Task: {task_id}, "
        f"Org: {request.organization_name}, Project: {request.project_path}"
    )
    
    # Add initialization to background tasks
    background_tasks.add_task(
        init_project_background,
        task_id=task_id,
        request=request,
    )
    
    return InitProjectResponse(
        task_id=task_id,
        status="accepted",
        message="Project initialization started"
    )