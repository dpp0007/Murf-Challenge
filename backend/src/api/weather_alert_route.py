"""
Weather Alert API Route Handler.

HTTP endpoints for outbound weather alert calling.
This is a standalone module that can be imported into FastAPI or other frameworks.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("weather_alert_route")


async def initiate_weather_alert_call(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Initiate a demo weather alert call.
    
    This is the main entry point for the weather alert button.
    
    Args:
        user_id: Optional farmer user ID for personalization
    
    Returns:
        Response dict with call status or error
    """
    try:
        # Import here to avoid circular dependencies
        from services.outbound_weather_service import get_outbound_weather_service
        
        service = get_outbound_weather_service()
        result = await service.initiate_demo_weather_alert(user_id=user_id)
        
        logger.info(f"[WeatherAlertRoute] Call initiated: {result.get('call_id', 'unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"[WeatherAlertRoute] Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": f"An internal error occurred: {str(e)}"
        }


async def get_weather_alert_call_status(call_id: str) -> Dict[str, Any]:
    """
    Get the status of a weather alert call.
    
    Args:
        call_id: Call identifier
        
    Returns:
        Call status or error
    """
    try:
        from services.outbound_weather_service import get_outbound_weather_service
        
        service = get_outbound_weather_service()
        status = service.get_call_status(call_id)
        
        if not status:
            logger.warning(f"[WeatherAlertRoute] Call not found: {call_id}")
            return {
                "success": False,
                "error": "CALL_NOT_FOUND",
                "message": "Call not found."
            }
        
        return {
            "success": True,
            **status
        }
        
    except Exception as e:
        logger.error(f"[WeatherAlertRoute] Status error: {e}", exc_info=True)
        return {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "An internal error occurred."
        }
