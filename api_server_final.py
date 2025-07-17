import asyncio
import logging
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, DirectoryPath, Field
import httpx
import subprocess
import os

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

class MCPServer(BaseModel):
    id: str
    name: str
    command: str
    args: List[str]
    connected: bool = False
    icon: Optional[str] = None
    description: Optional[str] = None
    env_vars: Optional[List[str]] = None  # List of required environment variables

class MCPServerConfig(BaseModel):
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

class CustomConnectorRequest(BaseModel):
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

class AIInstructionFiles(BaseModel):
    create_claude_md: bool = Field(default=True, description="Create CLAUDE.md using Claude Code SDK")
    create_ai_dos_and_donts: bool = Field(default=True, description="Create AI_DOS_AND_DONTS.md")
    create_ai_figma_to_code: bool = Field(default=True, description="Create AI_FIGMA_TO_CODE.md")
    create_ai_coding_rules: bool = Field(default=True, description="Create AI_CODING_RULES.md")
    update_claude_md: bool = Field(default=True, description="Update CLAUDE.md with references")

class InitProjectRequest(BaseModel):
    github_repo_url: str = Field(description="GitHub repository URL to clone")
    path: str = Field(description="Path within /projects directory where to create the project")
    project_name: str = Field(description="Name of the project and branch to create")
    mcp_servers: Optional[Dict[str, Any]] = Field(default=None, description="MCP servers configuration for the project")
    ai_instruction_files: Optional[AIInstructionFiles] = Field(default=None, description="AI instruction files to create")

def get_mcp_config():
    """Get MCP configuration from mcp-servers.json"""
    mcp_config_path = Path(__file__).parent / "mcp-servers.json"
    if mcp_config_path.exists():
        with open(mcp_config_path) as f:
            return json.load(f)
    return None

def save_mcp_config(config: Dict[str, Any]):
    """Save MCP configuration to mcp-servers.json"""
    mcp_config_path = Path(__file__).parent / "mcp-servers.json"
    with open(mcp_config_path, 'w') as f:
        json.dump(config, f, indent=2)

def get_available_mcp_servers() -> List[MCPServer]:
    """Get list of available MCP servers with their connection status"""
    # Predefined MCP servers that can be connected
    available_servers = [
        MCPServer(
            id="context-manager",
            name="Context Manager",
            command="npx",
            args=["mcp-context-manager"],
            icon="📋",
            description="Manage context across conversations"
        ),
        MCPServer(
            id="context7",
            name="Context7",
            command="npx",
            args=["-y", "@upstash/context7-mcp"],
            icon="📚",
            description="Access documentation and code examples"
        ),
        MCPServer(
            id="github",
            name="GitHub",
            command="docker",
            args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            icon="https://github.githubassets.com/favicon.ico",
            description="Access GitHub repositories and issues",
            env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"]
        ),
        MCPServer(
            id="figma",
            name="Figma",
            command="npx",
            args=["-y", "figma-developer-mcp"],
            icon="https://static.figma.com/app/icon/1/favicon.svg",
            description="Access Figma designs and components",
            env_vars=["FIGMA_API_KEY"]
        )
    ]
    
    # Check current configuration to see which are connected
    current_config = get_mcp_config()
    if current_config and "mcpServers" in current_config:
        connected_ids = set()
        for server_id, config in current_config["mcpServers"].items():
            # Skip the approval server
            if server_id == "approval-server":
                continue
            
            connected_ids.add(server_id)
            
            # If this server is not in our predefined list, add it as a custom server
            if not any(s.id == server_id for s in available_servers):
                custom_server = MCPServer(
                    id=server_id,
                    name=server_id.replace('-', ' ').title(),
                    command=config.get("command", ""),
                    args=config.get("args", []),
                    connected=True,
                    icon="🔧",  # Custom connector icon
                    description="Custom MCP connector"
                )
                available_servers.append(custom_server)
        
        # Update connection status for predefined servers
        for server in available_servers:
            if server.id in connected_ids:
                server.connected = True
    
    return available_servers

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
        # Send the user's prompt as a webhook to display in chat
        await send_webhook(webhook_url, WebhookPayload(
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            status="user_message",
            result=prompt,
            timestamp=datetime.utcnow()
        ))
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

        logger.info(f"Options: {claude_options_dict}")
        
        # Handle interactive permission mode with MCP
        if use_mcp:
            # Use project-specific MCP config if provided in options, otherwise use global config
            if options and 'mcp_servers' in options:
                mcp_servers = options['mcp_servers']
                logger.info(f"Task {task_id}: Using project-specific MCP config")
            else:
                mcp_config = get_mcp_config()
                mcp_servers = mcp_config.get("mcpServers", {}) if mcp_config else {}
                logger.info(f"Task {task_id}: Using global MCP config")
            
            if mcp_servers:
                logger.info(f"Task {task_id}: Using MCP interactive permissions")
                claude_options_dict['permission_mode'] = None  # Let MCP handle permissions
                claude_options_dict['permission_prompt_tool_name'] = "mcp__approval-server__permissions__approve"
                claude_options_dict['mcp_servers'] = mcp_servers
                # Add context-manager tool when using MCP
                claude_options_dict['allowed_tools'].append("mcp__context-manager")
                claude_options_dict['allowed_tools'].append("mcp__context7")
                claude_options_dict['allowed_tools'].append("mcp__github")
                claude_options_dict['allowed_tools'].append("mcp__figma")
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
                            
                            # Send intermediate message chunk via webhook
                            await send_webhook(webhook_url, WebhookPayload(
                                task_id=task_id,
                                session_id=result_session_id,
                                conversation_id=conversation_id,
                                status="processing",
                                result=block.text,
                                timestamp=datetime.utcnow()
                            ))
            
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

@app.get("/mcp/servers", response_model=List[MCPServer])
async def list_mcp_servers():
    """List all available MCP servers and their connection status"""
    return get_available_mcp_servers()

@app.post("/mcp/connect/{server_id}")
async def connect_mcp_server(server_id: str, custom_config: Optional[CustomConnectorRequest] = None):
    """Connect to an MCP server"""
    try:
        # Get current configuration
        config = get_mcp_config() or {"mcpServers": {}}
        
        # Always keep approval server
        if "approval-server" not in config["mcpServers"]:
            config["mcpServers"]["approval-server"] = {
                "command": "python",
                "args": ["mcp_approval_webhook_server.py"]
            }
        
        # Check if this is a custom connector (has command and args)
        if custom_config and custom_config.command and custom_config.args:
            # Use custom configuration provided
            server_config = {
                "command": custom_config.command,
                "args": custom_config.args
            }
            if custom_config.env:
                server_config["env"] = custom_config.env
            config["mcpServers"][server_id] = server_config
        else:
            # Find the server in predefined list
            available_servers = get_available_mcp_servers()
            server = next((s for s in available_servers if s.id == server_id), None)
            
            if not server:
                raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
            
            # Add the server configuration
            server_config = {
                "command": server.command,
                "args": server.args.copy()  # Copy to avoid modifying original
            }
            
            # Special handling for Figma
            if server_id == "figma" and custom_config and custom_config.env and "FIGMA_API_KEY" in custom_config.env:
                server_config["args"].extend([
                    f"--figma-api-key={custom_config.env['FIGMA_API_KEY']}",
                    "--stdio"
                ])
            else:
                # Add env if provided in request for other servers
                if custom_config and custom_config.env:
                    server_config["env"] = custom_config.env
            
            config["mcpServers"][server_id] = server_config
        
        # Save configuration
        save_mcp_config(config)
        
        return {"status": "connected", "server_id": server_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mcp/disconnect/{server_id}")
async def disconnect_mcp_server(server_id: str):
    """Disconnect from an MCP server"""
    try:
        config = get_mcp_config()
        if not config or "mcpServers" not in config:
            raise HTTPException(status_code=404, detail="No MCP configuration found")
        
        if server_id not in config["mcpServers"]:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not connected")
        
        # Don't allow disconnecting the approval server
        if server_id == "approval-server":
            raise HTTPException(status_code=400, detail="Cannot disconnect approval server")
        
        # Remove the server from configuration
        del config["mcpServers"][server_id]
        
        # Save configuration
        save_mcp_config(config)
        
        return {"status": "disconnected", "server_id": server_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_ai_instruction_files(project_path: Path, ai_files: AIInstructionFiles):
    """Create AI instruction files in the project directory"""
    
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
        with open(project_path / "AI_DOS_AND_DONTS.md", 'w') as f:
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
        with open(project_path / "AI_FIGMA_TO_CODE.md", 'w') as f:
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
        with open(project_path / "AI_CODING_RULES.md", 'w') as f:
            f.write(ai_coding_rules_content)

async def run_claude_init_command(project_path: Path):
    """Use Claude Code SDK to create CLAUDE.md with /init command"""
    try:
        # Check if CLAUDE.md already exists
        logger.info(f"Checking if CLAUDE.md exists in {project_path}")
        claude_md_path = project_path / "CLAUDE.md"
        logger.info(f"CLAUDE.md path: {claude_md_path}")
        existing_claude_md = claude_md_path.exists()
        logger.info(f"CLAUDE.md exists: {existing_claude_md}")
        
        # Use Claude Code SDK to run /init command
        claude_options = ClaudeCodeOptions(
            cwd=str(project_path),
            allowed_tools=["Read", "Write", "LS", "Edit", "MultiEdit"],
            max_turns=16,
            permission_mode='bypassPermissions'
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
                    if claude_md_path.exists():
                        logger.info(f"CLAUDE.md exists: {claude_md_path}")
                    else:
                        logger.info(f"CLAUDE.md does not exist: {claude_md_path}")
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

async def _run_claude_query(prompt: str, options: ClaudeCodeOptions):
    """Helper function to run Claude query in isolation"""    
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            logger.info(f"Claude /init response: {block.text}")
            
            # Check if ResultMessage indicates completion
            if isinstance(message, ResultMessage):
                if hasattr(message, 'result'):
                    return True
        return True
    except Exception as e:
        logger.warning(f"Error in Claude query helper: {e}")
        return False

async def _run_enhancement_query(prompt: str, options: ClaudeCodeOptions):
    """Helper function to run Claude enhancement query in isolation"""
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            logger.info(f"Claude enhancement response: {block.text[:100]}...")
            
            # Check if ResultMessage indicates success
            if isinstance(message, ResultMessage):
                if hasattr(message, 'result'):
                    return True
        
        return True
    except Exception as e:
        logger.warning(f"Error in Claude enhancement helper: {e}")
        return False

async def update_claude_md_with_references(project_path: Path):
    """Use Claude Code SDK to enhance CLAUDE.md with AI instruction file references"""
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
            permission_mode='acceptEdits'
        )
        
        # Dynamically detect which AI instruction files exist
        ai_files_present = []
        ai_file_descriptions = {
            "AI_DOS_AND_DONTS.md": "General do's and don'ts for AI development",
            "AI_FIGMA_TO_CODE.md": "Guidelines for converting Figma designs to code",
            "AI_CODING_RULES.md": "Specific coding rules and standards for this project"
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

@app.post("/init-project")
async def init_project(request: InitProjectRequest):
    """Initialize a new project by cloning a repository and creating a branch"""
    try:
        # Create the base projects directory within PROJECT_ROOT
        projects_dir = Path(PROJECT_ROOT) / "projects"
        projects_dir.mkdir(exist_ok=True)
        
        # Create the full project path
        project_path = projects_dir / request.path
        
        # Check if directory already exists
        if project_path.exists():
            raise HTTPException(
                status_code=400, 
                detail=f"Directory already exists: {project_path}"
            )
        
        # Create the directory
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {project_path}")
        
        # Clone the repository
        clone_cmd = ["git", "clone", request.github_repo_url, str(project_path)]
        clone_result = subprocess.run(
            clone_cmd, 
            capture_output=True, 
            text=True
        )
        
        if clone_result.returncode != 0:
            # Clean up directory on failure
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clone repository: {clone_result.stderr}"
            )
        
        logger.info(f"Cloned repository: {request.github_repo_url} to {project_path}")
        
        # Create and checkout new branch
        branch_cmd = ["git", "checkout", "-b", request.project_name]
        branch_result = subprocess.run(
            branch_cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        
        if branch_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create branch: {branch_result.stderr}"
            )
        
        logger.info(f"Created and checked out branch: {request.project_name}")
        
        # Create mcp-servers.json if MCP servers were provided
        if request.mcp_servers:
            mcp_config = {
                "mcpServers": {
                    # Always include approval server
                    "approval-server": {
                        "command": "python",
                        "args": [str(Path(__file__).parent / "mcp_approval_webhook_server.py")]
                    }
                }
            }
            
            # Add selected MCP servers
            for server_id, server_config in request.mcp_servers.items():
                if server_id == "figma" and "env" in server_config and "FIGMA_API_KEY" in server_config["env"]:
                    # Special handling for Figma - add API key to args
                    figma_config = server_config.copy()
                    figma_config["args"] = figma_config["args"].copy()
                    figma_config["args"].extend([
                        f"--figma-api-key={server_config['env']['FIGMA_API_KEY']}",
                        "--stdio"
                    ])
                    # Remove env since it's now in args
                    if "env" in figma_config:
                        del figma_config["env"]
                    mcp_config["mcpServers"][server_id] = figma_config
                else:
                    mcp_config["mcpServers"][server_id] = server_config
            
            # Write mcp-servers.json to project directory
            mcp_config_path = project_path / "mcp-servers.json"
            with open(mcp_config_path, 'w') as f:
                json.dump(mcp_config, f, indent=2)
            
            logger.info(f"Created mcp-servers.json with {len(request.mcp_servers)} servers (plus approval server)")
        
        # Handle AI instruction files
        ai_files_created = []
        claude_init_success = False
        
        if request.ai_instruction_files:
            ai_files = request.ai_instruction_files
            
            # Create AI instruction files
            if any([ai_files.create_ai_dos_and_donts, ai_files.create_ai_figma_to_code, ai_files.create_ai_coding_rules]):
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
                    basic_claude_md = f'''# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a {request.project_name} project created from {request.github_repo_url}.

## Important AI Instruction Files

When working on this project, always read and follow the guidelines in these files:

1. **AI_DOS_AND_DONTS.md** - General do's and don'ts for AI development
2. **AI_FIGMA_TO_CODE.md** - Guidelines for converting Figma designs to code  
3. **AI_CODING_RULES.md** - Specific coding rules and standards for this project

These files contain mandatory instructions that take precedence over general coding practices.

## Development Commands

Please update this section with relevant build, test, and deployment commands for your project.
'''
                    with open(project_path / "CLAUDE.md", 'w') as f:
                        f.write(basic_claude_md)
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
            try:
                logger.info("Running context manager initialization prompts...")
                
                # Run the 3 context manager prompts
                context_prompts = [
                    "use context manager mcp and Use setup_context for the current directory",
                    "use context manager mcp and Use update_context for the current directory", 
                    "use context manager mcp and Use persist_context for the current directory"
                ]
                mcp_config_path = project_path / "mcp-servers.json"
                if mcp_config_path.exists():
                    with open(mcp_config_path, 'r') as f:
                        mcp_config = json.load(f)
                    mcp_servers = mcp_config.get("mcpServers", {})
                    logger.info(f"MCP servers: {mcp_servers}")
                    
                for i, prompt in enumerate(context_prompts, 1):
                    try:
                        logger.info(f"Running context manager prompt {i}: {prompt}")
                        # Generate task ID for this context manager prompt
                        task_id = str(uuid4())
                        result = await process_query(
                            task_id=task_id,
                            prompt=prompt,
                            webhook_url="http://localhost:8002/webhook",  # Use standard webhook URL
                            session_id=None,
                            conversation_id=None,
                            options={
                                'cwd': str(project_path),
                                'permission_mode': 'interactive',  # Use interactive mode to enable MCP
                                'allowed_tools': ["mcp__context-manager", "Read", "Write", "LS", "Edit", "MultiEdit"],
                                'mcp_servers': mcp_servers
                            }
                        )
                        context_manager_results.append({
                            "prompt": prompt,
                            "success": True,
                            "result": result
                        })
                        logger.info(f"Context manager prompt {i} completed successfully")
                    except Exception as e:
                        logger.error(f"Context manager prompt {i} failed: {e}")
                        context_manager_results.append({
                            "prompt": prompt,
                            "success": False,
                            "error": str(e)
                        })
                        
                logger.info(f"Context manager initialization completed: {len([r for r in context_manager_results if r['success']])}/3 prompts succeeded")
                
            except Exception as e:
                logger.error(f"Context manager initialization failed: {e}")
                context_manager_results.append({
                    "error": f"Context manager initialization failed: {e}",
                    "success": False
                })
        
        return {
            "status": "success",
            "message": f"Project initialized successfully",
            "project_path": str(project_path),
            "branch": request.project_name,
            "mcp_servers_count": len(request.mcp_servers) + 1 if request.mcp_servers else 0,
            "ai_files_created": ai_files_created,
            "claude_init_success": claude_init_success,
            "context_manager_results": context_manager_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Claude Code Fire-and-Forget API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Submit a query with webhook notification",
            "GET /health": "Health check",
            "GET /mcp/servers": "List available MCP servers",
            "POST /mcp/connect/{server_id}": "Connect to an MCP server",
            "DELETE /mcp/disconnect/{server_id}": "Disconnect from an MCP server",
            "POST /init-project": "Initialize a project by cloning a repo and creating a branch"
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