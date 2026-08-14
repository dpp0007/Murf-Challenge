"""
Escalation Tools - Function tools for the Kisan Mitra agent.

Provides:
- create_escalation() - For agent to escalate serious issues
"""

import logging
from typing import Optional
from livekit.agents import function_tool, RunContext

try:
    from ..services.escalation_service import (
        get_escalation_service,
        EscalationReason,
    )
    from ..database.farmer_repository import get_farmer_repository
except (ImportError, ValueError):
    from services.escalation_service import (
        get_escalation_service,
        EscalationReason,
    )
    from database.farmer_repository import get_farmer_repository

logger = logging.getLogger("escalation_tools")


class EscalationTools:
    """Escalation-related tools for the agent."""
    
    def __init__(self):
        """Initialize escalation tools."""
        self.escalation_service = get_escalation_service()
        self.farmer_repo = get_farmer_repository()
    
    @function_tool
    async def create_escalation(
        self,
        ctx: RunContext,
        reason: str,
        summary: str,
        original_question: str,
        what_agent_checked: str,
        urgency: str = "MEDIUM",
        preferred_followup: str = "phone",
    ) -> str:
        """
        Create an escalation request for human adviser review.
        
        IMPORTANT: This tool should ONLY be called after:
        1. Agent determined human help is needed
        2. Agent asked farmer for permission
        3. Farmer gave explicit permission (हाँ, Yes, ठीक है, etc.)
        
        Do NOT call this tool if farmer declined.
        
        Args:
            reason: Escalation reason - must be one of:
                - SERIOUS_CROP_PROBLEM
                - MARKET_DATA_UNAVAILABLE
                - UNCERTAIN_DIAGNOSIS
                - OTHER
            summary: Brief summary of the issue (max 500 chars)
            original_question: The farmer's original question
            what_agent_checked: What the agent verified before escalating
            urgency: LOW, MEDIUM, HIGH (default: MEDIUM)
            preferred_followup: phone, whatsapp, etc. (default: phone)
        
        Returns:
            JSON string with escalation reference ID and status
        """
        try:
            # Get room name from context to extract user_id
            room_name = ctx.room.name if hasattr(ctx, 'room') else None
            if not room_name:
                logger.error("No room context available for escalation")
                return '{"status": "error", "message": "No user context"}'
            
            user_id = room_name
            
            # Validate reason
            valid_reasons = [e.value for e in EscalationReason]
            if reason not in valid_reasons:
                logger.warning(f"Invalid escalation reason: {reason}")
                return '{"status": "error", "message": "Invalid reason"}'
            
            # Validate summary length
            if not summary or len(summary) > 1000:
                logger.warning(f"Invalid summary length: {len(summary) if summary else 0}")
                return '{"status": "error", "message": "Summary too long or empty"}'
            
            # Validate question
            if not original_question:
                logger.warning("Empty original question")
                return '{"status": "error", "message": "Original question required"}'
            
            # Create escalation
            escalation = self.escalation_service.create_escalation(
                user_id=user_id,
                reason=EscalationReason(reason),
                original_question=original_question,
                summary=summary,
                what_agent_checked=what_agent_checked,
                urgency=urgency,
                preferred_followup=preferred_followup,
            )
            
            if not escalation:
                logger.warning(f"Failed to create escalation for user {user_id}")
                return '{"status": "error", "message": "Could not create escalation"}'
            
            logger.info(f"Escalation created: {escalation.reference_id} by {user_id}")
            
            return f'''{{
                "status": "success",
                "reference_id": "{escalation.reference_id}",
                "message": "आपकी समस्या कृषि सलाहकार के पास भेज दी गई है। वे जल्द ही आपसे संपर्क करेंगे।"
            }}'''
            
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return f'{{"status": "error", "message": "Server error"}}'


# Global instance
_escalation_tools_instance: Optional[EscalationTools] = None


def get_escalation_tools() -> EscalationTools:
    """Get or create the global escalation tools."""
    global _escalation_tools_instance
    if _escalation_tools_instance is None:
        _escalation_tools_instance = EscalationTools()
    return _escalation_tools_instance
