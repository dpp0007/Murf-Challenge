"""
Analytics API routes for the dashboard.

Endpoints:
- GET /api/analytics/summary - Overall metrics
- GET /api/analytics/recent - Recent calls
- GET /api/analytics/summary?range=7d - Time-filtered summary

SECURITY: These endpoints return only non-sensitive analytics data.
No phone numbers, SIP addresses, or private information is exposed.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from services.analytics_service import get_analytics_service

logger = logging.getLogger("analytics_routes")

router = APIRouter()


# ============================================================================
# Pydantic models
# ============================================================================

class CallAnalyticsResponse(BaseModel):
    """Analytics data for a single call."""
    call_id: str
    channel: str
    language: str
    started_at: str
    connected_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    outcome: str
    outcome_reason: Optional[str] = None
    task_type: str
    tool_used: Optional[str] = None
    escalated: bool
    latency_ms: Optional[int] = None
    failure_type: Optional[str] = None
    created_at: str


class AnalyticsSummaryResponse(BaseModel):
    """Summary analytics metrics."""
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float


class RecentCallsResponse(BaseModel):
    """Response containing recent calls."""
    calls: List[CallAnalyticsResponse]
    total_count: int
    query_time_ms: int


# ============================================================================
# Helper functions
# ============================================================================

def parse_range_parameter(range_str: Optional[str]) -> Optional[int]:
    """
    Parse range parameter (e.g., "7d", "30d", "all") to days.
    
    Args:
        range_str: Range string like "7d", "30d", "1d", or "all"
        
    Returns:
        Number of days, or None for "all"
    """
    if not range_str or range_str == "all":
        return None
    
    if range_str.endswith("d"):
        try:
            days = int(range_str[:-1])
            if days <= 0:
                raise ValueError()
            return days
        except (ValueError, IndexError):
            raise ValueError(f"Invalid range format: {range_str}. Use '7d', '30d', etc.")
    
    raise ValueError(f"Invalid range format: {range_str}. Use '7d', '30d', or 'all'.")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    range: Optional[str] = Query(None, description="Time range: '7d', '30d', 'all', etc.")
) -> Dict[str, Any]:
    """
    Get analytics summary (total, successful, failed calls).
    
    Args:
        range: Time range filter (optional). Examples: "7d", "30d", "all"
               Default is all time if not specified.
    
    Returns:
        Summary with total_calls, successful_calls, failed_calls, success_rate
    """
    try:
        # Parse range parameter
        days = None
        if range:
            days = parse_range_parameter(range)
        
        analytics_service = get_analytics_service()
        summary = analytics_service.get_summary(days=days)
        
        logger.info(f"[API] Analytics summary requested: range={range}, result={summary}")
        
        return summary
        
    except ValueError as e:
        logger.warning(f"[API] Invalid range parameter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error getting analytics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")


@router.get("/recent", response_model=RecentCallsResponse)
async def get_recent_calls(
    limit: int = Query(20, ge=1, le=100, description="Number of calls to return (1-100)"),
    range: Optional[str] = Query(None, description="Time range: '7d', '30d', 'all', etc.")
) -> Dict[str, Any]:
    """
    Get recent call records (most recent first).
    
    Args:
        limit: Number of calls to return (default 20, max 100)
        range: Time range filter (optional)
    
    Returns:
        List of recent calls with analytics data
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        
        # Parse range parameter
        days = None
        if range:
            days = parse_range_parameter(range)
        
        start_time = datetime.now(timezone.utc)
        
        analytics_service = get_analytics_service()
        call_records = analytics_service.get_recent_calls(limit=limit, days=days)
        
        end_time = datetime.now(timezone.utc)
        query_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Convert to response format
        calls = [
            CallAnalyticsResponse(
                call_id=call.call_id,
                channel=call.channel,
                language=call.language,
                started_at=call.started_at,
                connected_at=call.connected_at,
                ended_at=call.ended_at,
                duration_seconds=call.duration_seconds,
                outcome=call.outcome,
                outcome_reason=call.outcome_reason,
                task_type=call.task_type,
                tool_used=call.tool_used,
                escalated=call.escalated,
                latency_ms=call.latency_ms,
                failure_type=call.failure_type,
                created_at=call.created_at,
            )
            for call in call_records
        ]
        
        logger.info(f"[API] Recent calls retrieved: {len(calls)} calls (range={range})")
        
        return {
            "calls": calls,
            "total_count": len(calls),
            "query_time_ms": query_time_ms,
        }
        
    except ValueError as e:
        logger.warning(f"[API] Invalid parameter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error getting recent calls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get recent calls")


@router.get("/health")
async def analytics_health() -> Dict[str, str]:
    """
    Health check endpoint for analytics service.
    
    Returns:
        Status of analytics service
    """
    try:
        analytics_service = get_analytics_service()
        _ = analytics_service.get_summary()  # Quick test query
        return {"status": "healthy", "service": "analytics"}
    except Exception as e:
        logger.error(f"[API] Analytics health check failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/stats")
async def get_analytics_stats() -> Dict[str, Any]:
    """
    Get comprehensive analytics statistics.
    
    Returns:
        Extended analytics data including task type breakdown, channels, etc.
    """
    try:
        analytics_service = get_analytics_service()
        
        # Get summary
        summary = analytics_service.get_summary()
        
        # Get recent calls to compute additional stats
        recent_calls = analytics_service.get_recent_calls(limit=1000)  # Get more for stats
        
        # Calculate breakdowns
        task_type_count = {}
        channel_count = {}
        language_count = {}
        
        for call in recent_calls:
            # Task type
            task_type_count[call.task_type] = task_type_count.get(call.task_type, 0) + 1
            # Channel
            channel_count[call.channel] = channel_count.get(call.channel, 0) + 1
            # Language
            language_count[call.language] = language_count.get(call.language, 0) + 1
        
        # Average duration
        completed_calls = [c for c in recent_calls if c.duration_seconds]
        avg_duration = (
            sum(c.duration_seconds for c in completed_calls) / len(completed_calls)
            if completed_calls else 0
        )
        
        return {
            **summary,
            "average_duration_seconds": round(avg_duration, 2),
            "task_type_breakdown": task_type_count,
            "channel_breakdown": channel_count,
            "language_breakdown": language_count,
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting analytics stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics stats")
