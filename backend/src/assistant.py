"""
Kisan Mitra Assistant - Production-ready agriculture voice assistant.
This module contains the core Assistant class with clean architecture.
"""

import logging
from livekit.agents import Agent

from prompts import get_system_prompt
from config import ASSISTANT_NAME

logger = logging.getLogger("assistant")


class KisanMitraAssistant(Agent):
    """
    Production-ready agriculture assistant for Indian farmers.
    
    This assistant provides farming guidance in Hindi/English,
    handles natural voice conversations, and maintains context
    across multi-turn dialogues.
    """
    
    def __init__(self):
        """
        Initialize Kisan Mitra assistant with system prompt.
        
        The prompt is loaded from the prompts module,
        keeping the implementation clean and maintainable.
        """
        system_prompt = get_system_prompt()
        super().__init__(instructions=system_prompt)
        
        logger.info(f"{ASSISTANT_NAME} assistant initialized")
    
    # Future: Tool functions can be added here using @function_tool decorator
    # Example:
    # @function_tool
    # async def get_weather(self, context: RunContext, location: str):
    #     """Get weather information for a location."""
    #     pass
