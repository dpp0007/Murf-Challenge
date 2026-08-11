"""
Discord Integration Service for escalation notifications and adviser interactions.

Handles:
- Sending escalation notifications to Discord
- Managing adviser resolution interactions  
- Updating escalation status in Discord
- Role-based authorization for advisers

Discord.py implementation with proper error handling and security.
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("discord_service")

try:
    import discord
    from discord.ext import commands
    DISCORD_PY_AVAILABLE = True
except ImportError:
    DISCORD_PY_AVAILABLE = False
    logger.warning("discord.py not installed - install with: pip install discord.py")


class DiscordService:
    """Service for Discord bot integration with Kisan Mitra escalations."""
    
    def __init__(self):
        """Initialize Discord service with configuration from environment."""
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.guild_id = int(os.getenv("DISCORD_GUILD_ID", "0")) if os.getenv("DISCORD_GUILD_ID") else None
        self.escalation_channel_id = int(os.getenv("DISCORD_ESCALATION_CHANNEL_ID", "0")) if os.getenv("DISCORD_ESCALATION_CHANNEL_ID") else None
        self.adviser_role_id = int(os.getenv("DISCORD_ADVISER_ROLE_ID", "0")) if os.getenv("DISCORD_ADVISER_ROLE_ID") else None
        
        self.enabled = bool(
            self.bot_token 
            and self.guild_id 
            and self.escalation_channel_id 
            and DISCORD_PY_AVAILABLE
        )
        
        # CRITICAL: Validate that adviser role is configured if Discord is enabled
        self.adviser_authorization_available = bool(self.adviser_role_id) if self.enabled else False
        
        self.bot: Optional[commands.Bot] = None
        self.escalation_messages: Dict[str, int] = {}  # reference_id -> message_id
        
        if not self.enabled:
            if not DISCORD_PY_AVAILABLE:
                logger.warning("[Discord] discord.py not available - install with: pip install discord.py")
            else:
                logger.warning("[Discord] Not configured - set DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_ESCALATION_CHANNEL_ID")
        else:
            logger.info(f"[Discord] Service enabled - Guild: {self.guild_id}, Channel: {self.escalation_channel_id}")
            
            # Log authorization configuration
            if not self.adviser_authorization_available:
                logger.error(
                    "[Discord] ⚠️  CRITICAL: DISCORD_ADVISER_ROLE_ID not configured. "
                    "Adviser resolution will be DISABLED. "
                    "Set DISCORD_ADVISER_ROLE_ID in environment to enable adviser actions."
                )
            else:
                logger.info(f"[Discord] Adviser authorization enabled - Role ID: {self.adviser_role_id}")
    
    def initialize_bot(self):
        """Initialize Discord bot client."""
        if not self.enabled:
            logger.warning("[Discord] Cannot initialize - service not configured")
            return False
        
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            
            self.bot = commands.Bot(command_prefix="!", intents=intents)
            
            @self.bot.event
            async def on_ready():
                logger.info(f"[Discord] Bot connected as {self.bot.user}")
                try:
                    guild = self.bot.get_guild(self.guild_id)
                    if not guild:
                        logger.error(f"[Discord] Guild {self.guild_id} not found")
                    else:
                        logger.info(f"[Discord] Connected to guild: {guild.name}")
                except Exception as e:
                    logger.error(f"[Discord] Error on ready: {e}")
            
            logger.info("[Discord] Bot client initialized")
            return True
            
        except Exception as e:
            logger.error(f"[Discord] Failed to initialize bot: {e}")
            return False
    
    async def send_escalation_notification(self, escalation: Any) -> Optional[int]:
        """
        Send escalation notification to Discord channel.
        
        Args:
            escalation: Escalation object from database
        
        Returns:
            Discord message ID if successful, None otherwise
        """
        if not self.enabled or not self.bot:
            logger.debug(f"[Discord] Notifications disabled - skipping {escalation.reference_id}")
            return None
        
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                logger.error(f"[Discord] Guild {self.guild_id} not found")
                return None
            
            channel = guild.get_channel(self.escalation_channel_id)
            if not channel:
                logger.error(f"[Discord] Channel {self.escalation_channel_id} not found")
                return None
            
            # Build embed message
            embed = self._build_escalation_embed(escalation)
            
            # Send message
            message = await channel.send(embed=embed)
            
            # Store message ID for later updates
            self.escalation_messages[escalation.reference_id] = message.id
            
            logger.info(f"[Discord] Escalation notification sent: {escalation.reference_id} (msg_id={message.id})")
            
            return message.id
            
        except Exception as e:
            logger.error(f"[Discord] Error sending notification: {e}", exc_info=True)
            return None
    
    def _build_escalation_embed(self, escalation: Any) -> 'discord.Embed':
        """Build Discord embed for escalation notification."""
        # Urgency emoji and color
        urgency_config = {
            "LOW": ("🟢", discord.Colour.green()),
            "MEDIUM": ("🟡", discord.Colour.gold()),
            "HIGH": ("🔴", discord.Colour.red()),
            "EMERGENCY": ("🚨", discord.Colour.from_rgb(139, 0, 0)),
        }
        emoji, color = urgency_config.get(escalation.urgency, ("🟡", discord.Colour.gold()))
        
        embed = discord.Embed(
            title=f"{emoji} Kisan Mitra Escalation",
            description=f"Reference: `{escalation.reference_id}`",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Farmer Name", value=escalation.farmer_name, inline=True)
        embed.add_field(name="District", value=escalation.district or "Unknown", inline=True)
        embed.add_field(name="Language", value=escalation.language.upper(), inline=True)
        embed.add_field(name="Urgency", value=escalation.urgency, inline=True)
        embed.add_field(name="Status", value=escalation.status, inline=True)
        embed.add_field(name="Callback Status", value=escalation.callback_status, inline=True)
        
        embed.add_field(name="Problem Type", value=escalation.reason, inline=False)
        
        # Truncate original question if too long
        question = escalation.original_question[:1024] if escalation.original_question else "N/A"
        embed.add_field(name="Original Question", value=f"```{question}```", inline=False)
        
        # Truncate summary if too long
        summary = escalation.summary[:1024] if escalation.summary else "No summary"
        embed.add_field(name="Summary", value=f"```{summary}```", inline=False)
        
        checked = escalation.what_agent_checked or "General context"
        embed.add_field(name="Agent Checked", value=f"```{checked}```", inline=False)
        
        embed.add_field(name="Preferred Follow-up", value=escalation.preferred_followup, inline=True)
        embed.add_field(name="Created At", value=escalation.created_at, inline=False)
        
        embed.set_footer(text="Use /resolve <reference_id> <answer> to submit resolution")
        
        return embed
    
    async def update_escalation_status(
        self,
        reference_id: str,
        status: str,
        callback_status: Optional[str] = None,
    ) -> bool:
        """
        Update escalation status message in Discord.
        
        Args:
            reference_id: Escalation reference ID
            status: New escalation status
            callback_status: Callback status if applicable
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.bot:
            logger.debug(f"[Discord] Status update disabled - {reference_id}")
            return True
        
        try:
            message_id = self.escalation_messages.get(reference_id)
            if not message_id:
                logger.debug(f"[Discord] No message ID stored for {reference_id}")
                return False
            
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                logger.error(f"[Discord] Guild not found for status update")
                return False
            
            channel = guild.get_channel(self.escalation_channel_id)
            if not channel:
                logger.error(f"[Discord] Channel not found for status update")
                return False
            
            # Get the message and update it
            message = await channel.fetch_message(message_id)
            
            # Update embed with new status
            if message.embeds:
                embed = message.embeds[0]
                # Find and update status fields
                embed.set_field_at(4, name="Status", value=status, inline=True)
                if callback_status:
                    embed.set_field_at(5, name="Callback Status", value=callback_status, inline=True)
                await message.edit(embed=embed)
            
            logger.info(f"[Discord] Status updated: {reference_id} -> {status}/{callback_status}")
            return True
            
        except Exception as e:
            logger.error(f"[Discord] Error updating status: {e}")
            return False
    
    def is_authorized_adviser(self, member: 'discord.Member') -> bool:
        """
        Check if a Discord member is authorized to resolve escalations.
        
        CRITICAL: Fails CLOSED - missing configuration prevents ANY adviser action.
        
        Args:
            member: Discord member object
        
        Returns:
            True if member has adviser role AND role is configured
        """
        # FAIL-CLOSED: If role not configured, NO ONE is authorized
        if not self.adviser_role_id:
            logger.error(
                "[Discord] AUTHORIZATION FAILED: "
                "DISCORD_ADVISER_ROLE_ID not configured. "
                "Protected actions cannot proceed."
            )
            return False  # ✅ FAIL-CLOSED - SECURITY FIX
        
        # Check if member has the adviser role
        role_ids = [role.id for role in member.roles]
        has_role = self.adviser_role_id in role_ids
        
        if not has_role:
            logger.warning(
                f"[Discord] AUTHORIZATION DENIED: "
                f"User {member.id} ({member.name}) does not have adviser role {self.adviser_role_id}"
            )
        else:
            logger.info(f"[Discord] User {member.id} ({member.name}) authorized as adviser")
        
        return has_role
    
    def validate_guild(self, guild_id: int) -> bool:
        """
        Validate that interaction comes from the correct Discord guild.
        
        Args:
            guild_id: Guild ID from interaction
        
        Returns:
            True if guild matches configured guild_id
        """
        if guild_id != self.guild_id:
            logger.warning(
                f"[Discord] GUILD MISMATCH: "
                f"Request from guild {guild_id}, "
                f"expected {self.guild_id}"
            )
            return False
        return True


# Global instance
_discord_service_instance: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get or create the global Discord service."""
    global _discord_service_instance
    if _discord_service_instance is None:
        _discord_service_instance = DiscordService()
    return _discord_service_instance
