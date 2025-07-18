"""Query performance monitoring and tracking."""

from datetime import datetime
from typing import Any, Dict, List

import structlog


class QueryMonitor:
    """Monitors query performance and usage patterns."""

    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.query_metrics: Dict[str, Dict[str, Any]] = {}
        self.performance_stats: List[Dict[str, Any]] = []

    def start_query_monitoring(self, task_id: str) -> Dict[str, Any]:
        """Start monitoring a query."""
        monitoring_data = {
            "task_id": task_id,
            "start_time": datetime.utcnow(),
            "status": "running",
            "messages_received": 0,
            "webhook_calls": 0,
            "errors": [],
        }

        self.query_metrics[task_id] = monitoring_data
        return monitoring_data

    def record_message_received(self, task_id: str):
        """Record a message received from Claude."""
        if task_id in self.query_metrics:
            self.query_metrics[task_id]["messages_received"] += 1

    def record_webhook_sent(self, task_id: str, webhook_url: str, status_code: int):
        """Record a webhook sent."""
        if task_id in self.query_metrics:
            self.query_metrics[task_id]["webhook_calls"] += 1
            if status_code >= 400:
                self.query_metrics[task_id]["errors"].append(
                    {
                        "type": "webhook_error",
                        "status_code": status_code,
                        "url": webhook_url,
                        "timestamp": datetime.utcnow(),
                    }
                )

    def record_error(self, task_id: str, error_type: str, error_message: str):
        """Record an error during query processing."""
        if task_id in self.query_metrics:
            self.query_metrics[task_id]["errors"].append(
                {
                    "type": error_type,
                    "message": error_message,
                    "timestamp": datetime.utcnow(),
                }
            )

    def complete_query_monitoring(self, task_id: str, success: bool = True):
        """Complete monitoring for a query."""
        if task_id in self.query_metrics:
            monitoring_data = self.query_metrics[task_id]
            monitoring_data["end_time"] = datetime.utcnow()
            monitoring_data["duration"] = (
                monitoring_data["end_time"] - monitoring_data["start_time"]
            ).total_seconds()
            monitoring_data["status"] = "completed" if success else "failed"

            # Store in performance stats
            self.performance_stats.append(monitoring_data.copy())

            # Keep only last 1000 performance records
            if len(self.performance_stats) > 1000:
                self.performance_stats = self.performance_stats[-1000:]

            self.logger.info(
                "Query monitoring completed",
                task_id=task_id,
                duration=monitoring_data["duration"],
                success=success,
                messages_received=monitoring_data["messages_received"],
                webhook_calls=monitoring_data["webhook_calls"],
                errors=len(monitoring_data["errors"]),
            )

            # Clean up current metrics
            del self.query_metrics[task_id]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.performance_stats:
            return {"total_queries": 0}

        successful_queries = [s for s in self.performance_stats if s["status"] == "completed"]
        failed_queries = [s for s in self.performance_stats if s["status"] == "failed"]

        if successful_queries:
            avg_duration = sum(s["duration"] for s in successful_queries) / len(successful_queries)
            avg_messages = sum(s["messages_received"] for s in successful_queries) / len(
                successful_queries
            )
        else:
            avg_duration = 0
            avg_messages = 0

        return {
            "total_queries": len(self.performance_stats),
            "successful_queries": len(successful_queries),
            "failed_queries": len(failed_queries),
            "success_rate": len(successful_queries) / len(self.performance_stats)
            if self.performance_stats
            else 0,
            "average_duration": avg_duration,
            "average_messages_per_query": avg_messages,
        }