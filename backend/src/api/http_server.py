"""
FastAPI HTTP Server for Kisan Mitra backend APIs.

Provides REST endpoints for:
- Weather alert outbound calling
- Call status queries
- Escalation management and resolution

Run with: uvicorn src.api.http_server:app --host 0.0.0.0 --port 8080 --reload
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables from .env.local FIRST (before any imports that use env vars)
env_path = Path(__file__).parent.parent.parent / ".env.local"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env.local from {env_path}")
else:
    print(f"[WARN] No .env.local found at {env_path}")

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.weather_alert_route import (
    initiate_weather_alert_call,
    get_weather_alert_call_status
)
from api.escalation_routes import router as escalation_router
from database.db import get_database

logger = logging.getLogger("api_server")

# Initialize database on startup
try:
    db = get_database()
    logger.info("Database initialized for API server")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Initialize FastAPI app (single instance)
app = FastAPI(
    title="Kisan Mitra API",
    description="Backend API for Kisan Mitra outbound weather alerts and escalation management",
    version="1.0.0"
)

# Configure CORS - allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://*.vercel.app",  # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include escalation routes
app.include_router(escalation_router, prefix="/api/escalations", tags=["escalations"])


# Startup event to initialize service
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        from services.outbound_weather_service import get_outbound_weather_service
        service = get_outbound_weather_service()
        is_enabled = service.is_enabled()
        logger.info(f"Outbound weather service initialized (enabled={is_enabled})")
        if is_enabled:
            logger.info(f"[OK] SIP Trunk ID: {service.sip_trunk_id}")
            logger.info(f"[OK] Linphone URI configured: {service._mask_uri(service.linphone_sip_uri)}")
        else:
            logger.warning("[WARN] Outbound weather service is not properly configured")
    except Exception as e:
        logger.error(f"Failed to initialize outbound weather service: {e}", exc_info=True)
    
    # Initialize Discord service
    try:
        from services.discord_service import get_discord_service
        discord_svc = get_discord_service()
        if discord_svc.enabled:
            logger.info("[Discord] Discord service enabled - initializing bot")
            if discord_svc.initialize_bot():
                logger.info("[Discord] Bot client initialized")
        else:
            logger.info("[Discord] Discord service not configured")
    except Exception as e:
        logger.error(f"Failed to initialize Discord service: {e}", exc_info=True)


# Request/Response Models
class WeatherAlertRequest(BaseModel):
    """Request body for weather alert call."""
    action: str
    user_id: Optional[str] = None  # Optional farmer user ID for personalization


class WeatherAlertResponse(BaseModel):
    """Response for weather alert call."""
    success: bool
    call_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    weather: Optional[dict] = None
    error: Optional[str] = None
    room_name: Optional[str] = None   # LiveKit room name for the outbound call


class CallStatusResponse(BaseModel):
    """Response for call status query."""
    success: bool
    call_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "kisan-mitra-api"}


# Weather Alert Call Endpoint
@app.post("/api/weather-alert/call", response_model=WeatherAlertResponse)
async def initiate_weather_alert(request: WeatherAlertRequest):
    """
    Initiate an outbound weather alert call.
    
    This endpoint triggers a real SIP call to the configured Linphone account
    with weather information for the farmer's district.
    
    Args:
        request: Request containing action type
        
    Returns:
        Call details with status and weather information
        
    Raises:
        HTTPException: On invalid request or configuration errors
    """
    try:
        # Validate action
        if request.action != "initiate_weather_alert":
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "INVALID_ACTION",
                    "message": "Invalid action specified. Use 'initiate_weather_alert'."
                }
            )
        
        # Trigger the weather alert call
        logger.info("[API] Triggering weather alert call")
        result = await initiate_weather_alert_call(request.user_id)
        logger.info(f"[API] Result: call_id={result.get('call_id')}, status={result.get('status')}")
        
        # Return appropriate HTTP status
        if not result.get("success"):
            error_code = result.get("error", "UNKNOWN_ERROR")
            
            # Map error codes to HTTP status codes
            status_codes = {
                "DISABLED": 503,
                "WEATHER_UNAVAILABLE": 503,
                "INTERNAL_ERROR": 500,
            }
            
            status_code = status_codes.get(error_code, 500)
            
            raise HTTPException(
                status_code=status_code,
                detail=result
            )
        
        logger.info(f"[API] Weather alert call initiated: {result.get('call_id')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred."
            }
        )


# Call Status Endpoint
@app.get("/api/weather-alert/call/{call_id}", response_model=CallStatusResponse)
async def get_weather_call_status(call_id: str):
    """
    Get the status of a weather alert call.
    
    Args:
        call_id: Unique call identifier
        
    Returns:
        Current call status
        
    Raises:
        HTTPException: If call not found
    """
    try:
        logger.info(f"[API] Getting status for call: {call_id}")
        result = await get_weather_alert_call_status(call_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to retrieve call status."
            }
        )


# Run with: uvicorn src.api.http_server:app --host 0.0.0.0 --port 8080 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
