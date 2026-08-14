"""
Crop Problem Specialist Agent

A focused specialist for crop-specific problems, diseases, and pest management.
Works within the same conversation as Kisan Mitra using male voice (Samar).

This agent is separate from Kisan Mitra but shares the same call context.
"""

import logging
from typing import Optional
from livekit.agents import Agent
from src.prompts.crop_specialist_prompt import get_crop_specialist_prompt

logger = logging.getLogger("crop_specialist")


class CropSpecialist(Agent):
    """
    Crop Problem Specialist Agent
    
    Handles:
    - Crop disease identification
    - Pest problem diagnosis
    - Crop-specific troubleshooting
    - Targeted follow-up questions
    
    Does NOT handle:
    - Weather queries (handback to Kisan Mitra)
    - Mandi prices (handback to Kisan Mitra)
    - Generic farming questions (handback to Kisan Mitra)
    """
    
    def __init__(self, room_name: Optional[str] = None, call_id: Optional[str] = None):
        """
        Initialize Crop Specialist agent.
        
        Args:
            room_name: Room name from the session
            call_id: Unique call identifier for analytics
        """
        system_prompt = get_crop_specialist_prompt()
        
        # Store identifiers for context
        self.call_id = call_id or room_name
        self.room_name = room_name
        
        super().__init__(instructions=system_prompt)
        
        logger.info(f"Crop Specialist initialized for call_id: {call_id}")
        
        if room_name:
            logger.info(f"[CropSpecialist] Room name set to: {room_name}")
