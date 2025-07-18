"""Session management endpoint routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.routers.query import query_processor
from app.models import SessionInfo

router = APIRouter()


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    session_info = query_processor.session_manager.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(**session_info)


@router.post("/cleanup")
async def cleanup_sessions(max_age_hours: int = 24):
    """Clean up old sessions."""
    cleaned_count = query_processor.session_manager.cleanup_old_sessions(max_age_hours)
    return {
        "cleaned_sessions": cleaned_count,
        "timestamp": datetime.utcnow().isoformat(),
    }