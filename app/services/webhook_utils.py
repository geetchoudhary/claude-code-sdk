"""Webhook notification utilities."""

from typing import Any, Dict, Optional

import httpx
import structlog

from app.config import settings
from app.core.query_monitor import QueryMonitor
from app.models import ProjectInitStatus, ProjectInitWebhookPayload, WebhookPayload

logger = structlog.get_logger(__name__)


async def send_webhook(
    webhook_url: str,
    payload: WebhookPayload,
    query_monitor: Optional[QueryMonitor] = None,
):
    """Send webhook with proper error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload.model_dump(mode="json"),
                timeout=settings.webhook_timeout,
            )

            # Record webhook call if monitor provided
            if query_monitor:
                query_monitor.record_webhook_sent(
                    payload.task_id, webhook_url, response.status_code
                )

            if response.status_code >= 400:
                logger.error(
                    "Webhook failed",
                    url=webhook_url,
                    status_code=response.status_code,
                    response=response.text,
                    task_id=payload.task_id,
                )
            else:
                logger.debug(
                    "Webhook sent successfully",
                    url=webhook_url,
                    status_code=response.status_code,
                    task_id=payload.task_id,
                )
    except Exception as e:
        logger.error(
            "Failed to send webhook",
            url=webhook_url,
            error=str(e),
            task_id=payload.task_id,
        )
        # Record webhook error if monitor provided
        if query_monitor:
            query_monitor.record_webhook_sent(payload.task_id, webhook_url, 500)


async def send_project_init_webhook(
    webhook_url: str,
    task_id: str,
    step_name: str,
    completion_message: str,
    status: ProjectInitStatus,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Send webhook for project initialization steps."""
    payload = ProjectInitWebhookPayload(
        task_id=task_id,
        step_name=step_name,
        completion_message=completion_message,
        status=status,
        error=error,
        metadata=metadata,
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload.model_dump(mode="json"),
                timeout=settings.webhook_timeout,
            )

            if response.status_code >= 400:
                logger.error(
                    "Project init webhook failed",
                    url=webhook_url,
                    status_code=response.status_code,
                    response=response.text,
                    task_id=task_id,
                    step_name=step_name,
                )
            else:
                logger.debug(
                    "Project init webhook sent successfully",
                    url=webhook_url,
                    status_code=response.status_code,
                    task_id=task_id,
                    step_name=step_name,
                )
    except Exception as e:
        logger.error(
            "Failed to send project init webhook",
            url=webhook_url,
            error=str(e),
            task_id=task_id,
            step_name=step_name,
        )