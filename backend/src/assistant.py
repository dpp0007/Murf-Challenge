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
    from .tools.escalation_tools import get_escalation_tools
except ImportError:
    from prompts import get_system_prompt
    from config import ASSISTANT_NAME
    from services.weather_service import WeatherService
    from services.mandi_service import get_mandi_service
    from tools.farmer_memory import get_farmer_memory_tools
    from tools.escalation_tools import get_escalation_tools

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
        
        # Detect call type from room name
        self.room_name = room_name
        self.is_outbound_call = room_name and room_name.startswith("outbound-")
        self.is_escalation_callback = room_name and room_name.startswith("outbound-escalation-callback-")
        self.is_weather_alert = room_name and room_name.startswith("outbound-weather-alert-")
        
        # For outbound weather alert calls, add a special instruction
        if self.is_weather_alert:
            logger.info(f"[Assistant] Detected outbound weather alert call: {room_name}")
            system_prompt = (
                "🌦️ OUTBOUND WEATHER ALERT CALL MODE 🌦️\n\n"
                "This is an automated outbound weather alert call.\n"
                "The weather alert message has already been spoken by the agent.\n"
                "Your job is to:\n"
                "1. Wait for the user's response\n"
                "2. Answer any follow-up questions about the weather\n"
                "3. Handle opt-out requests if the user says they don't want future calls\n"
                "4. Keep the conversation short and natural\n\n"
                "DO NOT call lookup_farmer() - the personalization is already done.\n"
                "DO NOT generate a new greeting - just wait for user input.\n\n"
                "After this instruction, here is the full system prompt:\n\n"
            ) + system_prompt
        
        # For escalation callbacks, add different instructions
        elif self.is_escalation_callback:
            logger.info(f"[Assistant] Detected escalation callback call: {room_name}")
            system_prompt = (
                "📞 ESCALATION RESOLUTION CALLBACK MODE 📞\n\n"
                "This is an automatic callback about a resolved escalation.\n"
                "The farmer had asked for help, and an agricultural adviser has provided an answer.\n"
                "Your job is to:\n"
                "1. Greet the farmer warmly by name\n"
                "2. Briefly explain this is a callback about their escalated problem\n"
                "3. Repeat their original question naturally\n"
                "4. Provide the adviser's answer without hallucinating\n"
                "5. Offer to explain further if needed\n"
                "6. Keep the tone warm and conversational\n\n"
                "IMPORTANT:\n"
                "- DO NOT call lookup_farmer() - context is provided in room metadata\n"
                "- DO NOT generate a new greeting - use the context provided\n"
                "- DO NOT invent agricultural recommendations - only repeat the adviser's answer\n"
                "- Use the farmer's language preference (hindi or english)\n\n"
                "The farmer context will be in the room metadata.\n\n"
                "After this instruction, here is the full system prompt:\n\n"
            ) + system_prompt
        
        super().__init__(instructions=system_prompt)
        
        logger.info(f"{ASSISTANT_NAME} assistant initialized")
        self.weather_service = WeatherService()
        self.mandi_service = get_mandi_service()
        
        # Initialize memory tools and escalation tools
        self.memory_tools = get_farmer_memory_tools()
        self.escalation_tools = get_escalation_tools()
        
        if room_name:
            logger.info(f"[Assistant] Room name set to: {room_name}")
            if self.is_escalation_callback:
                logger.info(f"[Assistant] This is an ESCALATION CALLBACK")
            elif self.is_weather_alert:
                logger.info(f"[Assistant] This is an OUTBOUND weather alert call")
    
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
            
            # Check if no prices returned
            if not prices or len(prices) == 0:
                if language == "hi":
                    return f"मुझे {commodity} के लिए मंडी की जानकारी अभी नहीं मिल पाई। कृपया बाद में कोशिश करें या अपने नजदीकी मंडी से संपर्क करें।"
                else:
                    return f"I couldn't access market data for {commodity} right now. Please try again later or contact your local mandi."
            
            # Get most recent price
            latest = prices[0]
            price_value = latest.get('price', 0)
            
            # Check if price is 0 or invalid - means data is unavailable
            if price_value == 0 or price_value is None:
                logger.warning(f"Mandi price returned 0 or None for {commodity}")
                if language == "hi":
                    return (
                        f"मुझे {commodity} का सही मंडी भाव अभी नहीं मिल पा रहा है। "
                        f"यह हो सकता है कि इस फसल का डेटा उपलब्ध नहीं है या API काम नहीं कर रहा है। "
                        f"कृपया अपने नजदीकी मंडी से संपर्क करके सही भाव पता करें।"
                    )
                else:
                    return (
                        f"I couldn't get accurate mandi prices for {commodity} right now. "
                        f"The data may not be available or the API might be down. "
                        f"Please contact your local mandi to get current prices."
                    )
            
            # Valid price found - return formatted response
            market = latest.get('market', 'Unknown')
            unit = latest.get('unit', 'प्रति क्विंटल')
            
            if language == "hi":
                response = (
                    f"आज {market} मंडी में {latest['commodity']} का "
                    f"नवीनतम उपलब्ध भाव {price_value} रुपये {unit} है। "
                )
                return response
            else:
                response = (
                    f"Today in {market} market, the latest available price for {latest['commodity']} "
                    f"is ₹{price_value} {unit}. "
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
        outbound_calls_enabled: Optional[bool] = None,
        crops_grown: Optional[str] = None,
        land_size: Optional[str] = None,
        district: Optional[str] = None,
        irrigation_type: Optional[str] = None,
    ) -> str:
        """
        Save or update farmer information in memory.
        
        IMPORTANT: Use this ONLY after explicit user consent.
        Never save information without asking permission first.
        
        Special case: For outbound_calls_enabled=False (opt-out),
        you can save immediately when user requests it - no consent needed.
        
        Args:
            name: Farmer's name
            language_preference: Preferred language (hi/en)
            outbound_calls_enabled: Whether to allow outbound calls (True/False)
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
                outbound_calls_enabled=outbound_calls_enabled,
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
    
    @function_tool
    async def create_escalation(
        self,
        ctx: RunContext,
        reason: str,
        summary: str,
        original_question: str,
        what_agent_checked: str,
        urgency: str = "MEDIUM",
        preferred_followup: str = "phone",
    ) -> str:
        """
        Create an escalation request for human adviser review.
        
        IMPORTANT: This tool should ONLY be called after:
        1. Agent determined human help is needed
        2. Agent asked farmer for permission
        3. Farmer gave explicit permission (हाँ, Yes, ठीक है, etc.)
        
        Do NOT call this tool if farmer declined.
        
        Args:
            reason: Escalation reason - must be one of:
                - SERIOUS_CROP_PROBLEM
                - MARKET_DATA_UNAVAILABLE
                - UNCERTAIN_DIAGNOSIS
                - OTHER
            summary: Brief summary of the issue (max 500 chars)
            original_question: The farmer's original question
            what_agent_checked: What the agent verified before escalating
            urgency: LOW, MEDIUM, HIGH (default: MEDIUM)
            preferred_followup: phone, whatsapp, etc. (default: phone)
        
        Returns:
            JSON string with escalation reference ID and status
        """
        try:
            user_id = self.room_name
            if not user_id:
                logger.error("[create_escalation] No room_name available in assistant")
                return str({
                    "status": "error",
                    "message": "Could not identify user"
                })
            
            logger.info(f"[create_escalation] Creating escalation for user_id: {user_id}, reason: {reason}")
            
            # Directly create escalation without going through escalation_tools class
            from services.escalation_service import get_escalation_service, EscalationReason
            from services.discord_service import get_discord_service
            import asyncio
            
            escalation_service = get_escalation_service()
            discord_service = get_discord_service()
            
            # Validate reason
            valid_reasons = [e.value for e in EscalationReason]
            if reason not in valid_reasons:
                logger.warning(f"[create_escalation] Invalid reason: {reason}")
                return str({
                    "status": "error",
                    "message": f"Invalid reason. Must be one of: {', '.join(valid_reasons)}"
                })
            
            # Create escalation
            escalation = escalation_service.create_escalation(
                user_id=user_id,
                reason=EscalationReason(reason),
                original_question=original_question,
                summary=summary,
                what_agent_checked=what_agent_checked,
                urgency=urgency,
                preferred_followup=preferred_followup,
            )
            
            if not escalation:
                logger.error(f"[create_escalation] Failed to create escalation for {user_id}")
                return str({
                    "status": "error",
                    "message": "Could not create escalation"
                })
            
            logger.info(f"[create_escalation] SUCCESS: Created escalation {escalation.reference_id} for user {user_id}")
            
            # Send Discord notification asynchronously
            try:
                logger.info(f"[create_escalation] Sending Discord notification for {escalation.reference_id}")
                asyncio.create_task(discord_service.send_escalation_notification(escalation))
            except Exception as e:
                logger.warning(f"[create_escalation] Could not send Discord notification: {e}")
            
            return str({
                "status": "success",
                "reference_id": escalation.reference_id,
                "message": "आपकी समस्या कृषि सलाहकार के पास भेज दी गई है। वे जल्द ही आपसे संपर्क करेंगे।"
            })
            
        except Exception as e:
            logger.error(f"[create_escalation] Error: {e}", exc_info=True)
            return str({
                "status": "error",
                "message": "Server error creating escalation"
            })
