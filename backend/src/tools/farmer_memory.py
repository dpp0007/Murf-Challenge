"""
Farmer memory management tools for Kisan Mitra.

Provides functions for:
- Looking up existing farmers
- Saving new farmer information with consent
- Managing persistent farmer profiles

These tools are exposed to Gemini LLM for use in conversations.
"""

import logging
from typing import Optional, Dict, Any
from livekit.agents import function_tool, RunContext

try:
    from ..database.farmer_repository import get_farmer_repository, FarmerProfile
except (ImportError, ValueError):
    from database.farmer_repository import get_farmer_repository, FarmerProfile

logger = logging.getLogger("farmer_memory")


def format_farmer_info(profile: FarmerProfile) -> str:
    """
    Format farmer profile for agent use.
    
    Returns readable summary of known information.
    """
    info_parts = []
    
    if profile.name:
        info_parts.append(f"Name: {profile.name}")
    
    if profile.crops_grown:
        info_parts.append(f"Crops: {profile.crops_grown}")
    
    if profile.land_size:
        info_parts.append(f"Land: {profile.land_size}")
    
    if profile.district:
        info_parts.append(f"District: {profile.district}")
    
    if profile.irrigation_type:
        info_parts.append(f"Irrigation: {profile.irrigation_type}")
    
    if profile.last_interaction:
        info_parts.append(f"Last talked: {profile.last_interaction}")
    
    return " | ".join(info_parts) if info_parts else "No information stored"


class FarmerMemoryTools:
    """
    Tools for farmer memory management.
    
    Exposed to LLM as @function_tool decorators.
    """
    
    def __init__(self):
        """Initialize memory tools."""
        self.repository = get_farmer_repository()
    
    @function_tool
    async def lookup_farmer(
        self,
        ctx: RunContext,
        user_id: str,
    ) -> str:
        """
        Look up an existing farmer in the database.
        
        Use this to check if a caller is a returning customer
        and what information you already know about them.
        
        Args:
            user_id: Unique identifier for the farmer
            
        Returns:
            JSON string with farmer information if found,
            or indication that farmer is not in system
            
        Example response:
        {
            "status": "found",
            "name": "Ramesh",
            "crops_grown": "wheat",
            "land_size": "5 acres",
            "district": "Varanasi",
            "irrigation_type": "drip",
            "language_preference": "hi"
        }
        
        Or if not found:
        {
            "status": "not_found",
            "message": "No farmer found with this ID"
        }
        """
        try:
            logger.info(f"[FarmerMemoryTools] Looking up farmer with user_id: {user_id}")
            profile = self.repository.lookup_farmer(user_id)
            
            if not profile:
                logger.info(f"[FarmerMemoryTools] Farmer {user_id} not found - new caller")
                return str({
                    "status": "not_found",
                    "message": f"No farmer found with ID {user_id}"
                })
            
            logger.info(f"[FarmerMemoryTools] Found farmer {user_id}: name={profile.name}, crops={profile.crops_grown}, district={profile.district}")
            return str({
                "status": "found",
                "name": profile.name,
                "crops_grown": profile.crops_grown,
                "land_size": profile.land_size,
                "district": profile.district,
                "irrigation_type": profile.irrigation_type,
                "language_preference": profile.language_preference,
                "last_interaction": profile.last_interaction,
            })
            
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
        user_id: str,
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
        
        This tool should be used when:
        1. User provides personal information (name, location, etc.)
        2. You ask "Would you like me to remember this?"
        3. User clearly agrees ("Yes", "हाँ", "Sure", etc.)
        
        Do NOT use if:
        - User has not explicitly agreed
        - User said "No" or declined storage
        - Information is temporary or conversational
        
        Args:
            user_id: Unique identifier for the farmer
            name: Farmer's name
            language_preference: Preferred language (hi/en)
            crops_grown: Crops the farmer grows
            land_size: Size of land/farm
            district: District or region
            irrigation_type: Type of irrigation system
            
        Returns:
            JSON string confirming save or error
            
        Example response:
        {
            "status": "saved",
            "message": "Information saved for next conversation"
        }
        """
        try:
            # Save to database
            success = self.repository.save_farmer_memory(
                user_id=user_id,
                name=name,
                language_preference=language_preference,
                outbound_calls_enabled=outbound_calls_enabled,
                crops_grown=crops_grown,
                land_size=land_size,
                district=district,
                irrigation_type=irrigation_type,
            )
            
            if success:
                logger.info(f"Saved farmer memory for {user_id}")
                return str({
                    "status": "saved",
                    "message": "Information saved for your next conversation"
                })
            else:
                logger.error(f"Failed to save farmer memory for {user_id}")
                return str({
                    "status": "error",
                    "message": "Could not save information right now"
                })
                
        except Exception as e:
            logger.error(f"Error in save_farmer_memory: {e}")
            return str({
                "status": "error",
                "message": "Could not save information due to an error"
            })


# Create global instance
_memory_tools_instance: Optional[FarmerMemoryTools] = None


def get_farmer_memory_tools() -> FarmerMemoryTools:
    """
    Get or create the global farmer memory tools instance.
    
    Returns:
        FarmerMemoryTools instance with @function_tool methods
    """
    global _memory_tools_instance
    if _memory_tools_instance is None:
        _memory_tools_instance = FarmerMemoryTools()
    return _memory_tools_instance
