"""
Kisan Mitra - Production Voice Agent for Indian Farmers
Refactored for Murf VoiceForBharat Challenge Day 2

This module orchestrates the voice pipeline, handles latency tracking,
silence detection, and response post-processing for optimal voice UX.
"""

import asyncio
import logging

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

# Import configuration and utilities
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

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Initialize agent server
server = AgentServer()


def prewarm(proc: JobProcess):
    """
    Prewarm function to initialize models before session starts.
    This improves first-response latency.
    """
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model preloaded")


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
    - Session lifecycle
    """
    # Setup logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": AGENT_NAME,
    }
    
    logger.info(f"Starting Kisan Mitra session for room: {ctx.room.name}")
    
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
        
        # Reset silence handler on user activity (event-driven reset)
        silence_handler.reset()
        
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
        
        # Reset silence handler when agent speaks (event-driven reset)
        silence_handler.reset()
        
        # Log detailed pipeline metrics
        if ENABLE_LATENCY_LOGGING:
            latency_tracker.log_metrics()
        
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
        agent=KisanMitraAssistant(),
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
    
    # ========== INITIAL GREETING ==========
    
    async def send_initial_greeting():
        """Send initial greeting to user immediately after connection."""
        await asyncio.sleep(1)  # Brief pause to ensure connection is stable
        try:
            await session.say(GREETING_MESSAGE, allow_interruptions=True)
            logger.info("👋 Initial greeting sent to user")
            
            # Start event-driven silence monitoring after greeting
            silence_handler.start()
            
        except Exception as e:
            logger.error(f"Failed to send initial greeting: {e}")
    
    # Send initial greeting immediately
    await send_initial_greeting()


if __name__ == "__main__":
    cli.run_app(server)
