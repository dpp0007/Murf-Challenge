"""
Escalation Service - Human-in-the-Loop request handling.

Handles:
- Escalation determination logic
- Discord notification
- Callback scheduling
- Resolution management
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from database.escalation_repository import get_escalation_repository, Escalation
from database.farmer_repository import get_farmer_repository

logger = logging.getLogger("escalation_service")


class EscalationReason(str, Enum):
    """Escalation reason types."""
    SERIOUS_CROP_PROBLEM = "SERIOUS_CROP_PROBLEM"
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"
    UNCERTAIN_DIAGNOSIS = "UNCERTAIN_DIAGNOSIS"
    OTHER = "OTHER"


class EscalationService:
    """Service for managing escalation requests."""
    
    def __init__(self):
        """Initialize the service."""
        self.escalation_repo = get_escalation_repository()
        self.farmer_repo = get_farmer_repository()
    
    def should_escalate_crop_problem(
        self,
        problem_description: str,
        treatment_attempted: bool = False,
    ) -> bool:
        """
        Determine if a crop problem warrants escalation.
        
        Escalate when:
        - Serious crop damage or pest infestation
        - Disease symptoms
        - Previous treatment didn't work
        - Diagnosis is uncertain
        
        Args:
            problem_description: Description of the problem
            treatment_attempted: Whether farmer already tried a treatment
        
        Returns:
            True if escalation is recommended
        """
        # Keywords that suggest escalation
        serious_keywords = [
            "severe", "widespread", "dying", "dead", "infestation",
            "disease", "fungal", "bacterial", "virus", "wilt",
            "pest", "insect", "damage", "destroyed", "lost",
            "गंभीर", "फैला", "मरा", "बीमारी", "कीट",
        ]
        
        problem_lower = problem_description.lower()
        has_serious_indicator = any(kw in problem_lower for kw in serious_keywords)
        
        # If treatment already attempted, it's more serious
        if treatment_attempted and has_serious_indicator:
            return True
        
        return has_serious_indicator
    
    def should_escalate_market_data(
        self,
        market_query_failed: bool,
        data_available: bool = False,
        data_is_recent: bool = False,
    ) -> bool:
        """
        Determine if market data issue warrants escalation.
        
        Escalate when:
        - API failure
        - No data available
        - Data is too old
        
        Args:
            market_query_failed: Whether the market query failed
            data_available: Whether data was found
            data_is_recent: Whether data is recent (< 24 hours old)
        
        Returns:
            True if escalation is recommended
        """
        if market_query_failed:
            return True
        
        if not data_available:
            return True
        
        if not data_is_recent:
            return True
        
        return False
    
    def create_escalation(
        self,
        user_id: str,
        reason: EscalationReason,
        original_question: str,
        summary: str,
        what_agent_checked: Optional[str] = None,
        urgency: str = "MEDIUM",
        preferred_followup: str = "phone",
    ) -> Optional[Escalation]:
        """
        Create an escalation request.
        
        Args:
            user_id: Farmer user ID
            reason: Escalation reason
            original_question: The farmer's original question
            summary: Brief summary of the issue
            what_agent_checked: What the agent checked
            urgency: LOW, MEDIUM, HIGH, EMERGENCY
            preferred_followup: phone, whatsapp, etc.
        
        Returns:
            Created Escalation or None on failure
        """
        try:
            # Look up farmer details
            farmer_profile = self.farmer_repo.lookup_farmer(user_id)
            if not farmer_profile:
                logger.warning(f"Farmer not found for escalation: {user_id}")
                return None
            
            # Create escalation
            escalation = self.escalation_repo.create_escalation(
                user_id=user_id,
                farmer_name=farmer_profile.name or "Farmer",
                reason=reason.value,
                original_question=original_question,
                summary=summary,
                what_agent_checked=what_agent_checked,
                urgency=urgency,
                language=farmer_profile.language_preference or "hi",
                preferred_followup=preferred_followup,
                district=farmer_profile.district,
            )
            
            if escalation:
                logger.info(f"Escalation created: {escalation.reference_id} for {farmer_profile.name}")
            
            return escalation
            
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return None


# Global instance
_escalation_service_instance: Optional[EscalationService] = None


def get_escalation_service() -> EscalationService:
    """Get or create the global escalation service."""
    global _escalation_service_instance
    if _escalation_service_instance is None:
        _escalation_service_instance = EscalationService()
    return _escalation_service_instance
