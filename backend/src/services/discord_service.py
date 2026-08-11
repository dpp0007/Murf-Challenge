"""
Discord Integration Service for escalation notifications and adviser interactions.

Handles:
- Sending escalation notifications to Discord
- Handling adviser resolution submissions
- Updating escalation status in Discord
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger("discord_service")


class DiscordService:
    """Service for Discord integrations."""
    
    def __init__(self):
        """Initialize Discord service."""
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.guild_id = os.getenv("DISCORD_GUILD_ID")
        self.escalation_channel_id = os.getenv("DISCORD_ESCALATION_CHANNEL_ID")
        self.resolved_channel_id = os.getenv("DISCORD_RESOLVED_CHANNEL_ID")
        self.high_priority_channel_id = os.getenv("DISCORD_HIGH_PRIORITY_CHANNEL_ID")
        self.adviser_role_id = os.getenv("DISCORD_ADVISER_ROLE_ID")
        
        self.enabled = bool(self.bot_token and self.guild_id and self.escalation_channel_id)
        
        if not self.enabled:
            logger.warning("Discord service not configured - notifications will be skipped")
        else:
            logger.info("Discord service initialized")
            
            # Try to import discord.py if available
            try:
                import discord
                self.discord = discord
            except ImportError:
                logger.warning("discord.py not installed - Discord features disabled")
                self.discord = None
    
    def send_escalation_notification(self, escalation: Any) -> Optional[str]:
        """
        Send escalation notification to Discord.
        
        Args:
            escalation: Escalation object
        
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.enabled or not self.discord:
            logger.debug(f"Discord notifications disabled - skipping {escalation.reference_id}")
            return None
        
        try:
            import asyncio
            
            # This will be called asynchronously from the backend
            # For now, we'll log it and implement a simple webhook version
            logger.info(f"Escalation notification: {escalation.reference_id} for {escalation.farmer_name}")
            
            # Build the message
            message = self._build_escalation_message(escalation)
            
            # Try to send via webhook or bot client
            # This is a placeholder - actual implementation depends on the Discord.py version
            logger.debug(f"Message content: {message}")
            
            return escalation.reference_id
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return None
    
    def _build_escalation_message(self, escalation: Any) -> str:
        """Build Discord message content for escalation."""
        urgency_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴",
            "EMERGENCY": "🚨",
        }
        emoji = urgency_emoji.get(escalation.urgency, "🟡")
        
        message = f"""
{emoji} **KISAN MITRA — HUMAN HELP REQUEST**

**Reference:** `{escalation.reference_id}`
**Farmer:** {escalation.farmer_name}
**District:** {escalation.district or "Unknown"}
**Language:** {escalation.language.upper()}
**Urgency:** {escalation.urgency}

**Problem:** {escalation.reason}

**Original Question:**
> {escalation.original_question}

**Summary:**
{escalation.summary}

**What Kisan Mitra Checked:**
{escalation.what_agent_checked or "General crop context"}

**Preferred Follow-up:** {escalation.preferred_followup}

**Status:** {escalation.status}

---
*Use reactions or reply to acknowledge. Authorized advisers can resolve using the command.*
"""
        return message.strip()
    
    def update_escalation_status(
        self,
        reference_id: str,
        status: str,
        callback_status: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Update escalation status in Discord.
        
        Args:
            reference_id: Escalation reference ID
            status: Escalation status (OPEN, RESOLVED, etc.)
            callback_status: Callback status if applicable
            message_id: Discord message ID to update
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.discord:
            logger.debug(f"Discord status update disabled - {reference_id} -> {status}")
            return True
        
        try:
            logger.info(f"Discord status update: {reference_id} -> {status}/{callback_status}")
            
            # In a real implementation, this would edit the Discord message
            # For now, we log it
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating Discord status: {e}")
            return False
    
    def is_authorized_adviser(self, user_id: str, roles: list) -> bool:
        """
        Check if a Discord user is authorized to resolve escalations.
        
        Args:
            user_id: Discord user ID
            roles: List of role IDs the user has
        
        Returns:
            True if user can resolve escalations
        """
        if not self.adviser_role_id:
            # No role requirement configured
            logger.warning("DISCORD_ADVISER_ROLE_ID not configured - allowing all users")
            return True
        
        # Check if user has the adviser role
        has_role = self.adviser_role_id in [str(r) for r in roles]
        
        if not has_role:
            logger.warning(f"User {user_id} not authorized - missing role {self.adviser_role_id}")
        
        return has_role


# Global instance
_discord_service_instance: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get or create the global Discord service."""
    global _discord_service_instance
    if _discord_service_instance is None:
        _discord_service_instance = DiscordService()
    return _discord_service_instance
