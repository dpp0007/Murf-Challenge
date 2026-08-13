"""
Call analytics tracker - integrates with agent sessions.

Handles:
- Recording call start/connect/end
- Tracking task types and tool usage
- Determining call outcomes
- Integration with session events

This module provides a clean API for recording call analytics
without polluting the agent code with analytics logic.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from services.analytics_service import get_analytics_service
from database.analytics_repository import get_analytics_repository

logger = logging.getLogger("call_tracker")


class CallTracker:
    """Tracks analytics for a single call session."""
    
    def __init__(self, call_id: str, channel: str = "browser", language: str = "hi", user_id: Optional[str] = None):
        """
        Initialize a call tracker.
        
        Args:
            call_id: Unique call identifier (LiveKit room name or SIP call ID)
            channel: "browser" or "sip"
            language: Language code (default "hi")
            user_id: Optional farmer user ID (links call to farmer)
        """
        self.call_id = call_id
        self.channel = channel
        self.language = language
        self.user_id = user_id
        self.analytics_service = get_analytics_service()
        
        self.start_time = time.time()
        self.connected_time: Optional[float] = None
        self.task_recorded = False
        self.tool_recorded = False
        self.escalation_recorded = False
        self.finalized = False
        
        # Start the call record with user_id if provided
        self.analytics_service.start_call(
            call_id=call_id,
            channel=channel,
            language=language,
            user_id=user_id,
        )
        logger.info(f"[CallTracker] Started tracking: {call_id} (user_id: {user_id})")
    
    def mark_connected(self) -> None:
        """Mark the call as actually connected."""
        self.connected_time = time.time()
        self.analytics_service.connect_call(self.call_id)
        logger.debug(f"[CallTracker] Connected: {self.call_id}")
    
    def record_task(self, task_type: str) -> None:
        """Record the task type for this call."""
        if self.task_recorded:
            logger.warning(f"[CallTracker] Task already recorded for {self.call_id}")
            return
        
        self.task_recorded = True
        self.analytics_service.record_task(self.call_id, task_type)
        logger.debug(f"[CallTracker] Task: {self.call_id} = {task_type}")
    
    def record_tool(self, tool_name: str) -> None:
        """Record tool usage."""
        if self.tool_recorded:
            logger.warning(f"[CallTracker] Tool already recorded for {self.call_id}")
            return
        
        self.tool_recorded = True
        self.analytics_service.record_tool(self.call_id, tool_name)
        logger.debug(f"[CallTracker] Tool: {self.call_id} = {tool_name}")
    
    def record_escalation(self, escalation_ref_id: str) -> None:
        """Record escalation creation."""
        if self.escalation_recorded:
            logger.warning(f"[CallTracker] Escalation already recorded for {self.call_id}")
            return
        
        self.escalation_recorded = True
        self.analytics_service.record_escalation(self.call_id, escalation_ref_id)
        logger.info(f"[CallTracker] Escalation: {self.call_id} -> {escalation_ref_id}")
    
    def record_latency(self, latency_ms: int) -> None:
        """Record pipeline latency."""
        self.analytics_service.record_latency(self.call_id, latency_ms)
    
    def get_duration_seconds(self) -> int:
        """Get call duration in seconds."""
        return int(time.time() - self.start_time)
    
    def finalize_success(self, reason: Optional[str] = None) -> bool:
        """Mark call as successful."""
        if self.finalized:
            logger.warning(f"[CallTracker] Call already finalized: {self.call_id}")
            return False
        
        self.finalized = True
        duration = self.get_duration_seconds()
        result = self.analytics_service.finalize_success(
            self.call_id,
            duration,
            reason
        )
        logger.info(f"[CallTracker] Finalized SUCCESS: {self.call_id} ({duration}s)")
        return result
    
    def finalize_failure(
        self,
        failure_type: str,
        reason: str,
    ) -> bool:
        """Mark call as failed."""
        if self.finalized:
            logger.warning(f"[CallTracker] Call already finalized: {self.call_id}")
            return False
        
        self.finalized = True
        duration = self.get_duration_seconds()
        result = self.analytics_service.finalize_failure(
            self.call_id,
            duration,
            failure_type,
            reason
        )
        logger.warning(f"[CallTracker] Finalized FAILED: {self.call_id} ({failure_type})")
        return result
    
    def safe_finalize_if_not_done(self) -> None:
        """
        Safely finalize the call if not already finalized.
        
        Used in cleanup/exception handlers to ensure call is always finalized.
        """
        if self.finalized:
            return
        
        # Mark as unknown failure to ensure call is recorded
        self.finalize_failure(
            "UNKNOWN",
            "Call ended without explicit finalization (likely session crash or hangup)"
        )


# Global tracker storage (one per active call session)
_active_trackers: Dict[str, CallTracker] = {}


def get_or_create_tracker(call_id: str, channel: str = "browser", language: str = "hi", user_id: Optional[str] = None) -> CallTracker:
    """
    Get existing tracker or create new one for a call.
    
    Args:
        call_id: Unique call identifier
        channel: "browser" or "sip"
        language: Language code
        user_id: Optional farmer user ID (links call to farmer)
        
    Returns:
        CallTracker instance
    """
    if call_id not in _active_trackers:
        _active_trackers[call_id] = CallTracker(call_id, channel, language, user_id)
    return _active_trackers[call_id]


def get_tracker(call_id: str) -> Optional[CallTracker]:
    """Get existing tracker for a call."""
    return _active_trackers.get(call_id)


def remove_tracker(call_id: str) -> None:
    """Remove and finalize a tracker."""
    if call_id in _active_trackers:
        tracker = _active_trackers.pop(call_id)
        tracker.safe_finalize_if_not_done()
        logger.debug(f"[CallTracker] Removed: {call_id}")
