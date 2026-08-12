"""
Escalation API Routes for INTERNAL use by Discord bot.

⚠️ SECURITY: These routes are for INTERNAL use only.
They should NOT be exposed to the public internet.

The Discord bot should call these service methods directly,
NOT make HTTP requests to public endpoints.

If public HTTP endpoint is needed, add authentication:
- Check Authorization header
- Require internal API token from environment
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from database.escalation_repository import get_escalation_repository
from database.farmer_repository import get_farmer_repository
from services.discord_service import get_discord_service
from services.escalation_callback_service import get_escalation_callback_service

logger = logging.getLogger("escalation_routes")

# Create FastAPI router
router = APIRouter()

# ============================================================================
# SECURITY: Internal API Token for escalation endpoint
# ============================================================================
import os

INTERNAL_API_TOKEN = os.getenv("ESCALATION_INTERNAL_API_TOKEN")

def validate_internal_api_token(authorization: Optional[str] = Header(None)) -> bool:
    """
    Validate that request has the internal API token.
    
    ⚠️ CRITICAL: This prevents external users from resolving escalations.
    
    Args:
        authorization: Authorization header value
    
    Returns:
        True if token is valid
    
    Raises:
        HTTPException: If token missing or invalid
    """
    if not INTERNAL_API_TOKEN:
        logger.error(
            "[Security] ESCALATION_INTERNAL_API_TOKEN not configured. "
            "Escalation resolution endpoints are DISABLED for security."
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SERVICE_NOT_CONFIGURED",
                "message": "Escalation resolution is not configured"
            }
        )
    
    if not authorization:
        logger.warning("[Security] Escalation resolution request missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Missing Authorization header"}
        )
    
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        logger.warning("[Security] Invalid Authorization header format")
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid Authorization format"}
        )
    
    token = authorization[7:]  # Remove "Bearer "
    
    if token != INTERNAL_API_TOKEN:
        logger.warning("[Security] Invalid Authorization token")
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid token"}
        )
    
    return True


# ============================================================================
# Pydantic models
# ============================================================================

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


# ============================================================================
# Route handlers - INTERNAL ONLY
# ============================================================================

@router.get("/open", response_model=OpenEscalationsResponse)
async def get_open_escalations(
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Get all open escalations for Discord display.
    
    ⚠️ REQUIRES: ESCALATION_INTERNAL_API_TOKEN in Authorization header
    
    Returns:
        List of open escalations
    """
    try:
        # Validate API token
        validate_internal_api_token(authorization)
        
        escalation_repo = get_escalation_repository()
        escalations = escalation_repo.get_open_escalations(limit=100)
        
        logger.info(f"[API] Retrieved {len(escalations)} open escalations (authenticated)")
        
        return {
            "escalations": [e.to_dict() for e in escalations],
            "total": len(escalations),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error fetching open escalations: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/{reference_id}", response_model=Dict[str, Any])
async def get_escalation_details(
    reference_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Get details for a specific escalation.
    
    ⚠️ REQUIRES: ESCALATION_INTERNAL_API_TOKEN in Authorization header
    
    Args:
        reference_id: Escalation reference ID
    
    Returns:
        Escalation details
    """
    try:
        # Validate API token
        validate_internal_api_token(authorization)
        
        escalation_repo = get_escalation_repository()
        escalation = escalation_repo.get_escalation_by_reference(reference_id)
        
        if not escalation:
            logger.warning(f"[API] Escalation not found: {reference_id}")
            raise HTTPException(status_code=404, detail={"error": "Escalation not found"})
        
        logger.info(f"[API] Retrieved escalation: {reference_id} (authenticated)")
        
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
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Resolve an escalation with human answer.
    Automatically queues callback to farmer.
    
    ⚠️ SECURITY-CRITICAL: REQUIRES INTERNAL API TOKEN
    
    This endpoint should ONLY be called by:
    - Discord bot (with Authorization header)
    - Internal service-to-service calls
    - NEVER exposed to external/public clients
    
    Args:
        reference_id: Escalation reference ID
        request: Resolution request with human answer
        authorization: Authorization header with ESCALATION_INTERNAL_API_TOKEN
    
    Returns:
        Resolution result with callback status
    """
    try:
        # SECURITY: Validate API token FIRST - before any processing
        validate_internal_api_token(authorization)
        
        logger.info(f"[API] AUTHORIZED resolution request: {reference_id}")
        
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
        callback_service = get_escalation_callback_service()
        asyncio.create_task(callback_service.queue_callback(reference_id))
        logger.info(f"[API] Callback queued asynchronously: {reference_id}")
        
        # Note: Discord status update is handled by Discord service slash command handler
        # Don't update here to avoid duplicate messages
        
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
            detail={"error": "Internal server error"}
        )


@router.post("/notify-discord")
async def notify_discord(request: Dict[str, str]):
    """
    Internal endpoint to send Discord notification for an escalation.
    Called by the agent process to notify Discord in the HTTP server process.
    
    This is an INTERNAL endpoint (no authentication needed).
    It's only called from localhost by the agent process.
    
    Args:
        reference_id: Escalation reference ID to notify about
    
    Returns:
        Status of notification
    """
    try:
        reference_id = request.get("reference_id")
        if not reference_id:
            raise HTTPException(
                status_code=400,
                detail={"error": "reference_id is required"}
            )
        
        logger.info(f"[API] Discord notification request: {reference_id}")
        
        # Get escalation
        escalation_repo = get_escalation_repository()
        escalation = escalation_repo.get_escalation_by_reference(reference_id)
        
        if not escalation:
            logger.warning(f"[API] Escalation not found for notification: {reference_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Escalation not found"}
            )
        
        # Send Discord notification
        discord_service = get_discord_service()
        if not discord_service.enabled:
            logger.warning(f"[API] Discord not enabled, skipping notification")
            return {
                "status": "skipped",
                "message": "Discord notifications disabled"
            }
        
        # Queue the notification as a background task instead of awaiting directly
        # This avoids asyncio context issues with discord.py
        try:
            asyncio.create_task(discord_service._send_notification_async(escalation))
            logger.info(f"[API] Discord notification task created: {reference_id}")
            return {
                "status": "success",
                "message": "Discord notification queued",
                "reference_id": reference_id
            }
        except Exception as e:
            logger.error(f"[API] Failed to queue notification task: {e}")
            return {
                "status": "failed",
                "message": "Could not queue Discord notification",
                "reference_id": reference_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error in Discord notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error"}
        )
