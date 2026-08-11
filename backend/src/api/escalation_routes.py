"""
Escalation API Routes for Discord adviser interactions.

Endpoints:
- GET /api/escalations/open - Get open escalations for Discord
- POST /api/escalations/{reference_id}/resolve - Resolve an escalation
- GET /api/escalations/{reference_id} - Get escalation details
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from database.escalation_repository import get_escalation_repository
from database.farmer_repository import get_farmer_repository
from services.discord_service import get_discord_service
from services.escalation_callback_service import get_escalation_callback_service

logger = logging.getLogger("escalation_routes")


# Pydantic models
class ResolveEscalationRequest(BaseModel):
    """Request to resolve an escalation."""
    human_answer: str
    resolution_notes: Optional[str] = None
    adviser_id: Optional[str] = None


class EscalationResponse(BaseModel):
    """Response with escalation details."""
    reference_id: str
    farmer_name: str
    district: Optional[str]
    reason: str
    original_question: str
    summary: str
    urgency: str
    status: str
    callback_status: str
    created_at: str


class OpenEscalationsResponse(BaseModel):
    """Response with list of open escalations."""
    escalations: list
    total: int


# Route handlers
async def get_open_escalations() -> Dict[str, Any]:
    """
    Get all open escalations for Discord display.
    
    Returns:
        List of open escalations
    """
    try:
        escalation_repo = get_escalation_repository()
        escalations = escalation_repo.get_open_escalations(limit=100)
        
        logger.info(f"Retrieved {len(escalations)} open escalations")
        
        return {
            "status": "success",
            "escalations": [e.to_dict() for e in escalations],
            "total": len(escalations),
        }
        
    except Exception as e:
        logger.error(f"Error fetching open escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_escalation_details(reference_id: str) -> Dict[str, Any]:
    """
    Get details for a specific escalation.
    
    Args:
        reference_id: Escalation reference ID
    
    Returns:
        Escalation details
    """
    try:
        escalation_repo = get_escalation_repository()
        escalation = escalation_repo.get_escalation_by_reference(reference_id)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        return {
            "status": "success",
            "escalation": escalation.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def resolve_escalation(
    reference_id: str,
    request: ResolveEscalationRequest,
) -> Dict[str, Any]:
    """
    Resolve an escalation with human answer.
    Automatically queues callback to farmer.
    
    Args:
        reference_id: Escalation reference ID
        request: Resolution request with human answer
    
    Returns:
        Resolution result
    """
    try:
        # Validate input
        if not request.human_answer or not request.human_answer.strip():
            raise HTTPException(status_code=400, detail="Human answer is required")
        
        escalation_repo = get_escalation_repository()
        
        # Get current escalation
        escalation = escalation_repo.get_escalation_by_reference(reference_id)
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Check if already resolved (idempotency)
        if escalation.status == "RESOLVED":
            logger.info(f"Escalation already resolved: {reference_id}")
            return {
                "status": "success",
                "message": "Escalation already resolved",
                "reference_id": reference_id,
                "callback_status": escalation.callback_status,
            }
        
        # Resolve the escalation atomically
        resolved = escalation_repo.resolve_escalation(
            reference_id=reference_id,
            human_answer=request.human_answer,
            resolution_notes=request.resolution_notes,
        )
        
        if not resolved:
            raise HTTPException(status_code=500, detail="Failed to resolve escalation")
        
        logger.info(f"Escalation resolved: {reference_id}")
        
        # Queue callback asynchronously (don't wait for it to complete)
        callback_service = get_escalation_callback_service()
        asyncio.create_task(callback_service.queue_callback(reference_id))
        
        # Update Discord status
        discord_service = get_discord_service()
        discord_service.update_escalation_status(
            reference_id=reference_id,
            status="RESOLVED",
            callback_status="QUEUED",
        )
        
        return {
            "status": "success",
            "message": "Escalation resolved. Callback queued.",
            "reference_id": reference_id,
            "callback_status": "QUEUED",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
