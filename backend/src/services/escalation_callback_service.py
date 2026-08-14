"""
Escalation Callback Service - Handles automatic callbacks for resolved escalations.

Integrates with existing outbound calling service.
Passes escalation context to the agent.
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any

try:
    from ..database.escalation_repository import get_escalation_repository
    from ..database.farmer_repository import get_farmer_repository
    from .outbound_weather_service import get_outbound_weather_service
except (ImportError, ValueError):
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
        
        CRITICAL: This method ATOMICALLY updates DB status BEFORE spawning async task
        to prevent race conditions where multiple callbacks are queued for same escalation.
        
        This is called when an adviser resolves an escalation.
        It should NOT wait for the actual call to complete.
        
        Args:
            reference_id: Escalation reference ID
        
        Returns:
            True if queued successfully
        """
        try:
            print(f"\n[QUEUE_CALLBACK] START ref_id={reference_id}")
            logger.info(f"[QUEUE_CALLBACK] Processing callback queue: {reference_id}")
            
            # Get the escalation
            escalation = self.escalation_repo.get_escalation_by_reference(reference_id)
            if not escalation:
                logger.warning(f"Escalation not found: {reference_id}")
                print(f"[QUEUE_CALLBACK] ERROR: Escalation not found")
                return False
            
            print(f"[QUEUE_CALLBACK] Escalation found: status={escalation.status}, callback={escalation.callback_status}")
            
            # CRITICAL: Check escalation is RESOLVED (not just checking callback status)
            if escalation.status != "RESOLVED":
                logger.warning(f"Escalation not resolved yet: {reference_id} (status={escalation.status})")
                print(f"[QUEUE_CALLBACK] ERROR: Not resolved (status={escalation.status})")
                return False
            
            # Check if callback already COMPLETED or FAILED (don't retry)
            if escalation.callback_status in ("COMPLETED", "SKIPPED_OPT_OUT"):
                logger.info(f"Callback already completed or skipped: {reference_id} -> {escalation.callback_status}")
                print(f"[QUEUE_CALLBACK] Already completed: {escalation.callback_status}")
                return True  # Already handled
            
            # If callback was CALLING or CONNECTED, wait to see if it completes
            if escalation.callback_status in ("CALLING", "CONNECTED"):
                logger.info(f"Callback currently in progress: {reference_id} -> {escalation.callback_status}")
                print(f"[QUEUE_CALLBACK] Still calling: {escalation.callback_status}")
                return True
            
            # If callback is QUEUED, it should already be executing
            # If it hasn't executed yet, we need to start the executor
            # This handles race conditions and retry scenarios
            if escalation.callback_status == "QUEUED":
                logger.info(f"Callback in QUEUED state, will ensure it executes: {reference_id}")
                print(f"[QUEUE_CALLBACK] Callback QUEUED, ensuring executor runs...")
                # Fall through to start executor
            
            # Check farmer opt-out status
            farmer_profile = self.farmer_repo.lookup_farmer(escalation.user_id)
            if farmer_profile and not farmer_profile.outbound_calls_enabled:
                logger.info(f"Farmer opted out - skipping callback: {reference_id}")
                print(f"[QUEUE_CALLBACK] Farmer opted out")
                self.escalation_repo.update_callback_status(
                    reference_id,
                    "SKIPPED_OPT_OUT",
                    "Farmer has disabled outbound calls"
                )
                return True
            
            print(f"[QUEUE_CALLBACK] Farmer opted-in, updating status to QUEUED...")
            
            # CRITICAL: Update callback status to QUEUED SYNCHRONOUSLY
            # This prevents concurrent calls from both seeing "NOT_STARTED"
            # By the time _execute_callback async task runs, DB already shows QUEUED
            update_ok = self.escalation_repo.update_callback_status(
                reference_id,
                "QUEUED",
                "Callback queued for execution"
            )
            
            if not update_ok:
                logger.error(f"Failed to update callback status to QUEUED: {reference_id}")
                print(f"[QUEUE_CALLBACK] ERROR: Failed to update DB status")
                return False
            
            print(f"[QUEUE_CALLBACK] DB status updated to QUEUED, creating async task...")
            logger.info(f"Callback status updated to QUEUED in database: {reference_id}")
            
            # Schedule the callback execution
            # We need to use the Discord service's bot loop to ensure it runs
            try:
                from services.discord_service import get_discord_service
                discord_svc = get_discord_service()
                
                if discord_svc._bot_loop:
                    print(f"[QUEUE_CALLBACK] Scheduling task in Discord bot loop...")
                    # Run the callback executor in the bot's event loop
                    future = asyncio.run_coroutine_threadsafe(
                        self._execute_callback(escalation),
                        discord_svc._bot_loop
                    )
                    print(f"[QUEUE_CALLBACK] Task scheduled in bot loop")
                    logger.info(f"Callback execution scheduled in Discord bot loop: {reference_id}")
                else:
                    print(f"[QUEUE_CALLBACK] No bot loop available, using create_task...")
                    task = asyncio.create_task(self._execute_callback(escalation))
                    print(f"[QUEUE_CALLBACK] Async task created: {task}")
                    logger.info(f"Callback execution task created: {reference_id}")
            except Exception as e:
                print(f"[QUEUE_CALLBACK] Failed to schedule in bot loop: {e}, falling back to create_task")
                logger.warning(f"Failed to use bot loop: {e}, using create_task")
                task = asyncio.create_task(self._execute_callback(escalation))
            
            print(f"[QUEUE_CALLBACK] SUCCESS - task queued")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing callback: {e}", exc_info=True)
            print(f"[QUEUE_CALLBACK] ERROR: {type(e).__name__}: {e}")
            return False
    
    async def _execute_callback(self, escalation: Any) -> bool:
        """
        Execute the actual callback for an escalation.
        
        Updates callback_status to reflect the SIP lifecycle:
        QUEUED → CALLING (when SIP dispatch started)
        CALLING → CONNECTED (when SIP participant actually joins)
        CONNECTED → COMPLETED (when call finishes naturally)
        or CALLING → FAILED (on SIP error)
        
        Args:
            escalation: Escalation object
        
        Returns:
            True if call was successfully initiated
        """
        try:
            reference_id = escalation.reference_id
            user_id = escalation.user_id
            
            logger.info(f"[ESCALATION_CALLBACK_EXEC_START] reference_id={reference_id}, user_id={user_id}")
            print(f"\n[CALLBACK EXECUTOR STARTED] ref_id={reference_id}")
            
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
            
            print(f"[CALLBACK EXECUTOR] Callback context built, initiating outbound call...")
            
            # Update status to CALLING immediately
            # This indicates SIP dispatch has started
            self.escalation_repo.update_callback_status(
                reference_id, 
                "CALLING",
                "SIP call dispatch initiated"
            )
            logger.info(f"[ESCALATION_CALLBACK_STATUS_CALLING] reference_id={reference_id}")
            print(f"[CALLBACK EXECUTOR] Status updated to CALLING")
            
            # Use existing outbound calling service with escalation context
            print(f"[CALLBACK EXECUTOR] Calling outbound service for escalation callback...")
            result = await self.outbound_service.initiate_escalation_callback(
                user_id=user_id,
                context=callback_context
            )
            
            print(f"[CALLBACK EXECUTOR] Outbound service result: {result}")
            
            if result.get("success"):
                # SIP dispatch successful
                # Note: We DON'T change to CONNECTED yet - that requires SIP participant to actually join
                logger.info(
                    f"[ESCALATION_CALLBACK_SIP_SUCCESS] "
                    f"reference_id={reference_id}, "
                    f"call_id={result.get('call_id')}, "
                    f"room={result.get('room_name')}"
                )
                print(f"[CALLBACK EXECUTOR] ✅ SIP call successfully initiated! call_id={result.get('call_id')}")
                # Leave as CALLING - will become CONNECTED when participant joins
                return True
            else:
                # SIP dispatch failed
                error = result.get('error', 'Unknown')
                error_msg = result.get('message', '')
                
                logger.warning(
                    f"[ESCALATION_CALLBACK_SIP_FAILED] "
                    f"reference_id={reference_id}, "
                    f"error={error}, "
                    f"message={error_msg}"
                )
                print(f"[CALLBACK EXECUTOR] ❌ SIP dispatch failed: {error} - {error_msg}")
                
                # Update status to FAILED
                self.escalation_repo.update_callback_status(
                    reference_id,
                    "FAILED",
                    f"SIP dispatch failed: {error}"
                )
                return False
            
        except Exception as e:
            logger.error(
                f"[ESCALATION_CALLBACK_EXEC_ERROR] "
                f"reference_id={escalation.reference_id}, "
                f"error={type(e).__name__}: {str(e)[:100]}"
            )
            print(f"[CALLBACK EXECUTOR] ❌ ERROR: {type(e).__name__}: {e}")
            self.escalation_repo.update_callback_status(
                escalation.reference_id,
                "FAILED",
                f"{type(e).__name__}: {str(e)[:50]}"
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
        Sends notification to Discord resolved channel if successful.
        
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
            
            updated = self.escalation_repo.update_callback_status(
                reference_id,
                status,
                error
            )
            
            # If successful, send to resolved channel
            if success and updated:
                try:
                    from services.discord_service import get_discord_service
                    escalation = self.escalation_repo.get_escalation_by_reference(reference_id)
                    if escalation:
                        discord_svc = get_discord_service()
                        # Get adviser name from resolution notes (format: "Resolved by <name>")
                        adviser_name = "Unknown Adviser"
                        if escalation.resolution_notes and "Resolved by" in escalation.resolution_notes:
                            adviser_name = escalation.resolution_notes.split("Resolved by ")[-1]
                        
                        await discord_svc.send_resolution_notification(escalation, adviser_name)
                except Exception as e:
                    logger.warning(f"[Callback] Failed to send Discord resolution notification: {e}")
            
            return updated
            
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
