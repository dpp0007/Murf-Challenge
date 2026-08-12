"""
Kisan Mitra - Production Voice Agent for Indian Farmers
Refactored for Murf VoiceForBharat Challenge Day 2

This module orchestrates the voice pipeline, handles latency tracking,
silence detection, and response post-processing for optimal voice UX.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src directory to path to allow running: python src/agent.py dev
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import configuration and utilities - use absolute imports for direct execution
try:
    # Try relative import first (when run as module)
    from .config import (
        AGENT_NAME,
        TTS_VOICE,
        TTS_STYLE,
        TTS_TEXT_PACING,
        STT_MODEL,
        STT_LANGUAGE,
        LLM_MODEL,
        MIN_SENTENCE_LENGTH,
        ENABLE_LATENCY_LOGGING,
        SILENCE_TIMEOUT,
        MAX_SILENCE_RETRIES,
        GREETING_MESSAGE,
        SILENCE_REPROMPT_1,
        SILENCE_REPROMPT_2,
    )
    from .assistant import KisanMitraAssistant
    from .utils.response_processor import clean_response_for_voice
    from .utils.latency_tracker import LatencyTracker
    from .utils.silence_handler import ImprovedSilenceHandler
    from .database.db import get_database  # Initialize database on startup
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config import (
        AGENT_NAME,
        TTS_VOICE,
        TTS_STYLE,
        TTS_TEXT_PACING,
        STT_MODEL,
        STT_LANGUAGE,
        LLM_MODEL,
        MIN_SENTENCE_LENGTH,
        ENABLE_LATENCY_LOGGING,
        SILENCE_TIMEOUT,
        MAX_SILENCE_RETRIES,
        GREETING_MESSAGE,
        SILENCE_REPROMPT_1,
        SILENCE_REPROMPT_2,
    )
    from assistant import KisanMitraAssistant
    from utils.response_processor import clean_response_for_voice
    from utils.latency_tracker import LatencyTracker
    from utils.silence_handler import ImprovedSilenceHandler
    from database.db import get_database  # Initialize database on startup

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Initialize agent server
server = AgentServer()


def prewarm(proc: JobProcess):
    """
    Prewarm function to initialize models before session starts.
    This improves first-response latency and ensures database is ready.
    """
    # Initialize database before anything else
    db = get_database()
    logger.info("[OK] Database initialized during prewarm")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("[OK] VAD model preloaded")
    
    # Initialize Discord bot in background (for escalations)
    try:
        from services.discord_service import get_discord_service
        discord_svc = get_discord_service()
        if discord_svc.enabled:
            logger.info("[Discord] Initializing Discord bot during prewarm")
            if discord_svc.initialize_bot():
                logger.info("[Discord] Bot initialized and starting in background")
            else:
                logger.warning("[Discord] Bot initialization failed during prewarm")
        else:
            logger.debug("[Discord] Discord service not configured")
    except Exception as e:
        logger.error(f"[Discord] Failed to initialize Discord during prewarm: {e}", exc_info=True)


server.setup_fnc = prewarm


@server.rtc_session(agent_name=AGENT_NAME)
async def kisan_mitra_session(ctx: JobContext):
    """
    Main session handler for Kisan Mitra voice agent.
    
    Orchestrates:
    - Voice pipeline (STT -> LLM -> TTS)
    - Detailed latency tracking per pipeline stage
    - Event-driven silence detection
    - Response post-processing
    - Farmer memory management
    - Session lifecycle
    """
    # Setup logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": AGENT_NAME,
    }
    
    logger.info(f"Starting Kisan Mitra session for room: {ctx.room.name}")
    
    # Extract stable user_id from room name or participant ID
    # Format: voice_assistant_user_<random> from frontend token generation
    user_id = ctx.room.name  # This is stable per caller session
    logger.info(f"Farmer user_id: {user_id}")
    
    # Initialize latency tracker for detailed pipeline metrics
    latency_tracker = LatencyTracker()
    
    # Configure voice AI pipeline
    session = AgentSession(
        # Speech-to-Text: Converts user voice to text
        stt=deepgram.STT(
            model=STT_MODEL,
            language=STT_LANGUAGE  # Hindi language support
        ),
        
        # Large Language Model: Processes and generates responses
        llm=google.LLM(
            model=LLM_MODEL,
        ),
        
        # Text-to-Speech: Converts responses to natural voice
        tts=murf.TTS(
            voice=TTS_VOICE,  # Anisha - Natural Hindi female voice
            style=TTS_STYLE,
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=MIN_SENTENCE_LENGTH),
            text_pacing=TTS_TEXT_PACING
        ),
        
        # Voice Activity Detection and turn management
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        
        # Enable preemptive generation for lower latency
        preemptive_generation=True,
    )
    
    # ========== EVENT-DRIVEN SILENCE HANDLER ==========
    
    async def handle_silence(retry_count: int):
        """
        Handle silence detection with configured messages.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
        """
        try:
            if retry_count == 0:
                # First silence - send configured reminder
                await session.say(SILENCE_REPROMPT_1, allow_interruptions=True)
            elif retry_count == 1:
                # Second silence - send configured goodbye
                await session.say(SILENCE_REPROMPT_2, allow_interruptions=False)
                await asyncio.sleep(2)  # Wait for message to complete
        except Exception as e:
            logger.error(f"Failed to handle silence: {e}")
    
    # Initialize event-driven silence handler
    silence_handler = ImprovedSilenceHandler(
        timeout=SILENCE_TIMEOUT,
        max_retries=MAX_SILENCE_RETRIES,
        reprompt_callback=handle_silence
    )
    
    # ========== LATENCY TRACKING EVENTS ==========
    
    @session.on("user_speech_committed")
    def on_user_speech_end(msg):
        """
        Track when user finishes speaking.
        Reset silence timer immediately (event-driven).
        """
        # Mark latency checkpoint
        latency_tracker.mark_user_speech_end()
        
        # Stop silence monitoring when user speaks
        silence_handler.stop()
        logger.debug("[User] User speaking - silence monitoring stopped")
        
        if ENABLE_LATENCY_LOGGING:
            logger.debug("User speech committed - latency tracking started")
    
    @session.on("agent_started_speaking")
    def on_agent_speaking():
        """
        Track when agent starts speaking.
        Calculate and log detailed pipeline metrics.
        """
        # Mark final latency checkpoint
        latency_tracker.mark_first_audio_out()
        
        # Stop silence monitoring while agent speaks
        silence_handler.stop()
        logger.debug("[Agent] Agent speaking - silence monitoring stopped")
        
        # Log detailed pipeline metrics
        if ENABLE_LATENCY_LOGGING:
            latency_tracker.log_metrics()
    
    @session.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        """
        Called when agent finishes speaking.
        Start silence monitoring to detect if user doesn't respond.
        """
        # Start monitoring for silence after agent finishes speaking
        silence_handler.start()
        logger.info("[Agent] Agent stopped speaking - silence monitoring started")
        
        # Reset for next turn
        latency_tracker.reset()
    
    # ========== RESPONSE POST-PROCESSING ==========
    
    @session.on("agent_response")
    def on_agent_response(response):
        """
        Post-process LLM responses to optimize for voice output.
        Removes markdown, formatting, emojis, etc.
        """
        if hasattr(response, 'text'):
            original = response.text
            cleaned = clean_response_for_voice(original)
            
            if original != cleaned:
                response.text = cleaned
                logger.debug(f"Response cleaned for voice: {len(original)} -> {len(cleaned)} chars")
        
        # Mark LLM completion for latency tracking
        latency_tracker.mark_llm_complete()
    
    # ========== START SESSION ==========
    
    logger.info("Initializing Kisan Mitra assistant...")
    
    await session.start(
        agent=KisanMitraAssistant(room_name=ctx.room.name),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Apply noise cancellation for better audio quality
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )
    
    logger.info("Kisan Mitra session started successfully")
    
    # Connect to the room and begin interaction
    await ctx.connect()
    
    logger.info(f"Kisan Mitra connected to room: {ctx.room.name}")
    
    # ========== OUTBOUND CALL DETECTION ==========
    # For outbound weather alert calls, the room name contains "weather-alert"
    # For escalation callbacks, the room name contains "escalation-callback"
    is_weather_alert_call = "weather-alert" in ctx.room.name
    is_escalation_callback = "escalation-callback" in ctx.room.name
    is_outbound_call = is_weather_alert_call or is_escalation_callback
    
    logger.info(f"Call type: {'OUTBOUND-WEATHER' if is_weather_alert_call else 'OUTBOUND-ESCALATION' if is_escalation_callback else 'INBOUND'}")
    logger.info(f"Room metadata present: {bool(ctx.room.metadata)}")
    
    # For outbound calls, speak the message from room metadata immediately
    if is_outbound_call and ctx.room.metadata:
        logger.info(f"Outbound call detected - preparing callback message")
        
        message = ctx.room.metadata.strip()
        
        # VALIDATION: Check if metadata is valid callback message
        # Metadata should be natural Hindi/English text, NOT a Python dict string
        if message.startswith("{'") or message.startswith('{'):
            logger.error(f"[ERROR] Room metadata is a Python dict, not a natural message!")
            logger.error(f"[ERROR] Metadata: {message[:100]}...")
            # Use fallback instead of sending dict to farmer
            if is_escalation_callback:
                logger.error(f"[OutboundEscalation] Adviser's answer was not properly formatted in metadata")
            message = None
        
        if message:
            # IMPROVED PARSING: Split message into greeting + content more robustly
            # Look for first sentence separator (! or ।)
            greeting_end = -1
            for i, char in enumerate(message):
                if char in ('!', '।', '?', '.'):  # Better delimiters
                    if i < len(message) * 0.25:  # Greeting should be <25% of total
                        greeting_end = i + 1
                        break
            
            if greeting_end > 0:
                greeting = message[:greeting_end].strip()
                content = message[greeting_end:].strip()
                
                if is_escalation_callback:
                    logger.info(f"[OutboundEscalation] Speaking greeting: {greeting[:60]}...")
                    logger.info(f"[OutboundEscalation] Speaking adviser answer: {content[:60]}...")
                else:
                    logger.info(f"[OutboundWeather] Speaking greeting: {greeting[:60]}...")
                    logger.info(f"[OutboundWeather] Speaking content: {content[:60]}...")
                
                try:
                    await session.say(greeting, allow_interruptions=True)
                    await asyncio.sleep(1)  # Small delay for call stability
                    
                    if content:
                        await session.say(content, allow_interruptions=True)
                    else:
                        logger.warning(f"[Outbound] No content after greeting")
                except Exception as e:
                    logger.error(f"[Outbound] Failed to speak parsed message: {e}")
            else:
                # Fallback: speak entire message if can't parse
                logger.warning(f"[Outbound] Could not parse greeting/content - speaking full message")
                if is_escalation_callback:
                    logger.warning(f"[OutboundEscalation] No sentence delimiter found - might confuse farmer")
                try:
                    await session.say(message, allow_interruptions=True)
                except Exception as e:
                    logger.error(f"[Outbound] Failed to speak message: {e}")
        else:
            # message is None - use default
            logger.warning("Outbound call but no valid message in metadata - using fallback greeting")
            if is_escalation_callback:
                default_message = (
                    "नमस्ते! मैं किसान मित्र हूँ। "
                    "आपकी समस्या का समाधान मेरे पास है। "
                    "कृपया सुनिए।"
                )
            else:
                default_message = (
                    "नमस्ते! मैं किसान मित्र हूँ। "
                    "मैं आपको मौसम की जानकारी देने के लिए कॉल किया हूँ। "
                    "धन्यवाद।"
                )
            await session.say(default_message, allow_interruptions=True)
    
    # Check if there are any SIP participants already in the room
    # (Log for debugging purposes)
    for p in ctx.room.remote_participants.values():
        if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            logger.info(f"SIP participant present: {p.identity}")
    # Also listen for new participants joining
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}, kind={participant.kind}")
        # For outbound calls, the weather message is already spoken from room metadata
        # No need to handle participant metadata here
            
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
        # If the SIP user hangs up, we can end the session
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            logger.info("SIP participant left, terminating agent session.")
            # End the session gracefully - no direct process termination needed
            # The agent will detect no participants and exit naturally

    # ========== SILENCE MONITORING ==========
    # Note: Silence handler will be started automatically after agent's first speech
    # via the on_agent_stopped_speaking event handler
    
    logger.info("Session ready - waiting for interaction")


if __name__ == "__main__":
    cli.run_app(server)
