"""Project initialization endpoint routes."""

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
import structlog

from app.config import settings
from app.models import InitProjectRequest
from app.services.project_utils import (
    clone_repository,
    create_ai_instruction_files,
    create_basic_claude_md,
    create_git_branch,
    create_mcp_config_for_project,
    run_claude_init_command,
    run_context_manager_prompts,
    update_claude_md_with_references,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/init-project")
async def init_project(request: InitProjectRequest):
    """Initialize a new project by cloning a repository and creating a branch."""
    try:
        # Create the base projects directory within PROJECT_ROOT
        projects_dir = settings.projects_dir
        projects_dir.mkdir(exist_ok=True)

        # Create the full project path
        project_path = projects_dir / request.path

        # Check if directory already exists
        if project_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Directory already exists: {project_path}",
            )

        # Create the directory
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {project_path}")

        # Clone the repository
        clone_result = clone_repository(request.github_repo_url, project_path)

        if clone_result.returncode != 0:
            # Clean up directory on failure
            if project_path.exists():
                shutil.rmtree(project_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clone repository: {clone_result.stderr}",
            )

        logger.info(f"Cloned repository: {request.github_repo_url} to {project_path}")

        # Create and checkout new branch
        branch_result = create_git_branch(project_path, request.project_name)

        if branch_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create branch: {branch_result.stderr}",
            )

        logger.info(f"Created and checked out branch: {request.project_name}")

        # Create mcp-servers.json if MCP servers were provided
        if request.mcp_servers:
            approval_server_path = Path(__file__).parent.parent.parent / "mcp_approval_webhook_server.py"
            create_mcp_config_for_project(project_path, request.mcp_servers, approval_server_path)

        # Handle AI instruction files
        ai_files_created = []
        claude_init_success = False

        if request.ai_instruction_files:
            ai_files = request.ai_instruction_files

            # Create AI instruction files
            if any(
                [
                    ai_files.create_ai_dos_and_donts,
                    ai_files.create_ai_figma_to_code,
                    ai_files.create_ai_coding_rules,
                ]
            ):
                create_ai_instruction_files(project_path, ai_files)
                if ai_files.create_ai_dos_and_donts:
                    ai_files_created.append("AI_DOS_AND_DONTS.md")
                if ai_files.create_ai_figma_to_code:
                    ai_files_created.append("AI_FIGMA_TO_CODE.md")
                if ai_files.create_ai_coding_rules:
                    ai_files_created.append("AI_CODING_RULES.md")

                logger.info(f"Created AI instruction files: {', '.join(ai_files_created)}")

            # Run Claude /init command to create CLAUDE.md
            if ai_files.create_claude_md:
                claude_init_success = await run_claude_init_command(project_path)
                if claude_init_success:
                    ai_files_created.append("CLAUDE.md")
                    logger.info("Successfully created CLAUDE.md using Claude Code SDK")
                else:
                    # Create a basic CLAUDE.md as fallback
                    logger.warning("Creating basic CLAUDE.md template as fallback")
                    create_basic_claude_md(project_path, request.project_name, request.github_repo_url)
                    ai_files_created.append("CLAUDE.md")
                    claude_init_success = True
                    logger.info("Created basic CLAUDE.md template")

            # Update CLAUDE.md with references to AI instruction files
            if ai_files.update_claude_md and claude_init_success:
                enhancement_success = await update_claude_md_with_references(project_path)
                if enhancement_success:
                    logger.info("Updated CLAUDE.md with AI instruction file references")
                else:
                    logger.warning("Failed to enhance CLAUDE.md with AI instruction file references")

        # Run context manager initialization if context-manager is selected
        context_manager_results = []
        if request.mcp_servers and "context-manager" in request.mcp_servers:
            # Load the mcp-servers.json from the project directory
            mcp_config_path = project_path / "mcp-servers.json"
            if mcp_config_path.exists():
                with open(mcp_config_path, "r") as f:
                    mcp_config = json.load(f)
                mcp_servers = mcp_config.get("mcpServers", {})
                context_manager_results = await run_context_manager_prompts(project_path, mcp_servers)

        return {
            "status": "success",
            "message": f"Project initialized successfully",
            "project_path": str(project_path),
            "branch": request.project_name,
            "mcp_servers_count": len(request.mcp_servers) + 1 if request.mcp_servers else 0,
            "ai_files_created": ai_files_created,
            "claude_init_success": claude_init_success,
            "context_manager_results": context_manager_results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        raise HTTPException(status_code=500, detail=str(e))