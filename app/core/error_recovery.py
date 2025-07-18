"""Error recovery strategies and retry logic."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional, Tuple

import structlog


class ErrorRecoveryManager:
    """Handles error recovery and retry logic for Claude queries."""

    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.recovery_strategies = {
            "timeout": self._handle_timeout_recovery,
            "process_error": self._handle_process_error_recovery,
            "sdk_error": self._handle_sdk_error_recovery,
            "cli_not_found": self._handle_cli_not_found_recovery,
            "webhook_error": self._handle_webhook_error_recovery,
        }

    async def attempt_recovery(
        self,
        error_type: str,
        task_id: str,
        error_context: Dict[str, Any],
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> Tuple[bool, Optional[str]]:
        """Attempt to recover from an error."""
        if retry_count >= max_retries:
            self.logger.error(
                "Maximum retries exceeded",
                task_id=task_id,
                error_type=error_type,
                retry_count=retry_count,
            )
            return False, "Maximum retries exceeded"

        self.logger.info(
            "Attempting error recovery",
            task_id=task_id,
            error_type=error_type,
            retry_count=retry_count,
        )

        if error_type in self.recovery_strategies:
            return await self.recovery_strategies[error_type](task_id, error_context, retry_count)
        else:
            self.logger.warning(
                "No recovery strategy for error type",
                task_id=task_id,
                error_type=error_type,
            )
            return False, f"No recovery strategy for {error_type}"

    async def _handle_timeout_recovery(
        self, task_id: str, error_context: Dict[str, Any], retry_count: int
    ) -> Tuple[bool, Optional[str]]:
        """Handle timeout recovery with exponential backoff."""
        backoff_delay = min(30, 2**retry_count)  # Cap at 30 seconds
        self.logger.info(
            "Timeout recovery: waiting before retry",
            task_id=task_id,
            backoff_delay=backoff_delay,
            retry_count=retry_count,
        )

        await asyncio.sleep(backoff_delay)
        return True, "Timeout recovery: retry after backoff"

    async def _handle_process_error_recovery(
        self, task_id: str, error_context: Dict[str, Any], retry_count: int
    ) -> Tuple[bool, Optional[str]]:
        """Handle process error recovery."""
        exit_code = error_context.get("exit_code", 0)

        # Specific recovery strategies based on exit code
        if exit_code == 1:
            # Generic error - try with reduced options
            self.logger.info(
                "Process error recovery: reducing options",
                task_id=task_id,
                exit_code=exit_code,
            )
            return True, "Process error recovery: retry with reduced options"
        elif exit_code == 2:
            # Permission error - try with different permission mode
            self.logger.info(
                "Process error recovery: changing permission mode",
                task_id=task_id,
                exit_code=exit_code,
            )
            return True, "Process error recovery: retry with different permissions"
        else:
            # Unknown exit code - limited retry
            if retry_count < 1:
                return True, f"Process error recovery: retry for exit code {exit_code}"
            else:
                return False, f"Process error recovery failed: exit code {exit_code}"

    async def _handle_sdk_error_recovery(
        self, task_id: str, error_context: Dict[str, Any], retry_count: int
    ) -> Tuple[bool, Optional[str]]:
        """Handle Claude SDK error recovery."""
        error_message = error_context.get("error_message", "")

        # Check for specific SDK errors
        if "rate limit" in error_message.lower():
            # Rate limit - wait longer
            backoff_delay = min(120, 30 * (retry_count + 1))
            self.logger.info(
                "SDK rate limit recovery: waiting",
                task_id=task_id,
                backoff_delay=backoff_delay,
            )
            await asyncio.sleep(backoff_delay)
            return True, "SDK rate limit recovery: retry after extended wait"
        elif "authentication" in error_message.lower():
            # Auth error - no point in retrying
            return False, "SDK authentication error: no recovery possible"
        elif "quota" in error_message.lower():
            # Quota exceeded - no point in retrying
            return False, "SDK quota exceeded: no recovery possible"
        else:
            # Generic SDK error - try once more
            if retry_count < 1:
                await asyncio.sleep(5)
                return True, "SDK error recovery: retry after short delay"
            else:
                return False, "SDK error recovery failed: unknown error"

    async def _handle_cli_not_found_recovery(
        self, task_id: str, error_context: Dict[str, Any], retry_count: int
    ) -> Tuple[bool, Optional[str]]:
        """Handle CLI not found error recovery."""
        # CLI not found is typically not recoverable without system changes
        return False, "CLI not found: requires system installation"

    async def _handle_webhook_error_recovery(
        self, task_id: str, error_context: Dict[str, Any], retry_count: int
    ) -> Tuple[bool, Optional[str]]:
        """Handle webhook error recovery."""
        status_code = error_context.get("status_code", 500)

        # Retry webhook calls for temporary failures
        if status_code >= 500:
            # Server error - retry
            backoff_delay = min(10, 2**retry_count)
            await asyncio.sleep(backoff_delay)
            return True, f"Webhook server error recovery: retry after {backoff_delay}s"
        elif status_code == 404:
            # Not found - no point in retrying
            return False, "Webhook not found: endpoint unavailable"
        elif status_code >= 400:
            # Client error - limited retry
            if retry_count < 1:
                await asyncio.sleep(2)
                return True, "Webhook client error recovery: retry once"
            else:
                return False, f"Webhook client error: {status_code}"
        else:
            return False, f"Webhook error recovery failed: status {status_code}"