"""
Escalation API Routes for Discord adviser interactions.

Endpoints:
- GET /open - Get open escalations for Discord
- POST /{reference_id}/resolve - Resolve an escalation
- GET /{reference_id} - Get escalation details
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.escalation_repository import get_escalation_repository
from database.farmer_repository import get_farmer_repository
from services.discord_service import get_discord_service
from services.escalation_callback_service import get_escalation_callback_service

logger = logging.getLogger("escalation_routes")

# Create FastAPI router
router = APIRouter()


# Pydantic models
class ResolveEscalationRequest(BaseModel):
    """Request to resolve an escalation."""
    human_answer: str
    resolution_notes: Optional[str] = None
    adviser_id: Optional[str] = None
    adviser_name: Optional[str] = None


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
    escalations: List[Dict[str, Any]]
    total: int


class ResolveEscalationResponse(BaseModel):
    """Response from resolve endpoint."""
    status: str
    message: str
    reference_id: str
    callback_status: str


# Route handlers
@router.get("/open", response_model=OpenEscalationsResponse)
async def get_open_escalations() -> Dict[str, Any]:
    """
    Get all open escalations for Discord display.
    
    Returns:
        List of open escalations
    """
    try:
        escalation_repo = get_escalation_repository()
        escalations = escalation_repo.get_open_escalations(limit=100)
        
        logger.info(f"[API] Retrieved {len(escalations)} open escalations")
        
        return {
            "escalations": [e.to_dict() for e in escalations],
            "total": len(escalations),
        }
        
    except Exception as e:
        logger.error(f"[API] Error fetching open escalations: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/{reference_id}", response_model=Dict[str, Any])
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
            logger.warning(f"[API] Escalation not found: {reference_id}")
            raise HTTPException(status_code=404, detail={"error": "Escalation not found"})
        
        logger.info(f"[API] Retrieved escalation: {reference_id}")
        
        return {
            "status": "success",
            "escalation": escalation.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error fetching escalation: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/{reference_id}/resolve", response_model=ResolveEscalationResponse)
async def resolve_escalation(
    reference_id: str,
    request: ResolveEscalationRequest,
) -> Dict[str, Any]:
    """
    Resolve an escalation with human answer.
    Automatically queues callback to farmer.
    
    CRITICAL: This endpoint is called by authorized advisers to submit their answer.
    The callback is automatically triggered and placed to the farmer's phone.
    
    Args:
        reference_id: Escalation reference ID
        request: Resolution request with human answer
    
    Returns:
        Resolution result with callback status
    """
    try:
        logger.info(f"[API] Resolving escalation: {reference_id}")
        
        # Validate input
        if not request.human_answer or not request.human_answer.strip():
            logger.warning(f"[API] Empty human answer for {reference_id}")
            raise HTTPException(
                status_code=400, 
                detail={"error": "Human answer is required"}
            )
        
        if len(request.human_answer) > 5000:
            logger.warning(f"[API] Human answer too long for {reference_id}")
            raise HTTPException(
                status_code=400,
                detail={"error": "Human answer is too long (max 5000 characters)"}
            )
        
        escalation_repo = get_escalation_repository()
        
        # Get current escalation
        escalation = escalation_repo.get_escalation_by_reference(reference_id)
        if not escalation:
            logger.error(f"[API] Escalation not found: {reference_id}")
            raise HTTPException(
                status_code=404, 
                detail={"error": "Escalation not found"}
            )
        
        logger.info(f"[API] Escalation status: {escalation.status}, callback_status: {escalation.callback_status}")
        
        # Check if already resolved (idempotency protection)
        if escalation.status == "RESOLVED":
            if escalation.callback_status in ("QUEUED", "CALLING", "CONNECTED", "COMPLETED"):
                logger.info(f"[API] Escalation already resolved with callback: {reference_id}")
                return {
                    "status": "success",
                    "message": "Escalation already resolved. Callback already queued.",
                    "reference_id": reference_id,
                    "callback_status": escalation.callback_status,
                }
            else:
                logger.info(f"[API] Escalation already resolved: {reference_id}")
                return {
                    "status": "success",
                    "message": "Escalation already resolved.",
                    "reference_id": reference_id,
                    "callback_status": escalation.callback_status,
                }
        
        # Resolve the escalation atomically (critical for duplicate prevention)
        logger.info(f"[API] Atomically resolving escalation: {reference_id}")
        resolved = escalation_repo.resolve_escalation(
            reference_id=reference_id,
            human_answer=request.human_answer.strip(),
            resolution_notes=request.resolution_notes,
        )
        
        if not resolved:
            logger.error(f"[API] Failed to atomically resolve {reference_id}")
            raise HTTPException(
                status_code=500, 
                detail={"error": "Failed to resolve escalation"}
            )
        
        logger.info(f"[API] Escalation resolved atomically: {reference_id} -> status=RESOLVED, callback_status=QUEUED")
        
        # Queue callback asynchronously (don't wait for it to complete)
        # This is critical - we don't block the HTTP response on the callback
        callback_service = get_escalation_callback_service()
        asyncio.create_task(callback_service.queue_callback(reference_id))
        logger.info(f"[API] Callback queued asynchronously: {reference_id}")
        
        # Update Discord status (async, don't block)
        try:
            discord_service = get_discord_service()
            asyncio.create_task(discord_service.update_escalation_status(
                reference_id=reference_id,
                status="RESOLVED",
                callback_status="QUEUED",
            ))
        except Exception as e:
            logger.warning(f"[API] Could not update Discord status: {e}")
        
        logger.info(f"[API] Resolution complete: {reference_id}")
        
        return {
            "status": "success",
            "message": "Escalation resolved. Automatic callback queued to farmer.",
            "reference_id": reference_id,
            "callback_status": "QUEUED",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error resolving escalation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={"error": "Internal server error", "detail": str(e)}
        )
