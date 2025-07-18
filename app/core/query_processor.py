"""Main query processing logic with Claude SDK integration."""

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
    query,
)

from app.config import settings
from app.core.error_recovery import ErrorRecoveryManager
from app.core.query_monitor import QueryMonitor
from app.core.session_manager import SessionManager
from app.models import WebhookPayload
from app.services.mcp_integration import get_mcp_config
from app.services.webhook_utils import send_webhook


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
        self.logger.info(
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
        """Get MCP servers configuration."""
        if options and "mcp_servers" in options:
            return options["mcp_servers"]

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

        async for message in query(prompt=prompt, options=claude_options):
            if isinstance(message, Message):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            messages.append(block.text)
                            self.query_monitor.record_message_received(task_id)
                            self.logger.debug(
                                "Received message chunk",
                                task_id=task_id,
                                chunk_length=len(block.text),
                            )

                            # Send intermediate message chunk via webhook
                            await send_webhook(
                                webhook_url,
                                WebhookPayload(
                                    task_id=task_id,
                                    session_id=result_session_id,
                                    conversation_id=conversation_id,
                                    status="processing",
                                    result=block.text,
                                    timestamp=datetime.utcnow(),
                                ),
                                self.query_monitor,
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
                status="failed",
                error=error_msg,
                timestamp=datetime.utcnow(),
            ),
            self.query_monitor,
        )