"""Project initialization and AI instruction file utilities."""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    Message,
    ResultMessage,
    TextBlock,
    query,
)

from app.config import settings
from app.models import AIInstructionFiles

logger = structlog.get_logger(__name__)


def create_ai_instruction_files(project_path: Path, ai_files: AIInstructionFiles):
    """Create AI instruction files in the project directory."""
    if ai_files.create_ai_dos_and_donts:
        ai_dos_and_donts_content = '''# AI DO's and DON'Ts

## DO's
- Always follow the project's coding standards and conventions
- Write clear, concise, and well-documented code
- Use meaningful variable and function names
- Implement proper error handling and logging
- Follow the DRY (Don't Repeat Yourself) principle
- Write unit tests for your code
- Use version control best practices
- Consider performance implications of your code
- Follow security best practices
- Document your API endpoints and functions

## DON'Ts
- Don't hardcode sensitive information like API keys or passwords
- Don't ignore error handling
- Don't write overly complex code without proper documentation
- Don't skip testing
- Don't commit broken code
- Don't use deprecated libraries or functions
- Don't ignore code review feedback
- Don't write code without understanding the business requirements
- Don't make breaking changes without proper communication
- Don't ignore performance bottlenecks

## Code Quality Guidelines
- Maintain consistent code formatting
- Use appropriate design patterns
- Keep functions and classes focused on single responsibilities
- Write self-documenting code
- Use proper naming conventions
- Implement proper logging for debugging and monitoring
'''
        with open(project_path / "AI_DOS_AND_DONTS.md", "w") as f:
            f.write(ai_dos_and_donts_content)

    if ai_files.create_ai_figma_to_code:
        ai_figma_to_code_content = '''# AI Figma to Code Guidelines

## Process Overview
1. **Analysis**: Carefully analyze the Figma design for layout, components, and interactions
2. **Planning**: Plan the component structure and identify reusable elements
3. **Implementation**: Convert design to clean, maintainable code
4. **Testing**: Ensure the implementation matches the design specifications

## Key Principles
- **Pixel Perfect**: Strive for exact visual match with the Figma design
- **Responsive**: Ensure the implementation works across different screen sizes
- **Semantic HTML**: Use appropriate HTML elements for accessibility
- **Component-Based**: Break down complex designs into reusable components
- **Performance**: Optimize for fast loading and smooth interactions

## Design Analysis Checklist
- [ ] Layout structure and grid system
- [ ] Typography (fonts, sizes, weights, line heights)
- [ ] Colors and color schemes
- [ ] Spacing and padding
- [ ] Border radius and shadows
- [ ] Interactive states (hover, focus, active)
- [ ] Responsive breakpoints
- [ ] Component variations and states
- [ ] Animation and transition requirements

## Implementation Guidelines
- Use CSS Grid or Flexbox for layouts
- Implement proper component hierarchy
- Use CSS variables for consistent theming
- Ensure proper accessibility attributes
- Optimize images and assets
- Test on multiple devices and browsers
- Validate against design specifications

## Quality Assurance
- Compare implementation with Figma design side-by-side
- Test all interactive elements
- Verify responsive behavior
- Check accessibility compliance
- Validate performance metrics
'''
        with open(project_path / "AI_FIGMA_TO_CODE.md", "w") as f:
            f.write(ai_figma_to_code_content)

    if ai_files.create_ai_coding_rules:
        ai_coding_rules_content = '''# AI Coding Rules

## General Principles
1. **Clean Code**: Write code that is easy to read, understand, and maintain
2. **SOLID Principles**: Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion
3. **DRY**: Don't Repeat Yourself - avoid code duplication
4. **KISS**: Keep It Simple, Stupid - avoid unnecessary complexity
5. **YAGNI**: You Aren't Gonna Need It - don't implement features until they're needed

## Code Structure
- Use consistent indentation (spaces or tabs, not mixed)
- Group related functionality together
- Use meaningful file and folder names
- Keep functions and methods small and focused
- Use descriptive variable and function names
- Add comments for complex logic, not obvious code

## Error Handling
- Always handle potential errors gracefully
- Use appropriate error types and messages
- Log errors with sufficient context
- Provide meaningful feedback to users
- Implement proper validation for inputs

## Security
- Never hardcode sensitive information
- Validate and sanitize all inputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Follow security best practices for your technology stack

## Performance
- Avoid premature optimization
- Profile code to identify bottlenecks
- Use appropriate data structures and algorithms
- Minimize network requests
- Implement caching where appropriate
- Optimize database queries

## Testing
- Write unit tests for business logic
- Test edge cases and error conditions
- Use integration tests for API endpoints
- Mock external dependencies
- Maintain good test coverage
- Keep tests simple and focused

## Documentation
- Write clear commit messages
- Document API endpoints
- Add inline comments for complex logic
- Keep README files up to date
- Document deployment procedures
- Maintain changelog for releases

## Code Review
- Review code for functionality, readability, and maintainability
- Check for security vulnerabilities
- Ensure tests are adequate
- Verify documentation is updated
- Provide constructive feedback
- Be open to feedback and suggestions
'''
        with open(project_path / "AI_CODING_RULES.md", "w") as f:
            f.write(ai_coding_rules_content)


async def run_claude_init_command(project_path: Path) -> bool:
    """Use Claude Code SDK to create CLAUDE.md with /init command."""
    try:
        # Check if CLAUDE.md already exists
        logger.info(f"Checking if CLAUDE.md exists in {project_path}")
        claude_md_path = project_path / "CLAUDE.md"
        existing_claude_md = claude_md_path.exists()
        logger.info(f"CLAUDE.md exists: {existing_claude_md}")

        # Use Claude Code SDK to run /init command
        claude_options = ClaudeCodeOptions(
            cwd=str(project_path),
            allowed_tools=["Read", "Write", "LS", "Edit", "MultiEdit"],
            max_turns=16,
            permission_mode="bypassPermissions",
        )

        # Run /init command using Claude Code SDK
        init_prompt = "/init"

        try:
            # Create a separate task to handle the query
            query_task = asyncio.create_task(_run_claude_query(init_prompt, claude_options))

            # Wait for the query with a timeout
            try:
                success = await asyncio.wait_for(query_task, timeout=120.0)
                if success:
                    logger.info(f"Successfully created CLAUDE.md using Claude Code SDK")
                    return True
            except asyncio.TimeoutError:
                logger.warning("Claude query timed out after 120 seconds")
                # Cancel the task but don't wait for cancellation
                query_task.cancel()
                # Give it a moment to cancel gracefully
                await asyncio.sleep(0.1)

        except Exception as query_error:
            logger.warning(f"Error during Claude query: {query_error}")
            # Continue to check if CLAUDE.md was created despite the error

        # Check if CLAUDE.md exists now
        if claude_md_path.exists():
            if existing_claude_md:
                logger.info(f"CLAUDE.md already existed and was updated by Claude Code SDK")
            else:
                logger.info(f"Successfully created CLAUDE.md using Claude Code SDK")
            return True
        else:
            # If /init didn't create CLAUDE.md (e.g., due to existing file), create a basic one
            logger.warning("CLAUDE.md was not created by /init command, creating basic template")
            return False

    except Exception as e:
        logger.error(f"Error running Claude /init command: {e}")
        # Check if it's an API limit error
        if "Claude AI usage limit reached" in str(e):
            logger.warning("Claude API usage limit reached")
        return False


async def _run_claude_query(prompt: str, options: ClaudeCodeOptions) -> bool:
    """Helper function to run Claude query in isolation."""
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            logger.info(f"Claude /init response: {block.text}")

            # Check if ResultMessage indicates completion
            if isinstance(message, ResultMessage):
                if hasattr(message, "result"):
                    return True
        return True
    except Exception as e:
        logger.warning(f"Error in Claude query helper: {e}")
        return False


async def _run_enhancement_query(prompt: str, options: ClaudeCodeOptions) -> bool:
    """Helper function to run Claude enhancement query in isolation."""
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            logger.info(f"Claude enhancement response: {block.text[:100]}...")

            # Check if ResultMessage indicates success
            if isinstance(message, ResultMessage):
                if hasattr(message, "result"):
                    return True

        return True
    except Exception as e:
        logger.warning(f"Error in Claude enhancement helper: {e}")
        return False


async def update_claude_md_with_references(project_path: Path) -> bool:
    """Use Claude Code SDK to enhance CLAUDE.md with AI instruction file references."""
    claude_md_path = project_path / "CLAUDE.md"

    if not claude_md_path.exists():
        logger.warning("CLAUDE.md not found, cannot update with references")
        return False

    try:
        # Use Claude Code SDK to enhance CLAUDE.md
        claude_options = ClaudeCodeOptions(
            cwd=str(project_path),
            allowed_tools=["Read", "Write", "LS", "Edit", "MultiEdit"],
            max_turns=8,
            permission_mode="acceptEdits",
        )

        # Dynamically detect which AI instruction files exist
        ai_files_present = []
        ai_file_descriptions = {
            "AI_DOS_AND_DONTS.md": "General do's and don'ts for AI development",
            "AI_FIGMA_TO_CODE.md": "Guidelines for converting Figma designs to code",
            "AI_CODING_RULES.md": "Specific coding rules and standards for this project",
        }

        for ai_file, description in ai_file_descriptions.items():
            if (project_path / ai_file).exists():
                ai_files_present.append(f"- {ai_file}: {description}")

        if not ai_files_present:
            logger.warning("No AI instruction files found for enhancement")
            return True

        ai_files_list = "\n".join(ai_files_present)

        # Enhanced prompt with dynamic file detection
        enhancement_prompt = f"""Please enhance the CLAUDE.md file to include references to the AI instruction files that are present in this project. 

The AI instruction files that exist in this project are:
{ai_files_list}

Please add a new section in CLAUDE.md that references ONLY these existing files and instructs Claude to always follow these guidelines when working on this project. Make sure the instructions are clear and emphasize the importance of following these AI instruction files."""

        try:
            # Create a separate task to handle the query
            query_task = asyncio.create_task(_run_enhancement_query(enhancement_prompt, claude_options))

            # Wait for the query with a timeout
            try:
                success = await asyncio.wait_for(query_task, timeout=60.0)
                if success:
                    logger.info(f"Successfully enhanced CLAUDE.md with AI instruction file references")
                return True
            except asyncio.TimeoutError:
                logger.warning("Claude enhancement query timed out after 60 seconds")
                # Cancel the task but don't wait for cancellation
                query_task.cancel()
                await asyncio.sleep(0.1)
                return True  # Return True since the file exists, just not enhanced

        except Exception as query_error:
            logger.warning(f"Error during Claude enhancement query: {query_error}")
            return True  # Return True since the file exists, just not enhanced

    except Exception as e:
        logger.error(f"Error enhancing CLAUDE.md with references: {e}")
        return False


def create_basic_claude_md(project_path: Path, project_name: str, github_url: str):
    """Create a basic CLAUDE.md template."""
    basic_claude_md = f'''# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a {project_name} project created from {github_url}.

## Important AI Instruction Files

When working on this project, always read and follow the guidelines in these files:

1. **AI_DOS_AND_DONTS.md** - General do's and don'ts for AI development
2. **AI_FIGMA_TO_CODE.md** - Guidelines for converting Figma designs to code  
3. **AI_CODING_RULES.md** - Specific coding rules and standards for this project

These files contain mandatory instructions that take precedence over general coding practices.

## Development Commands

Please update this section with relevant build, test, and deployment commands for your project.
'''
    with open(project_path / "CLAUDE.md", "w") as f:
        f.write(basic_claude_md)


def clone_repository(repo_url: str, target_path: Path) -> subprocess.CompletedProcess:
    """Clone a git repository to the specified path."""
    clone_cmd = ["git", "clone", repo_url, str(target_path)]
    return subprocess.run(clone_cmd, capture_output=True, text=True)


def update_gitignore(project_path: Path) -> bool:
    """Update or create .gitignore to exclude .claude directory.
    
    Args:
        project_path: Project directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        gitignore_path = project_path / ".gitignore"
        claude_entry = ".claude/"
        
        if gitignore_path.exists():
            # Read existing .gitignore
            with open(gitignore_path, "r") as f:
                content = f.read()
            
            # Check if .claude is already in .gitignore
            lines = content.splitlines()
            if claude_entry not in lines and ".claude" not in lines:
                # Append .claude/ to existing .gitignore
                with open(gitignore_path, "a") as f:
                    # Add newline if file doesn't end with one
                    if content and not content.endswith('\n'):
                        f.write('\n')
                    f.write(f"{claude_entry}\n")
                logger.info(f"Added {claude_entry} to existing .gitignore")
            else:
                logger.info(f"{claude_entry} already exists in .gitignore")
        else:
            # Create new .gitignore with .claude/
            with open(gitignore_path, "w") as f:
                f.write(f"{claude_entry}\n")
            logger.info(f"Created .gitignore with {claude_entry}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to update .gitignore: {e}")
        return False


def create_git_branch(project_path: Path, branch_name: str) -> subprocess.CompletedProcess:
    """Create and checkout a new git branch."""
    branch_cmd = ["git", "checkout", "-b", branch_name]
    return subprocess.run(branch_cmd, cwd=str(project_path), capture_output=True, text=True)


def checkout_new_branch(project_path: Path, branch_name: str) -> Dict[str, Any]:
    """Create and checkout a new git branch.
    
    Args:
        project_path: Project directory path
        branch_name: Name of the new branch to create
        
    Returns:
        Dict with success status and metadata
    """
    try:
        checkout_result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if checkout_result.returncode != 0:
            logger.warning(f"Failed to create branch: {checkout_result.stderr}")
            return {
                "success": False,
                "error": checkout_result.stderr,
                "branch_name": branch_name
            }
        else:
            logger.info(f"Successfully created and checked out branch: {branch_name}")
            return {
                "success": True,
                "branch_name": branch_name
            }
            
    except Exception as e:
        logger.error(f"Error during branch checkout: {e}")
        return {
            "success": False,
            "error": str(e),
            "branch_name": branch_name
        }


def create_mcp_config_for_project(
    project_path: Path, mcp_servers: List[Any], approval_server_path: Path
):
    """Create mcp-servers.json configuration for a project.
    
    Args:
        project_path: Target project directory
        mcp_servers: List of MCPServerConfig objects
        approval_server_path: Path to the approval server script
    """
    from app.models import MCPServerType
    
    mcp_config = {
        "mcpServers": {
            # Always include approval server from .claude directory
            "approval-server": {
                "command": "python",
                "args": [".claude/mcp_approval_webhook_server.py"],
            }
        }
    }

    # MCP server configurations based on the reference mcp-servers.json
    server_configs = {
        MCPServerType.CONTEXT_MANAGER: {
            "command": "npx",
            "args": ["mcp-context-manager"]
        },
        MCPServerType.CONTEXT7: {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
        },
        MCPServerType.FIGMA: {
            "command": "npx",
            "args": ["-y", "figma-developer-mcp"],
            "requires_token": True,
            "token_arg_format": "--figma-api-key={token}",
            "extra_args": ["--stdio"]
        },
        MCPServerType.GITHUB: {
            "command": "docker",
            "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            "requires_token": True,
            "env_var": "GITHUB_PERSONAL_ACCESS_TOKEN"
        }
    }

    # Add selected MCP servers
    for server in mcp_servers:
        if hasattr(server, 'server_type'):
            server_type = server.server_type
            access_token = getattr(server, 'access_token', None)
            
            if server_type in server_configs:
                config = server_configs[server_type]
                server_dict = {
                    "command": config["command"],
                    "args": config["args"].copy()
                }
                
                # Handle token requirements
                if config.get("requires_token") and access_token:
                    if "token_arg_format" in config:
                        # For Figma, add token as argument
                        server_dict["args"].append(config["token_arg_format"].format(token=access_token))
                        if "extra_args" in config:
                            server_dict["args"].extend(config["extra_args"])
                    elif "env_var" in config:
                        # For GitHub, add as environment variable
                        server_dict["env"] = {
                            config["env_var"]: access_token
                        }
                elif config.get("requires_token"):
                    logger.warning(f"Access token required but not provided for {server_type.value}")
                    continue
                
                # Add to config using the enum value as key
                mcp_config["mcpServers"][server_type.value] = server_dict

    # Write mcp-servers.json to .claude directory
    claude_dir = project_path / ".claude"
    claude_dir.mkdir(exist_ok=True)
    mcp_config_path = claude_dir / "mcp-servers.json"
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    logger.info(
        f"Created .claude/mcp-servers.json with {len(mcp_servers)} servers (plus approval server)"
    )


def copy_mcp_approval_server(project_path: Path, source_path: Path) -> bool:
    """Copy mcp_approval_webhook_server.py to the project directory.
    
    Args:
        project_path: Target project directory
        source_path: Path to the original mcp_approval_webhook_server.py
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not source_path.exists():
            logger.error(f"MCP approval server not found at {source_path}")
            return False
            
        # Copy to .claude directory
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        target_path = claude_dir / "mcp_approval_webhook_server.py"
        import shutil
        shutil.copy2(source_path, target_path)
        
        logger.info(f"Copied MCP approval server to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy MCP approval server: {e}")
        return False


def setup_claude_directory(project_path: Path, webhook_url: str) -> bool:
    """Setup .claude directory with hooks and settings.json from resources.
    
    Args:
        project_path: Project directory path
        webhook_url: Webhook URL for settings configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        
        # Get resources directory
        resources_dir = settings.project_root / "resources"
        
        # Create .claude directory
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        
        # Copy settings.json from resources
        settings_source = resources_dir / "settings.json"
        if settings_source.exists():
            with open(settings_source, "r") as f:
                settings_content = json.load(f)
            
            # Update webhook URL in settings if needed
            if "webhook" in settings_content:
                settings_content["webhook"]["url"] = webhook_url
            
            settings_path = claude_dir / "settings.json"
            with open(settings_path, "w") as f:
                json.dump(settings_content, f, indent=2)
            logger.info("Copied and updated settings.json from resources")
        else:
            logger.warning(f"Settings file not found at {settings_source}")
            
        # Copy hooks directory from resources
        hooks_source = resources_dir / "hooks"
        hooks_dest = claude_dir / "hooks"
        
        if hooks_source.exists() and hooks_source.is_dir():
            # Create hooks directory
            hooks_dest.mkdir(exist_ok=True)
            
            # Copy all hook files
            for hook_file in hooks_source.iterdir():
                if hook_file.is_file():
                    dest_file = hooks_dest / hook_file.name
                    shutil.copy2(hook_file, dest_file)
                    
                    # Make hook files executable if they are scripts
                    if hook_file.suffix in [".py", ".sh"] or hook_file.name in ["pre-commit", "post-commit", "pre-push"]:
                        dest_file.chmod(0o755)
                    
                    logger.info(f"Copied hook file: {hook_file.name}")
            
            logger.info(f"Copied hooks directory from resources")
        else:
            logger.warning(f"Hooks directory not found at {hooks_source}")
            # Create basic hooks directory as fallback
            hooks_dest.mkdir(exist_ok=True)
            
        logger.info(f"Created .claude directory with hooks and settings.json")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup .claude directory: {e}")
        return False


def create_slash_commands(project_path: Path) -> bool:
    """Copy slash commands from resources directory to project.
    
    Args:
        project_path: Project directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    commands_copied = 0
    commands_failed = []
    
    try:
        # Get resources/commands directory
        resources_commands_dir = settings.project_root / "resources" / "commands"
        
        # Create .claude/commands directory
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        
        # Check if resources/commands exists
        if not resources_commands_dir.exists() or not resources_commands_dir.is_dir():
            logger.warning(f"Commands resources directory not found at {resources_commands_dir}")
            # Create a basic command as fallback
            basic_cmd = commands_dir / "help.md"
            with open(basic_cmd, "w") as f:
                f.write("""# /help

Get help with available commands.

## Usage
```
/help
```

This command shows available slash commands and their descriptions.
""")
            logger.info("Created basic help command as fallback")
            return True
            
        # Copy all command files from resources
        command_files = list(resources_commands_dir.glob("*.md"))
        
        if not command_files:
            logger.warning("No command files found in resources/commands")
            return True
            
        for source_file in command_files:
            try:
                dest_file = commands_dir / source_file.name
                shutil.copy2(source_file, dest_file)
                commands_copied += 1
                logger.info(f"Copied command file: {source_file.name}")
            except Exception as e:
                commands_failed.append(f"{source_file.name} ({str(e)})")
                logger.error(f"Failed to copy {source_file.name}: {e}")
                
        # Create commands index based on copied files
        index_commands = []
        for cmd_file in commands_dir.glob("*.md"):
            # Extract command name from filename (remove .md extension)
            cmd_name = cmd_file.stem
            
            # Try to extract description from file content
            description = f"Run {cmd_name} command"
            try:
                with open(cmd_file, "r") as f:
                    lines = f.readlines()
                    # Look for description in YAML frontmatter or first paragraph
                    for i, line in enumerate(lines):
                        if line.startswith("description:"):
                            description = line.replace("description:", "").strip()
                            break
                        elif i > 0 and not line.startswith("#") and not line.startswith("---") and line.strip():
                            # First non-header, non-frontmatter line
                            description = line.strip()
                            if len(description) > 100:
                                description = description[:97] + "..."
                            break
            except Exception as e:
                logger.warning(f"Could not extract description from {cmd_file.name}: {e}")
                
            index_commands.append({
                "name": cmd_name,
                "description": description,
                "file": cmd_file.name
            })
            
        # Write commands index
        if index_commands:
            index_path = commands_dir / "index.json"
            with open(index_path, "w") as f:
                json.dump({"commands": index_commands}, f, indent=2)
            logger.info(f"Created commands index with {len(index_commands)} commands")
            
        logger.info(f"Copied {commands_copied} slash commands to {commands_dir}")
        
        if commands_failed:
            logger.warning(f"Failed to copy {len(commands_failed)} commands: {commands_failed}")
            
        return commands_copied > 0 or not command_files  # Success if we copied something or there was nothing to copy
        
    except Exception as e:
        logger.error(f"Failed to create slash commands: {e}")
        return False


async def run_default_mcp_commands(
    project_path: Path, 
    mcp_servers: Dict[str, Any],
    webhook_url: str
) -> List[Dict[str, Any]]:
    """Run default MCP server initialization commands.
    
    Args:
        project_path: Project directory path
        mcp_servers: MCP servers configuration
        webhook_url: Webhook URL for notifications
        
    Returns:
        List of results from running MCP commands
    """
    results = []
    
    try:
        # Import query processor
        from app.core.query_processor import ClaudeQueryProcessor
        query_processor = ClaudeQueryProcessor()
        
        # Default MCP initialization commands
        default_commands = []
        
        # Add context-manager specific commands if present
        if "context-manager" in mcp_servers:
            default_commands.extend([
                "use context manager mcp and Use setup_context for the current directory",
                "use context manager mcp and Use update_context for the current directory",
                "use context manager mcp and Use persist_context for the current directory"
            ])
            
        # Run each command
        for i, command in enumerate(default_commands, 1):
            try:
                logger.info(f"Running MCP command {i}/{len(default_commands)}: {command}")
                
                task_id = str(uuid4())
                await query_processor.process_query_with_retry(
                    task_id=task_id,
                    prompt=command,
                    webhook_url=webhook_url,
                    session_id=None,
                    conversation_id=None,
                    options={
                        "cwd": str(project_path),
                        "permission_mode": "interactive",
                        "allowed_tools": [
                            "mcp__context-manager",
                            "Read", "Write", "LS"
                        ],
                        "mcp_servers": mcp_servers,
                        "max_turns": 4
                    },
                    timeout=60  # Shorter timeout for init commands
                )
                
                results.append({
                    "command": command,
                    "success": True,
                    "task_id": task_id
                })
                
            except Exception as e:
                logger.error(f"Failed to run MCP command '{command}': {e}")
                results.append({
                    "command": command,
                    "success": False,
                    "error": str(e)
                })
                
        logger.info(
            f"MCP initialization completed: "
            f"{len([r for r in results if r['success']])}/{len(results)} commands succeeded"
        )
        
    except Exception as e:
        logger.error(f"Failed to run default MCP commands: {e}")
        results.append({
            "error": f"MCP initialization failed: {e}",
            "success": False
        })
        
    return results


def copy_default_ai_files(project_path: Path) -> Dict[str, Any]:
    """Copy default AI instruction files from resources directory.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Dict with copy results and metadata
    """
    ai_files_copied = 0
    ai_files_failed = []
    
    # Define the AI instruction files to copy
    ai_instruction_files = [
        "AI_DOS_AND_DONTS.md",
        "ai-coding-rules.md", 
        "ai-figma-code.md"
    ]
    
    try:
        resources_dir = Path(__file__).parent.parent.parent / "resources"
        
        # Create resources directory in the project if it doesn't exist
        project_resources_dir = project_path / ".claude" / "resources"
        project_resources_dir.mkdir(exist_ok=True)
        logger.info(f"Created resources directory at {project_resources_dir}")
        
        for filename in ai_instruction_files:
            source_file = resources_dir / filename
            dest_file = project_path / ".claude" / "resources" / filename
            
            try:
                if source_file.exists():
                    shutil.copy2(source_file, dest_file)
                    ai_files_copied += 1
                    logger.info(f"Copied {filename} to project directory")
                else:
                    ai_files_failed.append(f"{filename} (source not found)")
                    logger.warning(f"Source file not found: {source_file}")
            except Exception as e:
                ai_files_failed.append(f"{filename} ({str(e)})")
                logger.error(f"Failed to copy {filename}: {e}")
                
    except Exception as e:
        logger.error(f"Error setting up AI instruction files: {e}")
        ai_files_failed.append(f"General error: {str(e)}")
        
    return {
        "files_copied": ai_files_copied,
        "files_failed": ai_files_failed,
        "total_files": len(ai_instruction_files),
        "success": ai_files_copied > 0
    }


async def run_claude_init_with_query_processor(
    project_path: Path, 
    task_id: str,
    webhook_url: str
) -> Dict[str, Any]:
    """Run Claude /init command using the query processor.
    
    Args:
        project_path: Project directory path
        task_id: Task ID for the operation
        webhook_url: Webhook URL for notifications
        
    Returns:
        Dict with success status and metadata
    """
    try:
        from app.core.query_processor import ClaudeQueryProcessor
        query_processor = ClaudeQueryProcessor()
        
        await query_processor.process_query_with_retry(
            task_id=task_id,
            prompt="/init",
            webhook_url=webhook_url,
            session_id=None,
            conversation_id=None,
            options={
                "cwd": str(project_path),
                "permission_mode": "bypassPermissions",
                "system_prompt": "Only include files that are in the current directory",
                "allowed_tools": ["Read", "Write", "LS", "Edit", "MultiEdit"],
                "max_turns": 16
            },
            timeout=600  # 5 minute timeout for init
        )
        
        logger.info("Successfully ran Claude /init command")
        return {
            "success": True,
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"Error running Claude /init: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id
        }