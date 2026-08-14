"""
Analytics service for tracking and evaluating call outcomes.

Handles:
- Recording call lifecycle events
- Determining call success/failure
- Tracking task types and tool usage
- Integration with escalation system
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

try:
    from ..database.analytics_repository import get_analytics_repository
except (ImportError, ValueError):
    from database.analytics_repository import get_analytics_repository

logger = logging.getLogger("analytics_service")


class AnalyticsService:
    """Service for call analytics and outcome evaluation."""
    
    # Valid channels
    CHANNEL_BROWSER = "browser"
    CHANNEL_SIP = "sip"
    VALID_CHANNELS = {CHANNEL_BROWSER, CHANNEL_SIP}
    
    # Valid task types
    TASK_WEATHER = "weather"
    TASK_MANDI = "mandi"
    TASK_ESCALATION = "escalation"
    TASK_CROP_ADVISORY = "crop_advisory"
    TASK_GENERAL = "general"
    TASK_UNKNOWN = "unknown"
    VALID_TASKS = {TASK_WEATHER, TASK_MANDI, TASK_ESCALATION, TASK_CROP_ADVISORY, TASK_GENERAL, TASK_UNKNOWN}
    
    # Valid outcomes
    OUTCOME_SUCCESS = "SUCCESS"
    OUTCOME_FAILED = "FAILED"
    OUTCOME_IN_PROGRESS = "IN_PROGRESS"
    VALID_OUTCOMES = {OUTCOME_SUCCESS, OUTCOME_FAILED, OUTCOME_IN_PROGRESS}
    
    # Failure types
    FAILURE_USER_HANGUP = "USER_HANGUP"
    FAILURE_TASK_INCOMPLETE = "TASK_INCOMPLETE"
    FAILURE_TOOL_FAILURE = "TOOL_FAILURE"
    FAILURE_API_UNAVAILABLE = "API_UNAVAILABLE"
    FAILURE_NO_RESPONSE = "NO_RESPONSE"
    FAILURE_SIP_FAILURE = "SIP_FAILURE"
    FAILURE_CONNECTION_FAILURE = "CONNECTION_FAILURE"
    FAILURE_UNKNOWN = "UNKNOWN"
    VALID_FAILURES = {
        FAILURE_USER_HANGUP,
        FAILURE_TASK_INCOMPLETE,
        FAILURE_TOOL_FAILURE,
        FAILURE_API_UNAVAILABLE,
        FAILURE_NO_RESPONSE,
        FAILURE_SIP_FAILURE,
        FAILURE_CONNECTION_FAILURE,
        FAILURE_UNKNOWN,
    }
    
    def __init__(self):
        self.repo = get_analytics_repository()
    
    def start_call(
        self,
        call_id: str,
        channel: str,
        user_id: Optional[str] = None,
        language: str = "hi",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Start a new call record.
        
        Args:
            call_id: Unique call identifier (LiveKit room name or SIP call ID)
            channel: "browser" or "sip"
            user_id: Optional farmer user ID
            language: Language code (default "hi")
            metadata: Optional metadata dictionary
            
        Returns:
            True if call record created successfully
        """
        if channel not in self.VALID_CHANNELS:
            logger.error(f"[Analytics] Invalid channel: {channel}")
            return False
        
        logger.info(f"[Analytics] Starting call: {call_id} (channel={channel})")
        return self.repo.create_call_record(call_id, channel, user_id, language, metadata)
    
    def connect_call(self, call_id: str) -> bool:
        """Mark a call as actually connected (SIP/browser session active)."""
        logger.debug(f"[Analytics] Call connected: {call_id}")
        return self.repo.mark_connected(call_id)
    
    def record_task(self, call_id: str, task_type: str) -> bool:
        """Record the task type for a call."""
        if task_type not in self.VALID_TASKS:
            logger.warning(f"[Analytics] Invalid task type: {task_type}, using 'unknown'")
            task_type = self.TASK_UNKNOWN
        
        logger.debug(f"[Analytics] Task recorded: {call_id} = {task_type}")
        return self.repo.record_task_type(call_id, task_type)
    
    def record_tool(self, call_id: str, tool_name: str) -> bool:
        """Record tool usage in a call."""
        logger.debug(f"[Analytics] Tool used: {call_id} = {tool_name}")
        return self.repo.record_tool_used(call_id, tool_name)
    
    def record_escalation(self, call_id: str, escalation_ref_id: str) -> bool:
        """Record escalation creation during a call."""
        logger.info(f"[Analytics] Escalation recorded: {call_id} -> {escalation_ref_id}")
        return self.repo.record_escalation(call_id, escalation_ref_id)
    
    def record_latency(self, call_id: str, latency_ms: int) -> bool:
        """Record pipeline latency (user speech end to first agent audio)."""
        logger.debug(f"[Analytics] Latency: {call_id} = {latency_ms}ms")
        return self.repo.record_latency(call_id, latency_ms)
    
    def finalize_success(
        self,
        call_id: str,
        duration_seconds: int,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Mark a call as successfully completed.
        
        Args:
            call_id: Call identifier
            duration_seconds: Total call duration
            reason: Optional reason/details
            
        Returns:
            True if finalized
        """
        logger.info(f"[Analytics] Call SUCCESS: {call_id} ({duration_seconds}s)")
        return self.repo.finalize_call_success(call_id, duration_seconds, reason)
    
    def finalize_failure(
        self,
        call_id: str,
        duration_seconds: int,
        failure_type: str,
        reason: str,
    ) -> bool:
        """
        Mark a call as failed.
        
        Args:
            call_id: Call identifier
            duration_seconds: Total call duration
            failure_type: Type of failure
            reason: Detailed reason
            
        Returns:
            True if finalized
        """
        if failure_type not in self.VALID_FAILURES:
            logger.warning(f"[Analytics] Invalid failure type: {failure_type}, using UNKNOWN")
            failure_type = self.FAILURE_UNKNOWN
        
        logger.warning(f"[Analytics] Call FAILED: {call_id} ({failure_type}) - {reason}")
        return self.repo.finalize_call_failed(call_id, duration_seconds, failure_type, reason)
    
    def evaluate_weather_outcome(
        self,
        call_id: str,
        tool_succeeded: bool,
        weather_data_received: bool,
        user_completed_task: bool,
    ) -> bool:
        """
        Evaluate outcome for a weather query call.
        
        Args:
            call_id: Call identifier
            tool_succeeded: Did weather API call succeed?
            weather_data_received: Was data delivered to user?
            user_completed_task: Did user get useful response?
            
        Returns:
            True if recorded
        """
        if not tool_succeeded:
            return self.finalize_failure(
                call_id, 0,  # Duration will be calculated from timestamps
                self.FAILURE_TOOL_FAILURE,
                "Weather API unavailable or failed"
            )
        
        if not weather_data_received or not user_completed_task:
            return self.finalize_failure(
                call_id, 0,
                self.FAILURE_TASK_INCOMPLETE,
                "Weather data not successfully delivered"
            )
        
        return self.finalize_success(
            call_id, 0,
            "Weather information successfully provided"
        )
    
    def evaluate_mandi_outcome(
        self,
        call_id: str,
        tool_succeeded: bool,
        price_data_received: bool,
        user_completed_task: bool,
    ) -> bool:
        """Evaluate outcome for a mandi/market price query call."""
        if not tool_succeeded:
            return self.finalize_failure(
                call_id, 0,
                self.FAILURE_TOOL_FAILURE,
                "Mandi API unavailable or failed"
            )
        
        if not price_data_received or not user_completed_task:
            return self.finalize_failure(
                call_id, 0,
                self.FAILURE_TASK_INCOMPLETE,
                "Market price data not successfully delivered"
            )
        
        return self.finalize_success(
            call_id, 0,
            "Market price information successfully provided"
        )
    
    def evaluate_escalation_outcome(
        self,
        call_id: str,
        escalation_created: bool,
        escalation_ref_id: Optional[str] = None,
    ) -> bool:
        """Evaluate outcome for an escalation call."""
        if not escalation_created:
            return self.finalize_failure(
                call_id, 0,
                self.FAILURE_TASK_INCOMPLETE,
                "Escalation could not be created"
            )
        
        if escalation_ref_id:
            self.record_escalation(call_id, escalation_ref_id)
        
        return self.finalize_success(
            call_id, 0,
            f"Escalation successfully created and queued for adviser"
        )
    
    def evaluate_user_hangup(
        self,
        call_id: str,
        task_type: Optional[str] = None,
        task_completed: bool = False,
    ) -> bool:
        """
        Evaluate outcome when user hangs up.
        
        Args:
            call_id: Call identifier
            task_type: What was the intended task?
            task_completed: Was the task completed before hangup?
            
        Returns:
            True if recorded
        """
        if task_completed:
            return self.finalize_success(
                call_id, 0,
                f"Call completed before user hung up"
            )
        else:
            return self.finalize_failure(
                call_id, 0,
                self.FAILURE_USER_HANGUP,
                "User ended call before task completion"
            )
    
    def evaluate_sip_failure(self, call_id: str, reason: str) -> bool:
        """Evaluate outcome for SIP/telephony failures."""
        return self.finalize_failure(
            call_id, 0,
            self.FAILURE_SIP_FAILURE,
            f"SIP call failure: {reason}"
        )
    
    def get_summary(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics summary."""
        return self.repo.get_summary(days)
    
    def get_recent_calls(self, limit: int = 20, days: Optional[int] = None):
        """Get recent call records."""
        return self.repo.get_recent_calls(limit, days)


# Global singleton
_analytics_service_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the global analytics service instance."""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = AnalyticsService()
    return _analytics_service_instance
