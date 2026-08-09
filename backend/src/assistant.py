"""
Kisan Mitra Assistant - Production-ready agriculture voice assistant.
This module contains the core Assistant class with clean architecture.
Includes function tools for weather and mandi price queries.
"""

import logging
from typing import Optional
from livekit.agents import Agent, function_tool, RunContext

# Handle both relative and absolute imports
try:
    from .prompts import get_system_prompt
    from .config import ASSISTANT_NAME
    from .services.weather_service import WeatherService
    from .services.mandi_service import get_mandi_service
    from .tools.farmer_memory import get_farmer_memory_tools
except ImportError:
    from prompts import get_system_prompt
    from config import ASSISTANT_NAME
    from services.weather_service import WeatherService
    from services.mandi_service import get_mandi_service
    from tools.farmer_memory import get_farmer_memory_tools

logger = logging.getLogger("assistant")


class KisanMitraAssistant(Agent):
    """
    Production-ready agriculture assistant for Indian farmers.
    
    This assistant provides farming guidance in Hindi/English,
    handles natural voice conversations, and maintains context
    across multi-turn dialogues.
    
    Includes tools for:
    - Real-time weather data (Open-Meteo)
    - Live mandi prices (Indian agricultural markets)
    """
    
    def __init__(self, room_name: Optional[str] = None):
        """
        Initialize Kisan Mitra assistant with system prompt.
        
        The prompt is loaded from the prompts module,
        keeping the implementation clean and maintainable.
        
        Includes access to:
        - Farmer memory tools (lookup, save)
        - Weather service
        - Mandi price service
        
        Args:
            room_name: Optional room name to use as user_id for farmer memory
        """
        system_prompt = get_system_prompt()
        super().__init__(instructions=system_prompt)
        
        logger.info(f"{ASSISTANT_NAME} assistant initialized")
        self.weather_service = WeatherService()
        self.mandi_service = get_mandi_service()
        self.room_name = room_name  # Store for use in lookup_farmer
        
        # Initialize memory tools
        self.memory_tools = get_farmer_memory_tools()
        
        if room_name:
            logger.info(f"[Assistant] Room name set to: {room_name}")
    
    @function_tool
    async def get_weather(
        self,
        ctx: RunContext,
        latitude: float,
        longitude: float,
        language: str = "hi"
    ) -> str:
        """
        Get current weather and forecast data for a location.
        
        Args:
            latitude: Location latitude coordinate
            longitude: Location longitude coordinate
            language: Response language (hi for Hindi, en for English)
        
        Returns:
            Formatted weather information as string
        """
        try:
            logger.info(f"Fetching weather for ({latitude}, {longitude})")
            
            weather_data = await self.weather_service.get_weather(
                latitude=latitude,
                longitude=longitude,
                language=language
            )
            
            if not weather_data or not weather_data.get("current"):
                if language == "hi":
                    return "मुझे मौसम की जानकारी अभी नहीं मिल पाई। कृपया बाद में कोशिश करें।"
                else:
                    return "I couldn't fetch weather data right now. Please try again later."
            
            current = weather_data["current"]
            
            if language == "hi":
                response = (
                    f"आपके इलाके में अभी तापमान {current['temperature']}°C है। "
                    f"आसमान {current['weather']} है। "
                    f"नमी {current['humidity']}% है और हवा {current['wind_speed']} किमी/घंटा की रफ्तार से चल रही है। "
                )
                if current['rain'] > 0:
                    response += f"बारिश हो रही है।"
                elif current['precipitation'] > 0:
                    response += f"कुछ बारिश होने की संभावना है।"
                return response
            else:
                response = (
                    f"The current temperature in your area is {current['temperature']}°C. "
                    f"Weather is {current['weather']}. "
                    f"Humidity is {current['humidity']}% and wind speed is {current['wind_speed']} km/h. "
                )
                if current['rain'] > 0:
                    response += f"It is raining."
                elif current['precipitation'] > 0:
                    response += f"There is a chance of rain."
                return response
                
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            if language == "hi":
                return "मौसम की जानकारी लाने में समस्या आ रही है। कृपया बाद में कोशिश करें।"
            else:
                return "There was an error fetching weather. Please try again later."
    
    @function_tool
    async def get_mandi_prices(
        self,
        ctx: RunContext,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        language: str = "hi"
    ) -> str:
        """
        Get live mandi (market) prices for agricultural commodities.
        
        Args:
            commodity: Name of the crop/commodity (e.g., "गेहूँ", "धान", "प्याज़")
            state: State name (optional, for better accuracy)
            district: District name (optional)
            language: Response language (hi for Hindi, en for English)
        
        Returns:
            Formatted price information as string
        """
        try:
            logger.info(f"Fetching mandi prices for {commodity} in {state}")
            
            prices = await self.mandi_service.get_prices(
                commodity=commodity,
                state=state,
                district=district,
                limit=5
            )
            
            if not prices:
                if language == "hi":
                    return f"मुझे {commodity} के लिए बाज़ार की जानकारी नहीं मिल पाई। कृपया बाद में कोशिश करें।"
                else:
                    return f"I couldn't find market data for {commodity}. Please try again later."
            
            # Get most recent price
            latest = prices[0]
            
            if language == "hi":
                response = (
                    f"आज {latest['market']} मंडी में {latest['commodity']} का "
                    f"नवीनतम उपलब्ध भाव {latest['price']} {latest['unit']} है। "
                )
                return response
            else:
                response = (
                    f"Today in {latest['market']} market, the latest available price for {latest['commodity']} "
                    f"is {latest['price']} {latest['unit']}. "
                )
                return response
                
        except Exception as e:
            logger.error(f"Mandi prices tool error: {e}")
            if language == "hi":
                return "मंडी के भाव लाने में समस्या आ रही है। कृपया बाद में कोशिश करें।"
            else:
                return "There was an error fetching mandi prices. Please try again later."
    
    @function_tool
    async def lookup_farmer(
        self,
        ctx: RunContext,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Look up an existing farmer in the database.
        
        Use this to check if a caller is a returning customer
        and what information you already know about them.
        
        This MUST be called at the start of every conversation.
        
        Args:
            user_id: Unique identifier for the farmer (optional - extracted from room name if not provided)
            
        Returns:
            JSON string with farmer information if found,
            or indication that farmer is not in system
        """
        try:
            # Extract user_id from context if not provided
            if not user_id:
                # Use room name stored in assistant instance
                if self.room_name:
                    user_id = self.room_name
                    logger.info(f"[lookup_farmer] Using room_name from assistant: {user_id}")
                else:
                    logger.error("[lookup_farmer] No room_name available in assistant instance")
                    return str({
                        "status": "error",
                        "message": "Could not identify user"
                    })
            else:
                logger.info(f"[lookup_farmer] Using provided user_id: {user_id}")
            
            result = await self.memory_tools.lookup_farmer(ctx, user_id)
            logger.info(f"[lookup_farmer] Result for {user_id}: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Error in lookup_farmer: {e}")
            return str({
                "status": "error",
                "message": "Could not look up farmer information at this time"
            })
    
    @function_tool
    async def save_farmer_memory(
        self,
        ctx: RunContext,
        name: Optional[str] = None,
        language_preference: Optional[str] = None,
        crops_grown: Optional[str] = None,
        land_size: Optional[str] = None,
        district: Optional[str] = None,
        irrigation_type: Optional[str] = None,
    ) -> str:
        """
        Save or update farmer information in memory.
        
        IMPORTANT: Use this ONLY after explicit user consent.
        Never save information without asking permission first.
        
        Args:
            name: Farmer's name
            language_preference: Preferred language (hi/en)
            crops_grown: Crops the farmer grows
            land_size: Size of land/farm
            district: District or region
            irrigation_type: Type of irrigation system
            
        Returns:
            JSON string confirming save or error
        """
        try:
            # Use room name as user_id
            user_id = self.room_name
            if not user_id:
                logger.error("[save_farmer_memory] No room_name available")
                return str({
                    "status": "error",
                    "message": "Could not identify user"
                })
            
            logger.info(f"[save_farmer_memory] Saving data for user_id: {user_id}")
            return await self.memory_tools.save_farmer_memory(
                ctx=ctx,
                user_id=user_id,
                name=name,
                language_preference=language_preference,
                crops_grown=crops_grown,
                land_size=land_size,
                district=district,
                irrigation_type=irrigation_type,
            )
        except Exception as e:
            logger.error(f"Error in save_farmer_memory: {e}")
            return str({
                "status": "error",
                "message": "Could not save information due to an error"
            })
