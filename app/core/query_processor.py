"""Main query processing logic with Claude SDK integration.

WEBHOOK FORMAT SPECIFICATION:

All webhooks now include a `type` field to categorize the webhook:

1. STATUS WEBHOOKS (type: "status"):
   - user_message: Initial prompt submission
   - completed: Final result
   - failed: Error occurred
   
2. QUERY WEBHOOKS (type: "query"):
   - All intermediate steps during Claude conversation
   - Includes detailed message parsing
   
3. ERROR WEBHOOKS (type: "error"):
   - Processing errors with detailed error information

Standard Webhook Payload Structure:
{
    "task_id": "string",
    "session_id": "string|null",
    "conversation_id": "string|null", 
    "type": "status|query|error",
    "status": "string",
    "result": "string|null",
    "error": "string|null",
    "message_type": "string|null",      // "AssistantMessage", "UserMessage", "ResultMessage", etc.
    "content_type": "string|null",      // "text", "tool_use", "tool_result", "result", etc.
    "tool_name": "string|null",         // Tool name for tool_use blocks
    "tool_input": "object|null",        // Tool input parameters
    
    // ResultMessage specific fields (only present for ResultMessage types)
    "subtype": "string|null",           // "success", "error", etc.
    "duration_ms": "number|null",       // Total execution duration
    "duration_api_ms": "number|null",   // API call duration  
    "is_error": "boolean|null",         // Whether result indicates error
    "num_turns": "number|null",         // Number of conversation turns
    "total_cost_usd": "number|null",    // Total cost in USD
    "usage": "object|null",             // Token usage and metrics
    
    "timestamp": "datetime"
}

Example Query Webhook (tool use):
{
    "task_id": "abc123",
    "session_id": "session456", 
    "type": "query",
    "status": "processing",
    "message_type": "AssistantMessage",
    "content_type": "tool_use",
    "tool_name": "Bash",
    "tool_input": {"command": "git diff"},
    "result": "Tool: Bash",
    "timestamp": "2025-01-01T12:00:00Z"
}

Example Query Webhook (tool result):
{
    "task_id": "abc123",
    "session_id": "session456",
    "type": "query", 
    "status": "processing",
    "message_type": "UserMessage",
    "content_type": "tool_result",
    "result": "diff output...",
    "timestamp": "2025-01-01T12:00:01Z"
}

Example Query Webhook (text response):
{
    "task_id": "abc123",
    "session_id": "session456",
    "type": "query",
    "status": "processing", 
    "message_type": "AssistantMessage",
    "content_type": "text",
    "result": "Removed the scroll indicator component...",
    "timestamp": "2025-01-01T12:00:02Z"
}

Example Query Webhook (result message with metrics):
{
    "task_id": "abc123",
    "session_id": "2c3f3da1-3ad9-43e1-a669-6991227c25f6",
    "type": "query",
    "status": "processing",
    "message_type": "ResultMessage", 
    "content_type": "result",
    "result": "Removed the scroll indicator component. Want me to commit these changes?",
    "subtype": "success",
    "duration_ms": 5371,
    "duration_api_ms": 8690,
    "is_error": false,
    "num_turns": 32,
    "total_cost_usd": 0.09051405,
    "usage": {
        "input_tokens": 10,
        "cache_creation_input_tokens": 21649,
        "cache_read_input_tokens": 20785,
        "output_tokens": 100,
        "server_tool_use": {
            "web_search_requests": 0
        },
        "service_tier": "standard"
    },
    "timestamp": "2025-01-01T12:00:03Z"
}
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog
from claude_code_sdk import (
    AssistantMessage,
    CLINotFoundError,
    ClaudeCodeOptions,
    ClaudeSDKError,
    Message,
    ProcessError,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from app.config import settings
from app.core.error_recovery import ErrorRecoveryManager
from app.core.query_monitor import QueryMonitor
from app.core.session_manager import SessionManager
from app.models import WebhookPayload
from app.services.mcp_integration import get_mcp_config
from app.services.webhook_utils import send_webhook

from app.logging_config import setup_logging

# Setup logging
logger = setup_logging()

class ClaudeQueryProcessor:
    """Handles Claude query processing with proper error handling and session management."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.active_queries: Dict[str, asyncio.Task] = {}
        self.session_manager = SessionManager()
        self.query_monitor = QueryMonitor()
        self.error_recovery = ErrorRecoveryManager()

    async def process_query_with_retry(
        self,
        task_id: str,
        prompt: str,
        webhook_url: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        max_retries: int = 3,
    ):
        """Process Claude query with retry logic and error recovery."""
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                await self.process_query_with_timeout(
                    task_id, prompt, webhook_url, session_id, conversation_id, options, timeout
                )
                return  # Success - exit retry loop

            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)

                self.logger.warning(
                    "Query attempt failed",
                    task_id=task_id,
                    retry_count=retry_count,
                    error_type=error_type,
                    error=str(e),
                )

                if retry_count >= max_retries:
                    self.logger.error(
                        "All retry attempts exhausted",
                        task_id=task_id,
                        max_retries=max_retries,
                        final_error=str(e),
                    )
                    break

                # Attempt error recovery
                can_recover, recovery_message = await self.error_recovery.attempt_recovery(
                    error_type,
                    task_id,
                    self._build_error_context(e),
                    retry_count,
                    max_retries,
                )

                if can_recover:
                    self.logger.info(
                        "Error recovery successful, retrying",
                        task_id=task_id,
                        retry_count=retry_count + 1,
                        recovery_message=recovery_message,
                    )
                    retry_count += 1
                else:
                    self.logger.error(
                        "Error recovery failed, aborting",
                        task_id=task_id,
                        retry_count=retry_count,
                        recovery_message=recovery_message,
                    )
                    break

        # If we reach here, all retries failed
        if last_error:
            raise last_error

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for recovery strategy."""
        if isinstance(error, asyncio.TimeoutError):
            return "timeout"
        elif isinstance(error, ProcessError):
            return "process_error"
        elif isinstance(error, ClaudeSDKError):
            return "sdk_error"
        elif isinstance(error, CLINotFoundError):
            return "cli_not_found"
        elif "webhook" in str(error).lower():
            return "webhook_error"
        else:
            return "unknown_error"

    def _build_error_context(self, error: Exception) -> Dict[str, Any]:
        """Build error context for recovery strategies."""
        context = {"error_message": str(error), "error_type": type(error).__name__}

        if isinstance(error, ProcessError):
            context["exit_code"] = error.exit_code

        return context

    async def process_query_with_timeout(
        self,
        task_id: str,
        prompt: str,
        webhook_url: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ):
        """Process Claude query with timeout and proper error handling."""
        # Start monitoring
        self.query_monitor.start_query_monitoring(task_id)

        # Track session if provided
        if session_id:
            self.session_manager.track_session(session_id, conversation_id=conversation_id)

        success = False
        try:
            # Create the query task
            query_task = asyncio.create_task(
                self._process_query_internal(
                    task_id, prompt, webhook_url, session_id, conversation_id, options
                )
            )

            # Store the task for potential cancellation
            self.active_queries[task_id] = query_task

            # Wait for completion with timeout
            try:
                await asyncio.wait_for(query_task, timeout=timeout)
                success = True
            except asyncio.TimeoutError:
                self.logger.warning(
                    "Query timed out",
                    task_id=task_id,
                    timeout=timeout,
                )
                self.query_monitor.record_error(
                    task_id, "timeout", f"Query timed out after {timeout} seconds"
                )
                query_task.cancel()
                await self._send_error_webhook(
                    webhook_url,
                    task_id,
                    session_id,
                    conversation_id,
                    f"Query timed out after {timeout} seconds",
                )

        except Exception as e:
            self.logger.error(
                "Error in query processing",
                task_id=task_id,
                error=str(e),
                exc_info=True,
            )
            self.query_monitor.record_error(task_id, "processing_error", str(e))
            await self._send_error_webhook(
                webhook_url, task_id, session_id, conversation_id, str(e)
            )
        finally:
            # Complete monitoring
            self.query_monitor.complete_query_monitoring(task_id, success)

            # Clean up the task reference
            self.active_queries.pop(task_id, None)

    async def _process_query_internal(
        self,
        task_id: str,
        prompt: str,
        webhook_url: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        """Internal query processing with structured error handling."""
        logger.info(
            "Starting query processing",
            task_id=task_id,
            session_id=session_id,
            conversation_id=conversation_id,
            prompt_length=len(prompt),
        )

        try:
            # Send user message webhook
            await send_webhook(
                webhook_url,
                WebhookPayload(
                    task_id=task_id,
                    session_id=session_id,
                    conversation_id=conversation_id,
                    type="status",
                    status="user_message",
                    result=prompt,
                    timestamp=datetime.utcnow(),
                ),
                self.query_monitor,
            )

            # Build Claude options with proper configuration
            claude_options = self._build_claude_options(options, session_id)

            # Execute query with proper message handling
            result_session_id, result_text = await self._execute_claude_query(
                task_id, prompt, claude_options, webhook_url, session_id, conversation_id
            )

            # Send success webhook
            await send_webhook(
                webhook_url,
                WebhookPayload(
                    task_id=task_id,
                    session_id=result_session_id,
                    conversation_id=conversation_id,
                    type="status",
                    status="completed",
                    result=result_text,
                    timestamp=datetime.utcnow(),
                ),
                self.query_monitor,
            )

            self.logger.info(
                "Query completed successfully",
                task_id=task_id,
                session_id=result_session_id,
                result_length=len(result_text) if result_text else 0,
            )

        except CLINotFoundError as e:
            error_msg = "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            self.logger.error(
                "Claude CLI not found",
                task_id=task_id,
                error=error_msg,
            )
            await self._send_error_webhook(webhook_url, task_id, session_id, conversation_id, error_msg)

        except ProcessError as e:
            error_msg = f"Claude process failed with exit code {e.exit_code}"
            self.logger.error(
                "Claude process error",
                task_id=task_id,
                exit_code=e.exit_code,
                error=str(e),
            )
            await self._send_error_webhook(webhook_url, task_id, session_id, conversation_id, error_msg)

        except ClaudeSDKError as e:
            error_msg = f"Claude SDK error: {str(e)}"
            self.logger.error(
                "Claude SDK error",
                task_id=task_id,
                error=str(e),
                exc_info=True,
            )
            await self._send_error_webhook(webhook_url, task_id, session_id, conversation_id, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(
                "Unexpected error in query processing",
                task_id=task_id,
                error=str(e),
                exc_info=True,
            )
            await self._send_error_webhook(webhook_url, task_id, session_id, conversation_id, error_msg)

    def _build_claude_options(
        self, options: Optional[Dict[str, Any]], session_id: Optional[str]
    ) -> ClaudeCodeOptions:
        """Build Claude options with proper defaults and MCP configuration."""
        # Default options
        claude_options_dict = {
            "cwd": options.get("cwd", str(settings.project_root)) if options else str(settings.project_root),
            "allowed_tools": options.get("allowed_tools", settings.claude_default_tools)
            if options
            else settings.claude_default_tools,
            "max_turns": options.get("max_turns", settings.claude_max_turns)
            if options
            else settings.claude_max_turns,
            "model": settings.claude_model,
            "resume": session_id,
        }

        self.logger.info(f"Claude options: {claude_options_dict}")

        # Handle permission modes and MCP configuration
        permission_mode = options.get("permission_mode", "acceptEdits") if options else "acceptEdits"
        use_mcp = permission_mode == "interactive"

        if use_mcp:
            mcp_servers = self._get_mcp_servers(options)
            if mcp_servers:
                self.logger.info(
                    "Configuring MCP interactive permissions",
                    mcp_servers=list(mcp_servers.keys()),
                )
                claude_options_dict.update(
                    {
                        "permission_mode": None,
                        "permission_prompt_tool_name": "mcp__approval-server__permissions__approve",
                        "mcp_servers": mcp_servers,
                    }
                )
                # Add MCP tools
                claude_options_dict["allowed_tools"].extend(
                    ["mcp__context-manager", "mcp__context7", "mcp__github", "mcp__figma"]
                )
            else:
                self.logger.warning("MCP config not found, falling back to acceptEdits")
                claude_options_dict["permission_mode"] = "acceptEdits"
        else:
            claude_options_dict["permission_mode"] = permission_mode

        return ClaudeCodeOptions(**claude_options_dict)

    def _get_mcp_servers(self, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get MCP servers configuration from project directory."""
        if options and "mcp_servers" in options:
            return options["mcp_servers"]
            
        # If cwd is provided in options, try to load mcp-servers.json from that directory
        if options and "cwd" in options:
            try:
                from pathlib import Path
                project_dir = Path(options["cwd"])
                mcp_config_file = project_dir / ".claude" / "mcp-servers.json"
                
                if mcp_config_file.exists():
                    import json
                    with open(mcp_config_file, "r") as f:
                        mcp_config = json.load(f)
                        self.logger.info(
                            f"Loaded MCP servers from project: {mcp_config_file}",
                            servers=list(mcp_config.get("mcpServers", {}).keys())
                        )
                        return mcp_config.get("mcpServers", {})
                else:
                    self.logger.warning(f"No mcp-servers.json found at {mcp_config_file}")
            except Exception as e:
                self.logger.error(f"Error loading project MCP config: {e}")
                
        # Fallback to global MCP config
        mcp_config = get_mcp_config()
        return mcp_config.get("mcpServers", {}) if mcp_config else {}

    async def _execute_claude_query(
        self,
        task_id: str,
        prompt: str,
        claude_options: ClaudeCodeOptions,
        webhook_url: str,
        session_id: Optional[str],
        conversation_id: Optional[str],
    ) -> Tuple[Optional[str], str]:
        """Execute Claude query with proper message handling."""
        messages = []
        result_session_id = session_id
        final_result = None
        logger.info(f"Prompt from _execute_claude_query: {prompt}")
        
        async for message in query(prompt=prompt, options=claude_options):
            logger.info(f"Message: {message}")
            
            # Send webhook for all message types
            await self._send_message_webhook(
                webhook_url, task_id, result_session_id, conversation_id, message
            )
            
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            messages.append(block.text)
                            self.query_monitor.record_message_received(task_id)
                            logger.info(
                                "Received message chunk",
                                task_id=task_id,
                                chunk_length=len(block.text),
                            )

            # Capture session ID and final result from ResultMessage
            if isinstance(message, ResultMessage):
                if hasattr(message, "session_id"):
                    result_session_id = message.session_id
                    self.logger.info(
                        "Session ID captured",
                        task_id=task_id,
                        session_id=result_session_id,
                    )
                if hasattr(message, "result"):
                    final_result = message.result
                    self.logger.info(
                        "Final result captured",
                        task_id=task_id,
                        result_length=len(final_result) if final_result else 0,
                    )

        # Use final_result if available, otherwise join messages
        result_text = final_result if final_result else "\n".join(messages)
        return result_session_id, result_text

    async def _send_message_webhook(
        self,
        webhook_url: str,
        task_id: str,
        session_id: Optional[str],
        conversation_id: Optional[str],
        message: Any,
    ):
        """Send webhook for all message types with detailed information."""
        message_type = type(message).__name__
        
        # Base payload
        payload_data = {
            "task_id": task_id,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "type": "query",
            "status": "processing",
            "message_type": message_type,
            "timestamp": datetime.utcnow(),
        }
        
        # Handle different message types
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    await send_webhook(
                        webhook_url,
                        WebhookPayload(
                            **payload_data,
                            content_type="text",
                            result=block.text,
                        ),
                        self.query_monitor,
                    )
                elif isinstance(block, ToolUseBlock):
                    await send_webhook(
                        webhook_url,
                        WebhookPayload(
                            **payload_data,
                            content_type="tool_use",
                            tool_name=block.name,
                            tool_input=block.input,
                            result=f"Tool: {block.name}",
                        ),
                        self.query_monitor,
                    )
                    
        elif isinstance(message, UserMessage):
            for content_item in message.content:
                if isinstance(content_item, dict):
                    # Handle tool results
                    if content_item.get("type") == "tool_result":
                        tool_use_id = content_item.get("tool_use_id", "")
                        tool_content = content_item.get("content", "")
                        is_error = content_item.get("is_error", False)
                        
                        await send_webhook(
                            webhook_url,
                            WebhookPayload(
                                **payload_data,
                                content_type="tool_result",
                                result=str(tool_content),
                                error=str(tool_content) if is_error else None,
                            ),
                            self.query_monitor,
                        )
                    else:
                        # Handle other dict content
                        await send_webhook(
                            webhook_url,
                            WebhookPayload(
                                **payload_data,
                                content_type="dict",
                                result=str(content_item),
                            ),
                            self.query_monitor,
                        )
                else:
                    # Handle string content
                    await send_webhook(
                        webhook_url,
                        WebhookPayload(
                            **payload_data,
                            content_type="text",
                            result=str(content_item),
                        ),
                        self.query_monitor,
                    )
                    
        elif isinstance(message, ResultMessage):
            await send_webhook(
                webhook_url,
                WebhookPayload(
                    **payload_data,
                    content_type="result",
                    result=getattr(message, "result", None),
                    subtype=getattr(message, "subtype", None),
                    duration_ms=getattr(message, "duration_ms", None),
                    duration_api_ms=getattr(message, "duration_api_ms", None),
                    is_error=getattr(message, "is_error", None),
                    num_turns=getattr(message, "num_turns", None),
                    total_cost_usd=getattr(message, "total_cost_usd", None),
                    usage=getattr(message, "usage", None),
                ),
                self.query_monitor,
            )
        else:
            # Handle any other message types
            await send_webhook(
                webhook_url,
                WebhookPayload(
                    **payload_data,
                    content_type="unknown",
                    result=str(message),
                ),
                self.query_monitor,
            )

    async def _send_error_webhook(
        self,
        webhook_url: str,
        task_id: str,
        session_id: Optional[str],
        conversation_id: Optional[str],
        error_msg: str,
    ):
        """Send error webhook notification."""
        await send_webhook(
            webhook_url,
            WebhookPayload(
                task_id=task_id,
                session_id=session_id,
                conversation_id=conversation_id,
                type="error",
                status="failed",
                error=error_msg,
                timestamp=datetime.utcnow(),
            ),
            self.query_monitor,
        )