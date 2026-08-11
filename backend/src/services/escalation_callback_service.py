"""
Escalation Callback Service - Handles automatic callbacks for resolved escalations.

Integrates with existing outbound calling service.
Passes escalation context to the agent.
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any

from database.escalation_repository import get_escalation_repository
from database.farmer_repository import get_farmer_repository
from services.outbound_weather_service import get_outbound_weather_service

logger = logging.getLogger("escalation_callback_service")


class EscalationCallbackService:
    """Service for managing escalation callbacks."""
    
    def __init__(self):
        """Initialize the service."""
        self.escalation_repo = get_escalation_repository()
        self.farmer_repo = get_farmer_repository()
        self.outbound_service = get_outbound_weather_service()
        self.max_retries = int(os.getenv("CALLBACK_MAX_RETRIES", "2"))
    
    async def queue_callback(self, reference_id: str) -> bool:
        """
        Queue an escalation callback for execution.
        
        This is called when an adviser resolves an escalation.
        It should NOT wait for the actual call to complete.
        
        Args:
            reference_id: Escalation reference ID
        
        Returns:
            True if queued successfully
        """
        try:
            # Get the escalation
            escalation = self.escalation_repo.get_escalation_by_reference(reference_id)
            if not escalation:
                logger.warning(f"Escalation not found: {reference_id}")
                return False
            
            # Check if already resolved (idempotency)
            if escalation.status != "RESOLVED":
                logger.warning(f"Escalation not resolved yet: {reference_id}")
                return False
            
            if escalation.callback_status != "QUEUED":
                logger.warning(f"Escalation callback not queued: {reference_id}")
                return False
            
            # Check farmer opt-out status
            farmer_profile = self.farmer_repo.lookup_farmer(escalation.user_id)
            if farmer_profile and not farmer_profile.outbound_calls_enabled:
                logger.info(f"Farmer opted out - skipping callback: {reference_id}")
                self.escalation_repo.update_callback_status(
                    reference_id,
                    "SKIPPED_OPT_OUT",
                    "Farmer has disabled outbound calls"
                )
                return True
            
            # Trigger the callback asynchronously
            asyncio.create_task(self._execute_callback(escalation))
            
            return True
            
        except Exception as e:
            logger.error(f"Error queuing callback: {e}")
            return False
    
    async def _execute_callback(self, escalation: Any) -> bool:
        """
        Execute the actual callback for an escalation.
        
        Args:
            escalation: Escalation object
        
        Returns:
            True if call was successfully initiated
        """
        try:
            reference_id = escalation.reference_id
            user_id = escalation.user_id
            
            logger.info(f"Initiating escalation callback: {reference_id}")
            
            # Build the callback context
            callback_context = {
                "call_type": "escalation_resolution",
                "reference_id": reference_id,
                "user_id": user_id,
                "farmer_name": escalation.farmer_name,
                "language": escalation.language,
                "original_question": escalation.original_question,
                "human_answer": escalation.human_answer,
                "reason": escalation.reason,
                "district": escalation.district,
            }
            
            # Use existing outbound calling service
            # We need to extend it to handle escalation callbacks
            result = await self.outbound_service.initiate_escalation_callback(
                user_id=user_id,
                context=callback_context
            )
            
            if result.get("success"):
                # Update status to CALLING
                self.escalation_repo.update_callback_status(reference_id, "CALLING")
                logger.info(f"Escalation callback initiated: {reference_id}")
                return True
            else:
                logger.warning(f"Failed to initiate callback: {result.get('error')}")
                # Retry logic could go here
                self.escalation_repo.update_callback_status(
                    reference_id,
                    "FAILED",
                    result.get("error", "Unknown error")
                )
                return False
            
        except Exception as e:
            logger.error(f"Error executing callback: {e}")
            self.escalation_repo.update_callback_status(
                escalation.reference_id,
                "FAILED",
                str(e)
            )
            return False
    
    async def handle_callback_completed(
        self,
        call_id: str,
        reference_id: str,
        success: bool = True,
        error: Optional[str] = None,
    ) -> bool:
        """
        Handle callback completion status update.
        
        Called by the agent or call tracking system when a call ends.
        
        Args:
            call_id: LiveKit call ID
            reference_id: Escalation reference ID
            success: Whether the call was successful
            error: Error message if applicable
        
        Returns:
            True if status was updated
        """
        try:
            if success:
                status = "COMPLETED"
            else:
                status = "FAILED"
            
            return self.escalation_repo.update_callback_status(
                reference_id,
                status,
                error
            )
            
        except Exception as e:
            logger.error(f"Error updating callback completion: {e}")
            return False
    
    def should_retry_callback(self, escalation: Any) -> bool:
        """
        Determine if a callback should be retried.
        
        Args:
            escalation: Escalation object
        
        Returns:
            True if retry should be attempted
        """
        # Don't retry if opt-out
        if escalation.callback_status == "SKIPPED_OPT_OUT":
            return False
        
        # Don't retry if successfully completed
        if escalation.callback_status == "COMPLETED":
            return False
        
        # Retry only NO_ANSWER and FAILED
        if escalation.callback_status not in ("NO_ANSWER", "FAILED"):
            return False
        
        # Check retry limit
        if escalation.callback_attempts >= self.max_retries:
            logger.info(f"Max retries reached: {escalation.reference_id}")
            return False
        
        return True


# Global instance
_callback_service_instance: Optional[EscalationCallbackService] = None


def get_escalation_callback_service() -> EscalationCallbackService:
    """Get or create the global escalation callback service."""
    global _callback_service_instance
    if _callback_service_instance is None:
        _callback_service_instance = EscalationCallbackService()
    return _callback_service_instance
