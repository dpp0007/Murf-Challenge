"""
Escalation Repository for Human-in-the-Loop requests.

Handles:
- Creating escalation requests
- Querying escalations
- Updating escalation status
- Managing callback tracking
- Resolving escalations
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid

from .db import get_database

logger = logging.getLogger("escalation_repository")


@dataclass
class Escalation:
    """Escalation request data model."""
    id: Optional[int] = None
    reference_id: str = ""
    user_id: str = ""
    farmer_name: str = ""
    district: Optional[str] = None
    reason: str = ""
    original_question: str = ""
    summary: str = ""
    what_agent_checked: Optional[str] = None
    urgency: str = "MEDIUM"  # LOW, MEDIUM, HIGH, EMERGENCY
    language: str = "hi"
    preferred_followup: str = "phone"
    status: str = "OPEN"  # OPEN, IN_PROGRESS, RESOLVED
    human_answer: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    resolved_at: Optional[str] = None
    callback_status: str = "NOT_STARTED"  # NOT_STARTED, QUEUED, CALLING, CONNECTED, COMPLETED, NO_ANSWER, FAILED, SKIPPED_OPT_OUT
    callback_attempts: int = 0
    callback_started_at: Optional[str] = None
    callback_connected_at: Optional[str] = None
    callback_completed_at: Optional[str] = None
    callback_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "reference_id": self.reference_id,
            "user_id": self.user_id,
            "farmer_name": self.farmer_name,
            "district": self.district,
            "reason": self.reason,
            "original_question": self.original_question,
            "summary": self.summary,
            "what_agent_checked": self.what_agent_checked,
            "urgency": self.urgency,
            "language": self.language,
            "preferred_followup": self.preferred_followup,
            "status": self.status,
            "human_answer": self.human_answer,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "callback_status": self.callback_status,
            "callback_attempts": self.callback_attempts,
            "callback_started_at": self.callback_started_at,
            "callback_connected_at": self.callback_connected_at,
            "callback_completed_at": self.callback_completed_at,
            "callback_error": self.callback_error,
        }


class EscalationRepository:
    """Repository for escalation data access."""
    
    def __init__(self):
        """Initialize repository."""
        self.db = get_database()
    
    def _generate_reference_id(self) -> str:
        """Generate a unique human-readable reference ID."""
        import random
        import uuid
        import hashlib
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d")
        
        # Use UUID to guarantee uniqueness, then convert to short hash
        unique_id = str(uuid.uuid4())
        # Take last 8 chars of UUID for readable suffix
        hash_suffix = unique_id.replace('-', '')[-8:].upper()
        
        # Get sequence for today for readability
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM escalations WHERE DATE(created_at) = ?",
                (date_str,)
            )
            count = cursor.fetchone()[0] + 1
            
            # Format: KM-YYYYMMDD-SEQUENCE-HASH
            # The HASH is derived from UUID so it's guaranteed unique
            ref_id = f"KM-{date_str}-{count:04d}-{hash_suffix[:4]}"
            
            return ref_id
        finally:
            conn.close()
    
    def create_escalation(
        self,
        user_id: str,
        farmer_name: str,
        reason: str,
        original_question: str,
        summary: str,
        what_agent_checked: Optional[str] = None,
        urgency: str = "MEDIUM",
        language: str = "hi",
        preferred_followup: str = "phone",
        district: Optional[str] = None,
    ) -> Optional[Escalation]:
        """
        Create a new escalation request.
        
        Args:
            user_id: Unique farmer identifier
            farmer_name: Name of the farmer
            reason: Escalation reason (CROP_PROBLEM, MARKET_DATA, etc.)
            original_question: The farmer's original question
            summary: Brief summary of the issue
            what_agent_checked: What the agent checked before escalating
            urgency: LOW, MEDIUM, HIGH, EMERGENCY
            language: hi, en, or mixed
            preferred_followup: phone, whatsapp, etc.
            district: Farmer's district
        
        Returns:
            Created Escalation object or None on failure
        """
        try:
            reference_id = self._generate_reference_id()
            timestamp = datetime.now(timezone.utc).isoformat()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO escalations (
                    reference_id, user_id, farmer_name, district, reason,
                    original_question, summary, what_agent_checked,
                    urgency, language, preferred_followup, status,
                    callback_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reference_id, user_id, farmer_name, district, reason,
                original_question, summary, what_agent_checked,
                urgency, language, preferred_followup, "OPEN",
                "NOT_STARTED", timestamp, timestamp
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Escalation created: {reference_id} for user {user_id}")
            return self.get_escalation_by_reference(reference_id)
            
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return None
    
    def get_escalation_by_reference(self, reference_id: str) -> Optional[Escalation]:
        """Get escalation by reference ID."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM escalations WHERE reference_id = ?", (reference_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return self._row_to_escalation(row)
            
        except Exception as e:
            logger.error(f"Error fetching escalation: {e}")
            return None
    
    def get_escalations_by_user(self, user_id: str, status: Optional[str] = None) -> List[Escalation]:
        """Get escalations for a specific user."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT * FROM escalations WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status)
                )
            else:
                cursor.execute(
                    "SELECT * FROM escalations WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_escalation(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching user escalations: {e}")
            return []
    
    def get_open_escalations(self, limit: int = 50) -> List[Escalation]:
        """Get all open escalations for Discord display."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM escalations 
                WHERE status IN ('OPEN', 'IN_PROGRESS')
                ORDER BY urgency DESC, created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_escalation(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching open escalations: {e}")
            return []
    
    def resolve_escalation(
        self,
        reference_id: str,
        human_answer: str,
        resolution_notes: Optional[str] = None,
    ) -> Optional[Escalation]:
        """
        Resolve an escalation with human answer.
        Atomically sets callback_status to QUEUED in a single SQL transaction.
        
        CRITICAL: This must be atomic to prevent duplicate callbacks!
        
        Args:
            reference_id: Escalation reference ID
            human_answer: The adviser's answer
            resolution_notes: Optional resolution notes
        
        Returns:
            Updated escalation or None on failure
        """
        if not human_answer or not human_answer.strip():
            logger.warning(f"Empty human answer for {reference_id}")
            return None
        
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # ATOMIC: Single transaction - resolve AND set callback status together
            # This prevents the window where another process sees "NOT_STARTED"
            cursor.execute("""
                UPDATE escalations
                SET status = ?,
                    human_answer = ?,
                    resolution_notes = ?,
                    resolved_at = ?,
                    updated_at = ?,
                    callback_status = ?
                WHERE reference_id = ? AND status != ?
            """, (
                "RESOLVED",
                human_answer,
                resolution_notes,
                timestamp,
                timestamp,
                "QUEUED",  # Set to QUEUED atomically with RESOLVED
                reference_id,
                "RESOLVED"
            ))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected == 0:
                # Already resolved or escalation not found
                logger.info(f"Escalation already resolved or not found: {reference_id}")
                conn.close()
                return self.get_escalation_by_reference(reference_id)
            
            logger.info(f"Escalation resolved atomically: {reference_id}")
            conn.close()
            
            # Fetch and return the updated escalation
            return self.get_escalation_by_reference(reference_id)
            
        except Exception as e:
            logger.error(f"Error resolving escalation {reference_id}: {e}")
            return None
            
            if affected == 0:
                logger.warning(f"Could not update escalation (already resolved?): {reference_id}")
                return self.get_escalation_by_reference(reference_id)
            
            logger.info(f"Escalation resolved: {reference_id}")
            return self.get_escalation_by_reference(reference_id)
            
        except Exception as e:
            logger.error(f"Error resolving escalation: {e}")
            return None
    
    def update_callback_status(
        self,
        reference_id: str,
        callback_status: str,
        callback_error: Optional[str] = None,
        increment_attempts: bool = False,
    ) -> bool:
        """
        Update callback status for an escalation.
        
        Args:
            reference_id: Escalation reference ID
            callback_status: New callback status
            callback_error: Optional error message
            increment_attempts: Whether to increment callback attempts
        
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build the update query
            if callback_status == "CALLING":
                cursor.execute("""
                    UPDATE escalations
                    SET callback_status = ?,
                        callback_started_at = ?,
                        callback_attempts = callback_attempts + 1,
                        updated_at = ?
                    WHERE reference_id = ?
                """, (callback_status, timestamp, timestamp, reference_id))
            elif callback_status == "CONNECTED":
                cursor.execute("""
                    UPDATE escalations
                    SET callback_status = ?,
                        callback_connected_at = ?,
                        updated_at = ?
                    WHERE reference_id = ?
                """, (callback_status, timestamp, timestamp, reference_id))
            elif callback_status == "COMPLETED":
                cursor.execute("""
                    UPDATE escalations
                    SET callback_status = ?,
                        callback_completed_at = ?,
                        updated_at = ?
                    WHERE reference_id = ?
                """, (callback_status, timestamp, timestamp, reference_id))
            elif callback_status in ("NO_ANSWER", "FAILED", "SKIPPED_OPT_OUT"):
                cursor.execute("""
                    UPDATE escalations
                    SET callback_status = ?,
                        callback_error = ?,
                        updated_at = ?
                    WHERE reference_id = ?
                """, (callback_status, callback_error, timestamp, reference_id))
            else:
                cursor.execute("""
                    UPDATE escalations
                    SET callback_status = ?,
                        updated_at = ?
                    WHERE reference_id = ?
                """, (callback_status, timestamp, reference_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating callback status: {e}")
            return False
    
    def _row_to_escalation(self, row: Any) -> Escalation:
        """Convert database row to Escalation object."""
        return Escalation(
            id=row["id"],
            reference_id=row["reference_id"],
            user_id=row["user_id"],
            farmer_name=row["farmer_name"],
            district=row["district"],
            reason=row["reason"],
            original_question=row["original_question"],
            summary=row["summary"],
            what_agent_checked=row["what_agent_checked"],
            urgency=row["urgency"],
            language=row["language"],
            preferred_followup=row["preferred_followup"],
            status=row["status"],
            human_answer=row["human_answer"],
            resolution_notes=row["resolution_notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
            callback_status=row["callback_status"],
            callback_attempts=row["callback_attempts"],
            callback_started_at=row["callback_started_at"],
            callback_connected_at=row["callback_connected_at"],
            callback_completed_at=row["callback_completed_at"],
            callback_error=row["callback_error"],
        )


# Global instance
_escalation_repo_instance: Optional[EscalationRepository] = None


def get_escalation_repository() -> EscalationRepository:
    """Get or create the global escalation repository."""
    global _escalation_repo_instance
    if _escalation_repo_instance is None:
        _escalation_repo_instance = EscalationRepository()
    return _escalation_repo_instance
