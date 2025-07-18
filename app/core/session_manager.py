"""Session lifecycle and state tracking management."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog


class SessionManager:
    """Manages Claude session lifecycle and state tracking."""

    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}

    def track_session(
        self, session_id: str, user_id: Optional[str] = None, conversation_id: Optional[str] = None
    ):
        """Track a new or existing session."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "created_at": datetime.utcnow(),
                "last_used": datetime.utcnow(),
                "query_count": 0,
                "total_tokens": 0,
                "tools_used": [],
                "status": "active",
            }
            self.logger.info(
                "New session tracked",
                session_id=session_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        else:
            # Update existing session
            self.active_sessions[session_id]["last_used"] = datetime.utcnow()
            self.active_sessions[session_id]["query_count"] += 1

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.active_sessions.get(session_id)

    def mark_session_completed(self, session_id: str):
        """Mark session as completed."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["completed_at"] = datetime.utcnow()

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = [
            session_id
            for session_id, info in self.active_sessions.items()
            if info["last_used"] < cutoff_time
        ]

        for session_id in expired_sessions:
            self.logger.info("Cleaning up expired session", session_id=session_id)
            del self.active_sessions[session_id]

        return len(expired_sessions)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        return {
            "active_sessions": len(self.active_sessions),
            "total_queries": sum(info["query_count"] for info in self.active_sessions.values()),
            "sessions_by_status": {
                "active": len([s for s in self.active_sessions.values() if s["status"] == "active"]),
                "completed": len(
                    [s for s in self.active_sessions.values() if s["status"] == "completed"]
                ),
            },
        }