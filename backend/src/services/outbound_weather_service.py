"""
Outbound Weather Alert Service for SIP calls via LiveKit.

Handles:
- Farmer lookup
- Weather data fetching
- Natural weather alert message generation
- Call initiation (via LiveKit SIP Trunk → Linphone)
- Call state tracking
"""

import logging
import uuid
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

from services.weather_service import WeatherService
from database.farmer_repository import get_farmer_repository
from livekit import api

logger = logging.getLogger("outbound_weather")


class CallStatus(str, Enum):
    """Call states."""
    INITIATED = "initiated"
    CONNECTING = "connecting"
    RINGING = "ringing"
    CONNECTED = "connected"
    SPEAKING = "speaking"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class OutboundWeatherAlertService:
    """
    Service for outbound weather alert calls via LiveKit SIP Trunk.

    Reuses existing weather service and farmer repository.
    Generates natural weather alert messages.
    Interfaces with LiveKit SIP trunk for call initiation via create_sip_participant.
    """

    def __init__(self):
        """Initialize the service."""
        self.weather_service = WeatherService()
        self.farmer_repo = get_farmer_repository()

        # LiveKit SIP Configuration
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
        self.linphone_sip_uri = os.getenv("LINPHONE_SIP_URI")

        # Feature flag
        self.enabled = os.getenv("OUTBOUND_CALL_ENABLED", "false").lower() == "true"

        # Demo configuration
        self.demo_district = os.getenv("WEATHER_ALERT_DEMO_DISTRICT", "Varanasi")
        self.call_timeout = int(os.getenv("WEATHER_ALERT_CALL_TIMEOUT", "60"))

        # Call tracking
        self.active_calls: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Outbound Weather Alert Service initialized (enabled={self.enabled})")

    def is_enabled(self) -> bool:
        """Check if outbound calling is enabled and configured."""
        if not self.enabled:
            return False

        if not all([self.livekit_url, self.livekit_api_key, self.livekit_api_secret,
                    self.sip_trunk_id, self.linphone_sip_uri]):
            logger.warning("Missing SIP/LiveKit configuration")
            return False

        return True

    async def initiate_demo_weather_alert(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate a demo weather alert call to the configured Linphone SIP URI.

        Flow:
          1. Validate config / feature flag
          2. Check if user has opted out of calls
          3. Look up user profile for personalization
          4. Fetch weather for demo district
          5. Generate personalized Hindi weather alert message with opt-out info
          6. Create a LiveKit room for the call
          7. Call livekit_api.sip.create_sip_participant() → SIP INVITE is sent
             to the Linphone app via the configured trunk
          8. Voice agent (agent.py) auto-joins the room and speaks the alert
          9. Return call_id + status + weather to the caller

        Args:
            user_id: Optional farmer user ID. If not provided, uses demo profile.

        Returns:
            Response dict with call_id, status, weather, and room_name
        """
        try:
            logger.info("[OutboundWeather] Initiating demo weather alert call")

            # ── 1. Check if enabled ──────────────────────────────────────────
            if not self.is_enabled():
                logger.error("[OutboundWeather] Service not configured")
                return {
                    "success": False,
                    "error": "DISABLED",
                    "message": "Outbound weather alert calling is not configured.",
                }

            # ── 2. Check opt-out status ──────────────────────────────────────
            if user_id:
                if not self.farmer_repo.can_receive_outbound_calls(user_id):
                    logger.info(f"[OutboundWeather] User {user_id} has opted out of calls")
                    return {
                        "success": False,
                        "error": "OPTED_OUT",
                        "message": "User has disabled outbound calls.",
                    }

            # ── 3. Look up user profile ──────────────────────────────────────
            farmer_profile = None
            farmer_name = "Farmer"  # Default fallback
            language = "hi"  # Default language
            
            if user_id:
                try:
                    farmer_profile = self.farmer_repo.lookup_farmer(user_id)
                    if farmer_profile:
                        farmer_name = farmer_profile.name or "Farmer"
                        language = farmer_profile.language_preference or "hi"
                        logger.info(f"[OutboundWeather] Found farmer: {farmer_name}")
                    else:
                        logger.info(f"[OutboundWeather] User {user_id} not found, using defaults")
                except Exception as e:
                    logger.warning(f"[OutboundWeather] Could not lookup farmer {user_id}: {e}")

            # ── 4. Fetch weather ─────────────────────────────────────────────
            district = self.demo_district
            logger.info(f"[OutboundWeather] Fetching weather for {district}")
            weather_data = await self._fetch_weather_for_district(district)

            if not weather_data:
                logger.error(f"[OutboundWeather] Weather unavailable for {district}")
                return {
                    "success": False,
                    "error": "WEATHER_UNAVAILABLE",
                    "message": "Could not fetch weather data. Please try again.",
                }

            # ── 5. Generate personalized alert message ───────────────────────
            logger.info(f"[OutboundWeather] Generating message with farmer_name='{farmer_name}', language='{language}'")
            alert_message = self._generate_weather_alert_message(
                farmer_name=farmer_name,
                district=district,
                weather=weather_data,
                language=language,
                include_opt_out_info=True,  # Always include opt-out instructions
            )
            logger.info(f"[OutboundWeather] Generated alert message (length={len(alert_message)}): {alert_message[:100]}...")

            # ── 4. Build identifiers ─────────────────────────────────────────
            call_id = f"weather-alert-{uuid.uuid4()}"
            room_name = f"outbound-{call_id}"

            logger.info(f"[OutboundWeather] call_id={call_id}, room={room_name}")

            # ── 5. LiveKit API client ────────────────────────────────────────
            lk_api = api.LiveKitAPI(
                url=self.livekit_url,
                api_key=self.livekit_api_key,
                api_secret=self.livekit_api_secret,
            )

            try:
                # ── 5a. Create the LiveKit room ──────────────────────────────
                room = await lk_api.room.create_room(
                    api.CreateRoomRequest(
                        name=room_name,
                        empty_timeout=120,   # auto-delete if empty for 2 min
                        max_participants=5,
                        metadata=alert_message,  # Store weather alert in room metadata
                    )
                )
                logger.info(
                    f"[OutboundWeather] LiveKit room created: "
                    f"{room.name} (sid={room.sid})"
                )
                
                # ── 5b. Create explicit agent dispatch ───────────────────────
                # This tells LiveKit to send our registered agent to this room
                try:
                    dispatch = await lk_api.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(
                            room=room_name,
                            agent_name="my-agent",  # Must match AGENT_NAME in agent.py
                        )
                    )
                    logger.info(f"[OutboundWeather] Agent dispatch created: {dispatch.id}")
                except AttributeError:
                    # agent_dispatch might not be available in all SDK versions
                    # Fall back to using room participants as trigger
                    logger.warning("[OutboundWeather] Agent dispatch API not available, agent may not auto-join")
                except Exception as dispatch_err:
                    logger.error(f"[OutboundWeather] Agent dispatch failed: {dispatch_err}")
                # ── 5c. Dispatch SIP outbound call → rings Linphone ──────────
                #
                # create_sip_participant sends a SIP INVITE from the trunk
                # (ST_JYme7d2hXeNp → sip.linphone.org) to LINPHONE_SIP_URI.
                # LiveKit bridges the answered call as a participant in room_name.
                # The voice agent watching for new rooms will auto-join and speak.
                #
                logger.info(
                    f"[OutboundWeather] Dispatching SIP call to "
                    f"{self._mask_uri(self.linphone_sip_uri)} "
                    f"via trunk {self.sip_trunk_id}"
                )
                
                # LiveKit expects just the SIP username, not the full URI
                # Extract username from "dpp@sip.linphone.org" → "dpp"
                sip_call_to = self.linphone_sip_uri.split("@")[0] if "@" in self.linphone_sip_uri else self.linphone_sip_uri
                logger.info(f"[OutboundWeather] Calling SIP user: {sip_call_to}")

                sip_participant = await lk_api.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=self.sip_trunk_id,
                        sip_call_to=sip_call_to,                    # Just username: "dpp"
                        room_name=room_name,
                        participant_identity=f"farmer-{call_id[:8]}",
                        participant_name="Kisan Mitra Weather Alert",
                        participant_metadata=alert_message,
                        # Tell LiveKit to dispatch the agent to this room
                        # This ensures the voice agent joins and speaks the alert
                        # The agent name must match what's registered (AGENT_NAME in config)
                        # Note: This may not be available in all LiveKit versions
                        # Alternative: Set room attributes to auto-dispatch
                    )
                )
                logger.info(
                    f"[OutboundWeather] SIP participant dispatched: "
                    f"identity={sip_participant.participant_identity}"
                )

            except Exception as dispatch_err:
                logger.error(
                    f"[OutboundWeather] Dispatch failed: {dispatch_err}", exc_info=True
                )
                # Attempt cleanup of the dangling room
                try:
                    await lk_api.room.delete_room(
                        api.DeleteRoomRequest(room=room_name)
                    )
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": "SIP_DISPATCH_FAILED",
                    "message": f"Could not initiate SIP call: {dispatch_err}",
                }
            finally:
                await lk_api.aclose()

            # ── 6. Track the call in memory ──────────────────────────────────
            self.active_calls[call_id] = {
                "call_id": call_id,
                "user_id": user_id or "demo",
                "district": district,
                "weather": weather_data,
                "message": alert_message,
                "status": CallStatus.RINGING,    # SIP INVITE sent → Linphone ringing
                "room_name": room_name,
                "sip_participant_identity": sip_participant.participant_identity,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "destination": self.linphone_sip_uri,
            }

            logger.info(
                f"[OutboundWeather] ✅ Call dispatched → call_id={call_id} "
                f"room={room_name} dest={self._mask_uri(self.linphone_sip_uri)}"
            )

            return {
                "success": True,
                "call_id": call_id,
                "status": CallStatus.RINGING.value,
                "message": alert_message,
                "weather": weather_data,
                "room_name": room_name,
            }

        except Exception as e:
            logger.error(f"[OutboundWeather] Unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "An error occurred while preparing the weather alert.",
            }

    async def _fetch_weather_for_district(self, district: str) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a district.

        Uses hardcoded coordinates for major Indian districts.
        In production, would use a geocoding service.

        Args:
            district: District name

        Returns:
            Weather dict or None if unavailable
        """
        try:
            # Hardcoded coordinates for demo districts
            coordinates = {
                "varanasi": (25.3176, 82.9739),
                "lucknow": (26.8467, 80.9462),
                "delhi": (28.7041, 77.1025),
                "mumbai": (19.0760, 72.8777),
                "bangalore": (12.9716, 77.5946),
                "chennai": (13.0827, 80.2707),
                "kolkata": (22.5726, 88.3639),
                "hyderabad": (17.3850, 78.4867),
                "pune": (18.5204, 73.8567),
                "jaipur": (26.9124, 75.7873),
                "agra": (27.1767, 78.0081),
                "indore": (22.7196, 75.8577),
                "ahmedabad": (23.0225, 72.5714),
                "chandigarh": (30.7333, 76.7794),
                "amritsar": (31.6340, 74.8711),
            }

            district_lower = district.lower()
            if district_lower not in coordinates:
                logger.warning(f"[OutboundWeather] No coordinates for {district}, using Varanasi")
                district_lower = "varanasi"

            lat, lon = coordinates[district_lower]

            # Fetch weather (existing service reused)
            weather = await self.weather_service.get_weather(lat, lon, "hi")

            if weather and weather.get("current"):
                return {
                    "district": district,
                    "temperature": weather["current"]["temperature"],
                    "condition": weather["current"]["weather"],
                    "humidity": weather["current"]["humidity"],
                    "wind_speed": weather["current"]["wind_speed"],
                    "precipitation": weather["current"]["precipitation"],
                    "rain": weather["current"]["rain"],
                }

            return None

        except Exception as e:
            logger.error(f"[OutboundWeather] Weather fetch error: {e}")
            return None

    def _generate_weather_alert_message(
        self,
        farmer_name: str,
        district: str,
        weather: Dict[str, Any],
        language: str = "hi",
        include_opt_out_info: bool = True,
    ) -> str:
        """
        Generate a natural, concise weather alert message with opt-out instructions.

        Args:
            farmer_name: Name of the farmer
            district: District name
            weather: Weather data dict
            language: Language (hi/en)
            include_opt_out_info: Whether to include opt-out instructions

        Returns:
            Natural weather alert message suitable for TTS, with speech optimization
        """
        temp = weather.get("temperature", 0)
        condition = weather.get("condition", "Unknown")
        rain_prob = weather.get("precipitation", 0)
        
        # Import Hindi speech normalization
        try:
            from utils.hindi_speech import optimize_for_murf_tts
        except ImportError:
            from .utils.hindi_speech import optimize_for_murf_tts

        if language == "hi":
            # Generate personalized greeting
            if farmer_name and farmer_name != "Farmer":
                greeting = f"नमस्ते {farmer_name} जी! किसान मित्र बोल रहा हूँ।"
            else:
                greeting = "नमस्ते! किसान मित्र बोल रहा हूँ।"
            
            # Explain purpose
            purpose = f"आपके इलाके {district} के मौसम की जरूरी जानकारी देने के लिए मैंने आपको कॉल किया है।"
            
            # Generate weather alert with natural numbers
            if rain_prob > 70:
                if rain_prob == 70:
                    rain_text = "सत्तर प्रतिशत"
                elif rain_prob == 80:
                    rain_text = "अस्सी प्रतिशत"
                elif rain_prob == 90:
                    rain_text = "नब्बे प्रतिशत"
                else:
                    rain_text = f"{rain_prob} प्रतिशत"
                    
                alert = (
                    f"आज {rain_text} बारिश की संभावना है। "
                    f"अगर खेत में कटाई का काम चल रहा है, तो उसे जल्द पूरा कर लें।"
                )
            elif rain_prob > 40:
                if rain_prob == 50:
                    rain_text = "पचास प्रतिशत"
                elif rain_prob == 60:
                    rain_text = "साठ प्रतिशत"
                else:
                    rain_text = f"{rain_prob} प्रतिशत"
                    
                alert = (
                    f"आज {rain_text} बारिश की संभावना है। "
                    f"अपनी योजना के अनुसार काम करें।"
                )
            elif temp > 38:
                if temp == 40:
                    temp_text = "चालीस डिग्री"
                elif temp == 42:
                    temp_text = "बयालीस डिग्री" 
                elif temp == 45:
                    temp_text = "पैंतालीस डिग्री"
                else:
                    temp_text = f"{temp} डिग्री"
                    
                alert = (
                    f"आज तापमान {temp_text} तक जा सकता है। "
                    f"खेत में काम करते समय पानी पिएं और धूप से बचें।"
                )
            elif temp < 5:
                alert = (
                    f"आज तापमान बहुत कम रहेगा। "
                    f"संवेदनशील फसलों का ध्यान रखें।"
                )
            else:
                if temp == 25:
                    temp_text = "पच्चीस डिग्री"
                elif temp == 30:
                    temp_text = "तीस डिग्री"
                elif temp == 32:
                    temp_text = "बत्तीस डिग्री"
                elif temp == 35:
                    temp_text = "पैंतीस डिग्री"
                else:
                    temp_text = f"{temp} डिग्री"
                    
                alert = (
                    f"आज तापमान लगभग {temp_text} रहेगा। "
                    f"खेत का काम सामान्य तरीके से करें।"
                )
            
            # Add opt-out instructions if requested
            opt_out_info = ""
            if include_opt_out_info:
                opt_out_info = (
                    "अगर आप ऐसे कॉल आगे नहीं चाहते, तो बस कह दीजिए 'कॉल बंद कर दो', "
                    "और मैं आपको आगे ऐसे कॉल नहीं करूंगा।"
                )
            
            # Combine message
            parts = [greeting, purpose, alert]
            if opt_out_info:
                parts.append(opt_out_info)
            parts.append("धन्यवाद।")
            
            message = " ".join(parts)
            
        else:
            # English version
            if farmer_name and farmer_name != "Farmer":
                greeting = f"Hello {farmer_name}! This is Kisan Mitra calling."
            else:
                greeting = "Hello! This is Kisan Mitra calling."
                
            purpose = f"I'm calling to share important weather information for {district}."
            
            if rain_prob > 70:
                alert = (
                    f"There is a {rain_prob}% chance of rain today. "
                    f"If you have harvesting work, try to complete it quickly."
                )
            elif rain_prob > 40:
                alert = (
                    f"There might be some rain today, around {rain_prob}% probability. "
                    f"Plan your work accordingly."
                )
            elif temp > 38:
                alert = (
                    f"Temperature may reach {temp}°C today. "
                    f"Stay hydrated and avoid prolonged sun exposure."
                )
            elif temp < 5:
                alert = (
                    f"Temperature may drop to {temp}°C. "
                    f"Take care of sensitive crops."
                )
            else:
                alert = (
                    f"Today's temperature will be around {temp}°C. "
                    f"Continue your normal farm work."
                )
            
            opt_out_info = ""
            if include_opt_out_info:
                opt_out_info = (
                    "If you don't want to receive such calls in future, just say 'stop these calls', "
                    "and I won't call you again."
                )
            
            parts = [greeting, purpose, alert]
            if opt_out_info:
                parts.append(opt_out_info)
            parts.append("Thank you.")
            
            message = " ".join(parts)
        
        # Apply speech normalization for Hindi
        if language == "hi":
            message = optimize_for_murf_tts(message)
        
        return message

    def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a call."""
        call = self.active_calls.get(call_id)
        if not call:
            return None

        return {
            "call_id": call_id,
            "status": call["status"].value,
            "created_at": call["created_at"],
        }

    def update_call_status(self, call_id: str, status: CallStatus):
        """Update call status."""
        if call_id in self.active_calls:
            self.active_calls[call_id]["status"] = status
            logger.info(f"[OutboundWeather] Call {call_id} status: {status.value}")

    def _mask_uri(self, uri: str) -> str:
        """Mask SIP URI for logging."""
        if not uri or "@" not in uri:
            return "***"
        parts = uri.split("@")
        username = parts[0]
        if len(username) > 2:
            username = f"{username[0]}***{username[-1]}"
        return f"{username}@{parts[1]}"


# Global service instance
_service_instance: Optional[OutboundWeatherAlertService] = None


def get_outbound_weather_service() -> OutboundWeatherAlertService:
    """Get or create the global outbound weather service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = OutboundWeatherAlertService()
    return _service_instance
