"""
Latency tracking utilities for voice pipeline metrics.
Measures individual stage latencies: STT, LLM, TTS, and total end-to-end.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("latency_tracker")


class LatencyTracker:
    """
    Tracks latency across voice pipeline stages.
    
    Measures:
    - STT (Speech-to-Text) latency
    - LLM (Language Model) latency
    - TTS (Text-to-Speech) latency
    - End-to-end total latency
    
    Uses time.perf_counter() for high-resolution measurements.
    """
    
    def __init__(self):
        """Initialize latency tracker with empty timestamps."""
        self.reset()
    
    def reset(self):
        """Reset all timestamps for a new turn."""
        self.user_speech_end: Optional[float] = None
        self.stt_complete: Optional[float] = None
        self.llm_complete: Optional[float] = None
        self.tts_start: Optional[float] = None
        self.first_audio_out: Optional[float] = None
    
    def mark_user_speech_end(self):
        """Mark when user finishes speaking."""
        self.user_speech_end = time.perf_counter()
        logger.debug(f"🎤 User speech ended at: {self.user_speech_end:.3f}")
    
    def mark_stt_complete(self):
        """Mark when STT processing completes."""
        self.stt_complete = time.perf_counter()
    
    def mark_llm_complete(self):
        """Mark when LLM generates response."""
        self.llm_complete = time.perf_counter()
    
    def mark_tts_start(self):
        """Mark when TTS synthesis begins."""
        self.tts_start = time.perf_counter()
    
    def mark_first_audio_out(self):
        """Mark when first audio is sent to user."""
        self.first_audio_out = time.perf_counter()
    
    def get_stt_latency(self) -> Optional[float]:
        """Calculate STT latency in milliseconds."""
        if self.user_speech_end and self.stt_complete:
            return (self.stt_complete - self.user_speech_end) * 1000
        return None
    
    def get_llm_latency(self) -> Optional[float]:
        """Calculate LLM latency in milliseconds."""
        if self.stt_complete and self.llm_complete:
            return (self.llm_complete - self.stt_complete) * 1000
        return None
    
    def get_tts_latency(self) -> Optional[float]:
        """Calculate TTS latency in milliseconds."""
        if self.llm_complete and self.tts_start:
            return (self.tts_start - self.llm_complete) * 1000
        return None
    
    def get_total_latency(self) -> Optional[float]:
        """Calculate total end-to-end latency in milliseconds."""
        if self.user_speech_end and self.first_audio_out:
            return (self.first_audio_out - self.user_speech_end) * 1000
        return None
    
    def log_metrics(self):
        """
        Log detailed pipeline metrics in structured format.
        
        Outputs:
        --------------------------------
        Voice Pipeline Metrics
        Speech End: <timestamp>
        STT: <ms>
        LLM: <ms>
        TTS: <ms>
        Total: <ms>
        --------------------------------
        """
        stt = self.get_stt_latency()
        llm = self.get_llm_latency()
        tts = self.get_tts_latency()
        total = self.get_total_latency()
        
        # Build metrics output
        lines = [
            "--------------------------------",
            "Voice Pipeline Metrics",
        ]
        
        if self.user_speech_end:
            lines.append(f"Speech End: {self.user_speech_end:.3f}")
        
        if stt is not None:
            lines.append(f"STT: {stt:.0f} ms")
        
        if llm is not None:
            lines.append(f"LLM: {llm:.0f} ms")
        
        if tts is not None:
            lines.append(f"TTS: {tts:.0f} ms")
        
        if total is not None:
            lines.append(f"Total: {total:.0f} ms")
        
        lines.append("--------------------------------")
        
        # Log all metrics together
        logger.info("\n".join(lines))
