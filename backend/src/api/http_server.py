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


# Debug endpoint for Discord command syncing
@app.post("/api/discord/sync-commands")
async def sync_discord_commands():
    """
    Manually sync Discord slash commands to the guild.
    Use this if /resolve command is not appearing in Discord.
    
    Call with: curl -X POST http://localhost:8080/api/discord/sync-commands
    
    Returns:
        Status of sync operation
    """
    try:
        from services.discord_service import get_discord_service
        import asyncio
        
        discord_svc = get_discord_service()
        
        if not discord_svc.enabled:
            return {
                "status": "error",
                "message": "Discord service not configured"
            }
        
        if not discord_svc.bot or not discord_svc.bot.user:
            return {
                "status": "error",
                "message": "Discord bot not connected - wait for bot to connect"
            }
        
        # Try guild sync first
        guild = discord_svc.bot.get_guild(discord_svc.guild_id)
        guild_result = None
        
        if guild:
            try:
                print(f"[Sync API] Syncing to guild {guild.name}...")
                synced = await discord_svc.bot.tree.sync(guild=guild)
                guild_result = [cmd.name for cmd in synced]
                print(f"[Sync API] Guild sync result: {guild_result}")
            except Exception as e:
                print(f"[Sync API] Guild sync failed: {e}")
        
        # Also do global sync
        try:
            print(f"[Sync API] Doing global sync...")
            # Run in bot's event loop
            if discord_svc._bot_loop:
                future = asyncio.run_coroutine_threadsafe(
                    discord_svc.bot.tree.sync(),
                    discord_svc._bot_loop
                )
                global_synced = future.result(timeout=10)
                global_result = [cmd.name for cmd in global_synced]
                print(f"[Sync API] Global sync result: {global_result}")
            else:
                global_result = None
        except Exception as e:
            print(f"[Sync API] Global sync failed: {e}")
            global_result = None
        
        logger.info(f"[API] Discord sync completed - guild: {guild_result}, global: {global_result}")
        
        return {
            "status": "success",
            "message": "Commands synced",
            "guild_synced": guild_result,
            "global_synced": global_result
        }
        
    except Exception as e:
        logger.error(f"[API] Error syncing Discord commands: {e}", exc_info=True)
        print(f"[Sync API] Error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# Startup event to initialize service
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("[STARTUP] Startup event triggered")
    logger.info("[STARTUP] Startup event triggered")
    
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
        print("[STARTUP] Initializing Discord service...")
        logger.info("[STARTUP] Initializing Discord service...")
        from services.discord_service import get_discord_service
        discord_svc = get_discord_service()
        print(f"[STARTUP] Discord service obtained, enabled={discord_svc.enabled}")
        logger.info(f"[STARTUP] Discord service obtained, enabled={discord_svc.enabled}")
        
        if discord_svc.enabled:
            logger.info("[Discord] Discord service enabled - initializing bot")
            print("[Discord] Discord service enabled - initializing bot")
            bot_init_result = discord_svc.initialize_bot()
            print(f"[Discord] initialize_bot() returned: {bot_init_result}")
            logger.info(f"[Discord] initialize_bot() returned: {bot_init_result}")
            if bot_init_result:
                logger.info("[Discord] ✅ Bot client initialized and should be starting in background")
                print("[Discord] ✅ Bot client initialized and should be starting in background")
            else:
                logger.error("[Discord] ❌ Bot client initialization returned False")
                print("[Discord] ❌ Bot client initialization returned False")
        else:
            logger.info("[Discord] Discord service not configured")
            print("[Discord] Discord service not configured")
    except Exception as e:
        print(f"[STARTUP] Exception during Discord initialization: {e}")
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


# Discord status endpoint
@app.get("/api/discord/status")
async def discord_status():
    """Get Discord bot status and command info."""
    try:
        from services.discord_service import get_discord_service
        
        discord_svc = get_discord_service()
        
        if not discord_svc.enabled:
            return {
                "enabled": False,
                "reason": "Discord not configured"
            }
        
        if not discord_svc.bot:
            return {
                "enabled": True,
                "connected": False,
                "reason": "Bot not initialized"
            }
        
        is_connected = discord_svc.bot.user is not None
        
        commands = list(discord_svc.bot.tree._get_all_commands()) if discord_svc.bot else []
        
        return {
            "enabled": True,
            "connected": is_connected,
            "bot_name": str(discord_svc.bot.user) if discord_svc.bot.user else None,
            "guild_id": discord_svc.guild_id,
            "guild_name": discord_svc.bot.get_guild(discord_svc.guild_id).name if is_connected else None,
            "commands_registered": [cmd.name for cmd in commands],
            "total_commands": len(commands)
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting Discord status: {e}")
        return {
            "enabled": True,
            "error": str(e)
        }


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
