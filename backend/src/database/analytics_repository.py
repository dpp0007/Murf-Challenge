"""
Analytics repository for call tracking and analytics.

Handles:
- Creating and updating call analytics records
- Querying analytics for dashboards
- Calculating success/failure metrics
- Robust idempotent operations
"""

import logging
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from .db import get_database

logger = logging.getLogger("analytics_repository")


class CallAnalytics:
    """Data class for a call analytics record."""
    
    def __init__(
        self,
        id: int,
        call_id: str,
        user_id: Optional[str],
        channel: str,
        language: str,
        started_at: str,
        connected_at: Optional[str],
        ended_at: Optional[str],
        duration_seconds: Optional[int],
        outcome: str,
        outcome_reason: Optional[str],
        task_type: str,
        tool_used: Optional[str],
        escalated: int,
        latency_ms: Optional[int],
        failure_type: Optional[str],
        created_at: str,
        metadata_json: Optional[str],
    ):
        self.id = id
        self.call_id = call_id
        self.user_id = user_id
        self.channel = channel
        self.language = language
        self.started_at = started_at
        self.connected_at = connected_at
        self.ended_at = ended_at
        self.duration_seconds = duration_seconds
        self.outcome = outcome
        self.outcome_reason = outcome_reason
        self.task_type = task_type
        self.tool_used = tool_used
        self.escalated = escalated == 1
        self.latency_ms = latency_ms
        self.failure_type = failure_type
        self.created_at = created_at
        self.metadata = {}
        if metadata_json:
            try:
                self.metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "call_id": self.call_id,
            "channel": self.channel,
            "language": self.language,
            "started_at": self.started_at,
            "connected_at": self.connected_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "task_type": self.task_type,
            "tool_used": self.tool_used,
            "escalated": self.escalated,
            "latency_ms": self.latency_ms,
            "failure_type": self.failure_type,
            "created_at": self.created_at,
        }


class AnalyticsRepository:
    """Repository for call analytics operations."""
    
    def __init__(self):
        self.db = get_database()
    
    def _get_utc_now(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def create_call_record(
        self,
        call_id: str,
        channel: str,
        user_id: Optional[str] = None,
        language: str = "hi",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create a new call analytics record.
        
        Args:
            call_id: Unique call identifier (LiveKit room name or SIP call ID)
            channel: "browser" or "sip"
            user_id: Optional farmer user ID if known
            language: Language code (default "hi")
            metadata: Optional JSON metadata
            
        Returns:
            True if created successfully, False if already exists
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            now = self._get_utc_now()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO call_analytics (
                    call_id, user_id, channel, language,
                    started_at, outcome, task_type,
                    created_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id, user_id, channel, language,
                now, "IN_PROGRESS", "unknown",
                now, metadata_json
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[Analytics] Call record created: {call_id} (channel={channel})")
            return True
            
        except sqlite3.IntegrityError:
            # Call already exists (duplicate prevention)
            logger.warning(f"[Analytics] Call record already exists: {call_id}")
            return False
        except Exception as e:
            logger.error(f"[Analytics] Failed to create call record: {e}", exc_info=True)
            return False
    
    def mark_connected(self, call_id: str) -> bool:
        """
        Mark a call as connected (actually established with SIP/browser).
        
        Args:
            call_id: Call identifier
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            connected_at = self._get_utc_now()
            
            cursor.execute("""
                UPDATE call_analytics
                SET connected_at = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (connected_at, call_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"[Analytics] Call marked connected: {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to mark call connected: {e}", exc_info=True)
            return False
    
    def record_task_type(self, call_id: str, task_type: str) -> bool:
        """
        Record the task type for a call.
        
        Args:
            call_id: Call identifier
            task_type: Task type (weather, mandi, escalation, crop_advisory, general, unknown)
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE call_analytics
                SET task_type = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (task_type, call_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"[Analytics] Task type recorded: {call_id} = {task_type}")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to record task type: {e}", exc_info=True)
            return False
    
    def record_tool_used(self, call_id: str, tool_name: str) -> bool:
        """
        Record which tool was used in a call.
        
        Args:
            call_id: Call identifier
            tool_name: Tool name (e.g., "weather_api", "mandi_api", "escalation_service")
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE call_analytics
                SET tool_used = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (tool_name, call_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"[Analytics] Tool recorded: {call_id} = {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to record tool: {e}", exc_info=True)
            return False
    
    def record_escalation(self, call_id: str, escalation_reference_id: str) -> bool:
        """
        Record that a call resulted in an escalation.
        
        Args:
            call_id: Call identifier
            escalation_reference_id: Reference ID of the created escalation
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE call_analytics
                SET escalated = 1, metadata_json = json_set(
                    COALESCE(metadata_json, '{}'),
                    '$.escalation_reference_id',
                    ?
                )
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (escalation_reference_id, call_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[Analytics] Escalation recorded: {call_id} -> {escalation_reference_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to record escalation: {e}", exc_info=True)
            return False
    
    def record_latency(self, call_id: str, latency_ms: int) -> bool:
        """
        Record latency for a call (e.g., user speech end to first agent audio).
        
        Args:
            call_id: Call identifier
            latency_ms: Latency in milliseconds
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE call_analytics
                SET latency_ms = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (latency_ms, call_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"[Analytics] Latency recorded: {call_id} = {latency_ms}ms")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to record latency: {e}", exc_info=True)
            return False
    
    def finalize_call_success(
        self,
        call_id: str,
        duration_seconds: int,
        outcome_reason: Optional[str] = None,
    ) -> bool:
        """
        Mark a call as successfully completed.
        
        Args:
            call_id: Call identifier
            duration_seconds: Call duration in seconds
            outcome_reason: Optional reason/details
            
        Returns:
            True if finalized successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            ended_at = self._get_utc_now()
            
            cursor.execute("""
                UPDATE call_analytics
                SET outcome = 'SUCCESS',
                    outcome_reason = ?,
                    ended_at = ?,
                    duration_seconds = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (outcome_reason, ended_at, duration_seconds, call_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[Analytics] Call finalized as SUCCESS: {call_id} ({duration_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to finalize call success: {e}", exc_info=True)
            return False
    
    def finalize_call_failed(
        self,
        call_id: str,
        duration_seconds: int,
        failure_type: str,
        outcome_reason: str,
    ) -> bool:
        """
        Mark a call as failed.
        
        Args:
            call_id: Call identifier
            duration_seconds: Call duration in seconds
            failure_type: Type of failure (USER_HANGUP, TASK_INCOMPLETE, TOOL_FAILURE, etc.)
            outcome_reason: Detailed reason for failure
            
        Returns:
            True if finalized successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            ended_at = self._get_utc_now()
            
            cursor.execute("""
                UPDATE call_analytics
                SET outcome = 'FAILED',
                    failure_type = ?,
                    outcome_reason = ?,
                    ended_at = ?,
                    duration_seconds = ?
                WHERE call_id = ? AND outcome = 'IN_PROGRESS'
            """, (failure_type, outcome_reason, ended_at, duration_seconds, call_id))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"[Analytics] Call finalized as FAILED: {call_id} ({failure_type})")
            return True
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to finalize call failed: {e}", exc_info=True)
            return False
    
    def get_call_record(self, call_id: str) -> Optional[CallAnalytics]:
        """
        Retrieve a call analytics record.
        
        Args:
            call_id: Call identifier
            
        Returns:
            CallAnalytics record or None if not found
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM call_analytics WHERE call_id = ?
            """, (call_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return CallAnalytics(
                id=row["id"],
                call_id=row["call_id"],
                user_id=row["user_id"],
                channel=row["channel"],
                language=row["language"],
                started_at=row["started_at"],
                connected_at=row["connected_at"],
                ended_at=row["ended_at"],
                duration_seconds=row["duration_seconds"],
                outcome=row["outcome"],
                outcome_reason=row["outcome_reason"],
                task_type=row["task_type"],
                tool_used=row["tool_used"],
                escalated=row["escalated"],
                latency_ms=row["latency_ms"],
                failure_type=row["failure_type"],
                created_at=row["created_at"],
                metadata_json=row["metadata_json"],
            )
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to get call record: {e}", exc_info=True)
            return None
    
    def get_summary(self, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get analytics summary (total, success, failed calls).
        
        Args:
            days: If provided, only include calls from the last N days
            
        Returns:
            Dictionary with total_calls, successful_calls, failed_calls, success_rate
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause for date filtering
            where_clause = "WHERE outcome IN ('SUCCESS', 'FAILED')"
            params = []
            
            if days:
                cursor.execute("""
                    SELECT datetime('now', ? || ' days') as cutoff
                """, (f"-{days}",))
                cutoff = cursor.fetchone()["cutoff"]
                where_clause += " AND created_at >= ?"
                params.append(cutoff)
            
            # Get counts
            query = f"""
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN outcome = 'SUCCESS' THEN 1 ELSE 0 END) as successful_calls,
                    SUM(CASE WHEN outcome = 'FAILED' THEN 1 ELSE 0 END) as failed_calls
                FROM call_analytics
                {where_clause}
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()
            
            total = row["total_calls"] or 0
            successful = row["successful_calls"] or 0
            failed = row["failed_calls"] or 0
            
            success_rate = (successful / total * 100) if total > 0 else 0
            
            return {
                "total_calls": total,
                "successful_calls": successful,
                "failed_calls": failed,
                "success_rate": round(success_rate, 2),
            }
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to get summary: {e}", exc_info=True)
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "success_rate": 0,
            }
    
    def get_recent_calls(self, limit: int = 20, days: Optional[int] = None) -> List[CallAnalytics]:
        """
        Get recent call records.
        
        Args:
            limit: Maximum number of records to return (default 20)
            days: If provided, only include calls from the last N days
            
        Returns:
            List of CallAnalytics records
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_clause = "WHERE outcome IN ('SUCCESS', 'FAILED')"
            params = [limit]
            
            if days:
                cursor.execute("""
                    SELECT datetime('now', ? || ' days') as cutoff
                """, (f"-{days}",))
                cutoff = cursor.fetchone()["cutoff"]
                where_clause += " AND created_at >= ?"
                params.insert(0, cutoff)
            
            # Get recent calls (most recent first)
            query = f"""
                SELECT * FROM call_analytics
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                CallAnalytics(
                    id=row["id"],
                    call_id=row["call_id"],
                    user_id=row["user_id"],
                    channel=row["channel"],
                    language=row["language"],
                    started_at=row["started_at"],
                    connected_at=row["connected_at"],
                    ended_at=row["ended_at"],
                    duration_seconds=row["duration_seconds"],
                    outcome=row["outcome"],
                    outcome_reason=row["outcome_reason"],
                    task_type=row["task_type"],
                    tool_used=row["tool_used"],
                    escalated=row["escalated"],
                    latency_ms=row["latency_ms"],
                    failure_type=row["failure_type"],
                    created_at=row["created_at"],
                    metadata_json=row["metadata_json"],
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to get recent calls: {e}", exc_info=True)
            return []
    
    def get_calls_by_status(
        self,
        outcome: str,
        limit: int = 100,
    ) -> List[CallAnalytics]:
        """
        Get calls filtered by outcome status.
        
        Args:
            outcome: 'SUCCESS' or 'FAILED'
            limit: Maximum records to return
            
        Returns:
            List of CallAnalytics records
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM call_analytics
                WHERE outcome = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (outcome, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                CallAnalytics(
                    id=row["id"],
                    call_id=row["call_id"],
                    user_id=row["user_id"],
                    channel=row["channel"],
                    language=row["language"],
                    started_at=row["started_at"],
                    connected_at=row["connected_at"],
                    ended_at=row["ended_at"],
                    duration_seconds=row["duration_seconds"],
                    outcome=row["outcome"],
                    outcome_reason=row["outcome_reason"],
                    task_type=row["task_type"],
                    tool_used=row["tool_used"],
                    escalated=row["escalated"],
                    latency_ms=row["latency_ms"],
                    failure_type=row["failure_type"],
                    created_at=row["created_at"],
                    metadata_json=row["metadata_json"],
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"[Analytics] Failed to get calls by status: {e}", exc_info=True)
            return []
    
    def update_call_user_id(self, call_id: str, user_id: str) -> bool:
        """
        Update user_id for an existing call record.
        
        Args:
            call_id: Call ID
            user_id: Farmer user ID
            
        Returns:
            True if updated successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE call_analytics
                SET user_id = ?
                WHERE call_id = ?
                """,
                (user_id, call_id)
            )
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount > 0:
                logger.debug(f"[Analytics] Updated user_id for call {call_id}")
                return True
            else:
                logger.warning(f"[Analytics] Call {call_id} not found for user_id update")
                return False
                
        except Exception as e:
            logger.error(f"[Analytics] Failed to update user_id for {call_id}: {e}", exc_info=True)
            return False


# Global singleton instance
_analytics_repository_instance: Optional[AnalyticsRepository] = None


def get_analytics_repository() -> AnalyticsRepository:
    """Get or create the global analytics repository instance."""
    global _analytics_repository_instance
    if _analytics_repository_instance is None:
        _analytics_repository_instance = AnalyticsRepository()
    return _analytics_repository_instance
