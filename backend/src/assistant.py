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
    
    def __init__(self):
        """
        Initialize Kisan Mitra assistant with system prompt.
        
        The prompt is loaded from the prompts module,
        keeping the implementation clean and maintainable.
        
        Includes access to:
        - Farmer memory tools (lookup, save)
        - Weather service
        - Mandi price service
        """
        system_prompt = get_system_prompt()
        super().__init__(instructions=system_prompt)
        
        logger.info(f"{ASSISTANT_NAME} assistant initialized")
        self.weather_service = WeatherService()
        self.mandi_service = get_mandi_service()
        
        # Initialize memory tools and register them as agent methods
        self.memory_tools = get_farmer_memory_tools()
        
        # Register memory tools as function tools on this agent
        self.lookup_farmer = self.memory_tools.lookup_farmer
        self.save_farmer_memory = self.memory_tools.save_farmer_memory
    
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
