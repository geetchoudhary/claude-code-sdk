"""Health and monitoring endpoint routes."""

from datetime import datetime

from fastapi import APIRouter

from app.routers.query import query_processor
from app.models import MetricsResponse, PerformanceStats, SessionStats

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get performance metrics and session statistics."""
    session_stats_data = query_processor.session_manager.get_session_stats()
    performance_stats_data = query_processor.query_monitor.get_performance_stats()

    return MetricsResponse(
        session_stats=SessionStats(**session_stats_data),
        performance_stats=PerformanceStats(**performance_stats_data),
        active_queries=len(query_processor.active_queries),
        timestamp=datetime.utcnow(),
    )