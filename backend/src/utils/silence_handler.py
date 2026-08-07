"""
Silence detection and handling for voice conversations.
Event-driven inactivity monitoring with configurable timeouts and reprompts.
"""

import asyncio
import logging
import time
from typing import Callable, Optional, Awaitable

logger = logging.getLogger("silence_handler")


class ImprovedSilenceHandler:
    """
    Event-driven silence handler that responds immediately to user/agent activity.
    
    Instead of polling every N seconds, this handler:
    - Starts a timer when conversation begins
    - Immediately resets the timer on any speech activity
    - Triggers reprompts at configured intervals
    - Handles retry logic based on MAX_SILENCE_RETRIES
    
    This provides responsive, accurate silence detection without polling overhead.
    """
    
    def __init__(
        self,
        timeout: float,
        max_retries: int,
        reprompt_callback: Callable[[int], Awaitable[None]]
    ):
        """
        Initialize improved silence handler.
        
        Args:
            timeout: Seconds of silence before triggering action
            max_retries: Maximum number of reprompt attempts
            reprompt_callback: Async function to call with retry count
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.reprompt_callback = reprompt_callback
        
        self.last_activity_time = time.perf_counter()
        self.retry_count = 0
        self.is_active = False
        self.timer_task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start monitoring for silence."""
        if self.is_active:
            return
        
        self.is_active = True
        self.last_activity_time = time.perf_counter()
        self.retry_count = 0
        self._start_timer()
        logger.debug(f"Silence monitoring started (timeout: {self.timeout}s)")
    
    def stop(self):
        """Stop monitoring for silence."""
        self.is_active = False
        self._cancel_timer()
        logger.debug("Silence monitoring stopped")
    
    def reset(self):
        """Reset inactivity timer - called on any speech activity."""
        if not self.is_active:
            return
        
        self.last_activity_time = time.perf_counter()
        self.retry_count = 0
        
        # Cancel and restart timer for immediate response
        self._cancel_timer()
        self._start_timer()
        
        logger.debug("Silence timer reset due to activity")
    
    def _start_timer(self):
        """Start or restart the inactivity timer."""
        if self.timer_task and not self.timer_task.done():
            return  # Timer already running
        
        self.timer_task = asyncio.create_task(self._monitor_silence())
    
    def _cancel_timer(self):
        """Cancel active timer."""
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
            self.timer_task = None
    
    async def _monitor_silence(self):
        """
        Monitor for silence and trigger reprompts.
        
        This is event-driven: it only runs once per timeout period,
        not continuously polling like the old implementation.
        """
        try:
            # Wait for configured timeout
            await asyncio.sleep(self.timeout)
            
            if not self.is_active:
                return
            
            # Silence detected after timeout
            elapsed = time.perf_counter() - self.last_activity_time
            logger.info(f"⏱️ Silence detected after {elapsed:.1f}s (retry: {self.retry_count}/{self.max_retries})")
            
            # Check if we've exceeded max retries
            if self.retry_count >= self.max_retries:
                logger.info(f"⏱️ Max silence retries ({self.max_retries}) reached - ending conversation")
                self.stop()
                return
            
            # Trigger reprompt callback
            try:
                await self.reprompt_callback(self.retry_count)
                self.retry_count += 1
                
                # Restart timer for next timeout period
                self._start_timer()
                
            except Exception as e:
                logger.error(f"Failed to send silence reprompt: {e}")
                self.stop()
        
        except asyncio.CancelledError:
            # Timer was cancelled due to activity - this is expected
            logger.debug("Silence timer cancelled (activity detected)")
        
        except Exception as e:
            logger.error(f"Error in silence monitor: {e}")
            self.stop()


class SilenceHandler:
    """
    Handles silence detection and manages reprompting behavior.
    
    Tracks periods of user silence and triggers appropriate reprompts
    or conversation termination based on configuration.
    """
    
    def __init__(
        self,
        silence_timeout: float = 5.0,
        max_retries: int = 2,
        reprompt_callback: Optional[Callable[[int], str]] = None
    ):
        """
        Initialize silence handler.
        
        Args:
            silence_timeout: Seconds to wait before considering silence
            max_retries: Maximum number of reprompt attempts
            reprompt_callback: Function that returns reprompt message for retry count
        """
        self.silence_timeout = silence_timeout
        self.max_retries = max_retries
        self.reprompt_callback = reprompt_callback
        
        self.silence_count = 0
        self.is_monitoring = False
        self.silence_task: Optional[asyncio.Task] = None
        self.last_user_speech_time: Optional[float] = None
    
    def reset(self):
        """Reset silence counter."""
        self.silence_count = 0
        logger.debug("Silence counter reset")
    
    def on_user_speech(self):
        """Called when user speaks - resets silence detection."""
        self.reset()
        self.cancel_silence_timer()
        logger.debug("User speech detected, silence timer cancelled")
    
    def on_agent_speech(self):
        """Called when agent speaks - resets silence detection."""
        self.reset()
        self.cancel_silence_timer()
        logger.debug("Agent speech started, silence timer cancelled")
    
    def start_silence_timer(self, callback: Callable):
        """
        Start monitoring for silence.
        
        Args:
            callback: Async function to call when silence is detected
        """
        if self.silence_task and not self.silence_task.done():
            return  # Already monitoring
        
        self.silence_task = asyncio.create_task(
            self._silence_monitor(callback)
        )
        logger.debug(f"Silence timer started ({self.silence_timeout}s)")
    
    def cancel_silence_timer(self):
        """Cancel active silence monitoring."""
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
            logger.debug("Silence timer cancelled")
    
    async def _silence_monitor(self, callback: Callable):
        """
        Internal coroutine that waits for silence timeout.
        
        Args:
            callback: Function to call when silence timeout occurs
        """
        try:
            await asyncio.sleep(self.silence_timeout)
            
            # Silence timeout reached
            self.silence_count += 1
            logger.info(f"Silence detected (count: {self.silence_count}/{self.max_retries})")
            
            # Call the callback to handle silence
            await callback(self.silence_count)
            
        except asyncio.CancelledError:
            # Timer was cancelled - this is expected
            logger.debug("Silence monitor cancelled")
    
    def should_end_conversation(self) -> bool:
        """
        Check if conversation should be ended due to repeated silence.
        
        Returns:
            True if max retries exceeded
        """
        return self.silence_count >= self.max_retries
    
    def get_reprompt_message(self) -> str:
        """
        Get appropriate reprompt message based on current silence count.
        
        Returns:
            Reprompt message string
        """
        if self.reprompt_callback:
            return self.reprompt_callback(self.silence_count - 1)
        
        # Default reprompts
        if self.silence_count == 1:
            return (
                "क्या आप मेरी आवाज़ सुन पा रहे हैं? "
                "मैं आपकी मदद के लिए यहाँ हूँ।"
            )
        elif self.silence_count == 2:
            return (
                "लगता है अभी आप व्यस्त हैं। "
                "जब चाहें दोबारा बात करिए। "
                "धन्यवाद।"
            )
        else:
            return "धन्यवाद। नमस्ते।"
