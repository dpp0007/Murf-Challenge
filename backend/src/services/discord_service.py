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
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Import services and database modules at module level to avoid import issues in async contexts
try:
    from ..database.escalation_repository import get_escalation_repository
    from .escalation_callback_service import get_escalation_callback_service
except (ImportError, ValueError):
    # Fallback for when running from different contexts
    try:
        from database.escalation_repository import get_escalation_repository
        from services.escalation_callback_service import get_escalation_callback_service
    except (ImportError, ValueError):
        get_escalation_repository = None
        get_escalation_callback_service = None

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
        self.resolved_channel_id = int(os.getenv("DISCORD_RESOLVED_CHANNEL_ID", "0")) if os.getenv("DISCORD_RESOLVED_CHANNEL_ID") else None
        
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
        self._bot_started = False  # Track if bot startup was initiated
        self._bot_thread: Optional[threading.Thread] = None  # Thread running the bot
        self._bot_loop: Optional[asyncio.AbstractEventLoop] = None  # Bot's own event loop
        
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
            
            # Store reference to self for use in nested functions
            service_self = self
            
            # Register slash commands BEFORE any event handlers
            logger.info("[Discord] Registering /resolve slash command...")
            print("[Discord Init] Registering /resolve slash command...")
            
            @self.bot.tree.command(
                name="resolve",
                description="Resolve an escalation with adviser answer"
            )
            @discord.app_commands.describe(
                reference_id="Escalation reference ID (e.g., KM-20260812-0001)",
                answer="Your solution for the farmer's problem"
            )
            async def resolve_command(
                interaction: discord.Interaction,
                reference_id: str,
                answer: str
            ):
                """Handle /resolve command from adviser."""
                print(f"\n[RESOLVE COMMAND HANDLER TRIGGERED]")
                print(f"  Reference ID: {reference_id}")
                print(f"  Answer: {answer[:50]}...")
                print(f"  User: {interaction.user.name} ({interaction.user.id})")
                print(f"  Guild: {interaction.guild_id}")
                
                logger.info(f"[Discord] /resolve command invoked: ref={reference_id}, user={interaction.user.name}")
                
                # IMMEDIATE response - must happen INSIDE the command callback, not in a separate function
                # This is because Discord has a strict 3-second timeout for responses
                try:
                    print(f"[RESOLVE] Deferring response...")
                    await interaction.response.defer(ephemeral=True)
                    print(f"[RESOLVE] Response deferred successfully")
                except Exception as e:
                    logger.error(f"[Discord] Failed to defer interaction: {e}")
                    print(f"[RESOLVE] ERROR deferring: {e}")
                    return
                
                # NOW call the handler (response is already sent, no timeout risk)
                print(f"[RESOLVE] Calling handler...")
                await service_self._handle_resolve_command(interaction, reference_id, answer)
                print(f"[RESOLVE] Handler completed")
            
            print(f"[Discord Init] Command registered in tree with name: {resolve_command.qualified_name}")
            logger.info(f"[Discord] Command registered in tree: {resolve_command.qualified_name}")
            print(f"[Discord Init] Total commands in tree: {len(list(self.bot.tree._get_all_commands()))}")
            print(f"[Discord Init] Resolve command object: {resolve_command}")
            print(f"[Discord Init] Resolve command callback: {resolve_command.callback}")
            
            # Also add a message handler as fallback for text-based resolve commands
            @self.bot.event
            async def on_message(message: discord.Message):
                """Handle resolve commands sent as plain text messages (fallback)."""
                # Ignore bot messages
                if message.author.bot:
                    return
                
                # Ignore slash commands - they're handled by the tree command handler
                # Slash commands have content starting with / but are NOT message events
                # We only handle explicit text-based resolve commands here
                if message.content.startswith('/'):
                    # This is likely a slash command, ignore it
                    # (slash commands are handled via tree.command, not message events)
                    await self.bot.process_commands(message)
                    return
                
                # Process commands with the bot command processor
                await self.bot.process_commands(message)
            
            @self.bot.event
            async def on_ready():
                logger.info(f"[Discord] ✅✅✅ Bot connected as {service_self.bot.user} ✅✅✅")
                print(f"\n[Discord on_ready] Bot connected as: {service_self.bot.user}")
                print(f"[Discord on_ready] Latency: {service_self.bot.latency * 1000:.0f}ms")
                print(f"[Discord on_ready] NOTE: Command sync handled by delayed global sync thread")
                
                try:
                    # Wait a moment for guild to be available
                    await asyncio.sleep(1)
                    
                    guild = service_self.bot.get_guild(service_self.guild_id)
                    if not guild:
                        logger.error(f"[Discord] Guild {service_self.guild_id} not found")
                        print(f"[Discord on_ready] ERROR: Guild {service_self.guild_id} not found")
                        print(f"[Discord on_ready] Available guilds: {[g.name for g in service_self.bot.guilds]}")
                    else:
                        logger.info(f"[Discord] Connected to guild: {guild.name}")
                        print(f"[Discord on_ready] Guild: {guild.name} (ID: {guild.id})")
                        
                except Exception as e:
                    logger.error(f"[Discord] Error on ready: {e}", exc_info=True)
                    print(f"[Discord on_ready] ERROR: {e}")
            
            logger.info("[Discord] Bot client initialized successfully")
            
            # Start bot in a separate thread with its own event loop
            # This prevents blocking the main LiveKit event loop
            self._start_bot_in_thread()
            
            return True
            
        except Exception as e:
            logger.error(f"[Discord] Failed to initialize bot: {e}", exc_info=True)
            return False
    
    def sync_commands(self) -> bool:
        """
        Sync slash commands with Discord.
        This should be called after bot is ready.
        """
        if not self.bot:
            logger.warning("[Discord] Cannot sync commands - bot not initialized")
            return False
        
        try:
            # Schedule command sync
            asyncio.create_task(self.bot.tree.sync())
            logger.info("[Discord] Slash commands sync scheduled")
            return True
        except Exception as e:
            logger.error(f"[Discord] Failed to sync commands: {e}")
            return False
    
    def _start_bot_in_thread(self):
        """
        Start Discord bot in a separate thread with its own event loop.
        
        This prevents blocking the main LiveKit event loop and ensures
        bot.start() runs properly with asyncio event handling.
        """
        if self._bot_thread and self._bot_thread.is_alive():
            logger.warning("[Discord] Bot thread already running")
            return
        
        def run_bot_in_thread():
            """Thread target: creates new event loop and runs bot.start()"""
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._bot_loop = loop
                
                logger.info("[Discord] Bot thread started - creating event loop and running bot.start()...")
                print("[Discord Thread] Starting bot.start() with token...")
                
                # This blocks until the bot is stopped
                loop.run_until_complete(self.bot.start(self.bot_token))
                
                logger.info("[Discord] Bot.start() completed successfully")
            except Exception as e:
                logger.error(f"[Discord] Bot thread error: {e}", exc_info=True)
                print(f"[Discord Thread ERROR] {e}")
            finally:
                # Clean up loop
                if self._bot_loop:
                    self._bot_loop.close()
                    self._bot_loop = None
                logger.warning("[Discord] Bot thread terminated")
        
        # Create and start thread as daemon (will close when main thread closes)
        self._bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True, name="DiscordBotThread")
        self._bot_thread.start()
        logger.info("[Discord] Bot startup thread created and started")
        
        # Schedule a delayed global sync as fallback (in case guild sync fails)
        def delayed_sync():
            """Delayed sync of slash commands (fallback)."""
            import time
            time.sleep(5)  # Wait 5 seconds for bot to fully connect
            try:
                if self.bot and self.bot.user:
                    logger.info("[Discord] Performing delayed global sync as fallback...")
                    print("[Discord Delayed Sync] Syncing globally...")
                    # Create a coroutine and run it in the bot's event loop
                    async def do_global_sync():
                        try:
                            synced = await self.bot.tree.sync()
                            logger.info(f"[Discord] Global sync completed: {[cmd.name for cmd in synced]}")
                            print(f"[Discord Delayed Sync] Global sync done: {[cmd.name for cmd in synced]}")
                        except Exception as e:
                            logger.error(f"[Discord] Global sync failed: {e}")
                    
                    if self._bot_loop:
                        future = asyncio.run_coroutine_threadsafe(do_global_sync(), self._bot_loop)
                        try:
                            future.result(timeout=10)
                        except Exception as e:
                            logger.error(f"[Discord] Global sync timed out: {e}")
            except Exception as e:
                logger.error(f"[Discord] Delayed sync error: {e}")
        
        # Run delayed sync in background thread
        sync_thread = threading.Thread(target=delayed_sync, daemon=True, name="DiscordSyncThread")
        sync_thread.start()
    async def send_escalation_notification(self, escalation: Any) -> Optional[int]:
        """
        Send escalation notification to Discord channel.
        ALWAYS uses HTTP to the API server to ensure notifications reach Discord.
        
        This is critical because:
        - Agent and HTTP server run in separate processes
        - Each process has its own discord_service instance
        - Only HTTP server's bot is connected
        - Therefore ALL notifications must go via HTTP
        
        Args:
            escalation: Escalation object from database
        
        Returns:
            Escalation reference ID if queued, None if notification disabled
        """
        if not self.enabled:
            logger.debug(f"[Discord] Notifications disabled - skipping {escalation.reference_id}")
            return None
        
        logger.info(f"[Discord] Sending notification via HTTP: {escalation.reference_id}")
        
        # ALWAYS use HTTP - this ensures notifications work across processes
        try:
            import httpx
            
            async def http_notify():
                async with httpx.AsyncClient() as client:
                    try:
                        logger.info(f"[Discord] HTTP POST to /notify-discord: {escalation.reference_id}")
                        response = await client.post(
                            "http://localhost:8080/api/escalations/notify-discord",
                            json={"reference_id": escalation.reference_id},
                            timeout=5.0
                        )
                        if response.status_code == 200:
                            logger.info(f"[Discord] ✅ HTTP notification successful: {escalation.reference_id}")
                        else:
                            logger.warning(f"[Discord] HTTP notification returned status {response.status_code}: {escalation.reference_id}")
                    except Exception as e:
                        logger.error(f"[Discord] HTTP notification failed: {e} for {escalation.reference_id}")
            
            asyncio.create_task(http_notify())
            logger.info(f"[Discord] Escalation notification queued via HTTP: {escalation.reference_id}")
            return escalation.reference_id
            
        except Exception as e:
            logger.error(f"[Discord] Failed to queue HTTP notification: {e}")
            return None
    
    async def send_resolution_notification(self, escalation: Any, adviser_name: str) -> bool:
        """
        Send a notification to the resolved channel when callback completes successfully.
        
        Args:
            escalation: Escalation object
            adviser_name: Name of the adviser who resolved it
        
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.bot or not self.resolved_channel_id:
            logger.debug(f"[Discord] Resolution notification disabled - skipping {escalation.reference_id}")
            return False
        
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                logger.error(f"[Discord] Guild {self.guild_id} not found for resolution notification")
                return False
            
            channel = guild.get_channel(self.resolved_channel_id)
            if not channel:
                logger.error(f"[Discord] Resolved channel {self.resolved_channel_id} not found")
                return False
            
            # Build embed for resolved escalation
            embed = discord.Embed(
                title="✅ Escalation Resolved & Called",
                description=f"Reference: `{escalation.reference_id}`",
                color=discord.Colour.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Farmer Name", value=escalation.farmer_name, inline=True)
            embed.add_field(name="Adviser", value=adviser_name, inline=True)
            embed.add_field(name="District", value=escalation.district or "Unknown", inline=True)
            embed.add_field(name="Status", value="✅ COMPLETED", inline=True)
            embed.add_field(name="Problem Type", value=escalation.reason, inline=False)
            embed.add_field(name="Solution", value=f"```{escalation.human_answer}```", inline=False)
            embed.add_field(name="Callback Status", value="✅ COMPLETED", inline=False)
            embed.set_footer(text="Farmer has received the solution via automatic phone call")
            
            # Send to resolved channel
            if self._bot_loop:
                async def send_msg():
                    return await channel.send(embed=embed)
                
                future = asyncio.run_coroutine_threadsafe(send_msg(), self._bot_loop)
                message = future.result(timeout=10)
                
                logger.info(f"[Discord] Resolution notification sent to resolved channel: {escalation.reference_id}")
                print(f"[Discord] Sent resolution notification to #resolved channel")
                return True
            else:
                logger.warning(f"[Discord] Bot loop not available for resolution notification")
                return False
        
        except Exception as e:
            logger.error(f"[Discord] Error sending resolution notification: {e}")
            print(f"[Discord] Error sending resolution: {e}")
            return False
    
    async def _send_notification_async(self, escalation: Any) -> Optional[int]:
        """
        Actually send the escalation notification (async task).
        Runs in background - doesn't block escalation flow.
        
        Args:
            escalation: Escalation object
        
        Returns:
            Discord message ID if successful
        """
        try:
            # Wait for bot to be ready (with longer timeout and backoff)
            max_wait = 30  # seconds - allow more time for bot connection
            waited = 0
            wait_interval = 0.5
            
            logger.info(f"[Discord] Waiting for bot connection for {escalation.reference_id}...")
            print(f"[Discord Notification] Waiting for bot.user (max {max_wait}s)...")
            
            while not self.bot.user and waited < max_wait:
                if waited % 5 == 0:  # Log every 5 seconds instead of 0.5s
                    logger.debug(f"[Discord] Waiting for bot connection... ({waited:.1f}s / {max_wait}s)")
                    print(f"[Discord Notification] Still waiting... {waited:.1f}s")
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            if not self.bot.user:
                logger.error(f"[Discord] Bot failed to connect within {max_wait}s for {escalation.reference_id}")
                print(f"[Discord Notification] Bot failed to connect within {max_wait}s")
                return None
            
            logger.info(f"[Discord] Bot connected after {waited:.1f}s")
            print(f"[Discord Notification] Bot connected! ({waited:.1f}s)")
            
            # Get guild - bot should be ready now
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                logger.error(f"[Discord] Guild {self.guild_id} not found immediately")
                return None
            
            channel = guild.get_channel(self.escalation_channel_id)
            if not channel:
                logger.error(f"[Discord] Channel {self.escalation_channel_id} not found in guild {self.guild_id}")
                return None
            
            # Build embed message
            embed = self._build_escalation_embed(escalation)
            
            # Send message using the bot's event loop to avoid asyncio context issues
            # The bot runs in a separate thread with its own loop
            try:
                import concurrent.futures
                
                async def send_msg():
                    return await channel.send(embed=embed)
                
                # Run the coroutine in the bot's event loop
                if self._bot_loop:
                    future = asyncio.run_coroutine_threadsafe(send_msg(), self._bot_loop)
                    message = future.result(timeout=10)
                else:
                    # Fallback: try in current loop
                    message = await send_msg()
                
                # Store message ID for later updates
                self.escalation_messages[escalation.reference_id] = message.id
                
                logger.info(f"[Discord] Escalation notification sent: {escalation.reference_id} (msg_id={message.id})")
                print(f"[Discord Notification] ✅ Sent to Discord! Message ID: {message.id}")
                
                return message.id
            except concurrent.futures.TimeoutError:
                logger.error(f"[Discord] Timeout sending message to Discord for {escalation.reference_id}")
                print(f"[Discord Notification] ❌ Timeout sending message")
                return None
            
        except Exception as e:
            logger.error(f"[Discord] Error sending notification for {escalation.reference_id}: {e}", exc_info=True)
            print(f"[Discord Notification] ❌ Error: {e}")
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
        
        embed.set_footer(text="Reply with: /resolve <ref_id> <your_solution>")
        
        return embed
    
    async def update_escalation_status(
        self,
        reference_id: str,
        status: str,
        callback_status: Optional[str] = None,
    ) -> bool:
        """
        Update escalation status message in Discord.
        
        IDEMPOTENT: Only updates if message exists and is different.
        Prevents duplicate messages to adviser.
        
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
                logger.debug(f"[Discord] No message ID stored for {reference_id} - cannot update")
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
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                logger.warning(f"[Discord] Message not found in channel - already deleted? {reference_id}")
                # Remove from tracking
                self.escalation_messages.pop(reference_id, None)
                return False
            
            # Update embed with new status (idempotent check)
            if message.embeds:
                embed = message.embeds[0]
                
                # IDEMPOTENCY: Check if status is already the same
                status_field_value = None
                for field in embed.fields:
                    if field.name == "Status":
                        status_field_value = field.value
                        break
                
                # Only update if different
                if status_field_value == status:
                    logger.debug(f"[Discord] Status already {status} for {reference_id} - skipping update")
                    return True  # Already in correct state
                
                # Update status fields
                try:
                    embed.set_field_at(4, name="Status", value=status, inline=True)
                    if callback_status:
                        embed.set_field_at(5, name="Callback Status", value=callback_status, inline=True)
                    await message.edit(embed=embed)
                except (IndexError, discord.HTTPException) as e:
                    logger.error(f"[Discord] Failed to update embed fields: {e}")
                    return False
            
            logger.info(f"[Discord] Status updated: {reference_id} -> {status}/{callback_status}")
            return True
            
        except Exception as e:
            logger.error(f"[Discord] Error updating status: {e}", exc_info=True)
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
    
    async def _handle_resolve_command(
        self,
        interaction: 'discord.Interaction',
        reference_id: str,
        answer: str
    ) -> None:
        """
        Handle /resolve command from adviser in Discord.
        
        NOTE: Interaction is ALREADY deferred by the command callback.
        This handler just needs to do the work and send followup messages.
        
        Args:
            interaction: Discord slash command interaction (already deferred)
            reference_id: Escalation reference ID
            answer: Adviser's solution/answer
        """
        print(f"\n[_handle_resolve_command] CALLED")
        print(f"  ref_id={reference_id}, answer={answer[:50]}...")
        print(f"  user={interaction.user.name}, guild_id={interaction.guild_id}")
        
        # Interaction is already deferred, so we can take our time now
        try:
            
            # Check authorization
            if not self.is_authorized_adviser(interaction.user):
                try:
                    await interaction.followup.send(
                        "❌ You are not authorized to resolve escalations. "
                        "Only advisers can use this command.",
                        ephemeral=True
                    )
                except:
                    pass
                logger.warning(
                    f"[Discord] Unauthorized resolve attempt by {interaction.user.name} "
                    f"({interaction.user.id})"
                )
                return
            
            # Validate guild
            if not self.validate_guild(interaction.guild_id):
                try:
                    await interaction.followup.send(
                        "❌ This command can only be used in the correct server.",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            # Validate input
            reference_id = reference_id.strip().upper()
            answer = answer.strip()
            
            if not reference_id or not answer:
                try:
                    await interaction.followup.send(
                        "❌ Reference ID and answer are required.",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            if len(answer) > 5000:
                try:
                    await interaction.followup.send(
                        "❌ Answer is too long. Maximum 5000 characters.",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            logger.info(
                f"[Discord] Resolve command: ref={reference_id}, "
                f"adviser={interaction.user.name}"
            )
            print(f"[Discord] Resolve command handler called for {reference_id}")
            
            # Use module-level imports (already imported at top of file)
            if not get_escalation_repository or not get_escalation_callback_service:
                logger.error("[Discord] Required services not imported at module level")
                try:
                    await interaction.followup.send(
                        "❌ Internal service error - required dependencies not loaded",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            try:
                escalation_repo = get_escalation_repository()
                print(f"[Discord] Got escalation repo: {escalation_repo}")
            except Exception as e:
                logger.error(f"[Discord] Failed to get escalation repo: {e}")
                try:
                    await interaction.followup.send(
                        "❌ Failed to access escalation database",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            escalation = escalation_repo.get_escalation_by_reference(reference_id)
            print(f"[Discord] Fetched escalation: {escalation}")
            
            if not escalation:
                try:
                    await interaction.followup.send(
                        f"❌ Escalation not found: `{reference_id}`",
                        ephemeral=True
                    )
                except:
                    pass
                logger.warning(f"[Discord] Escalation not found: {reference_id}")
                return
            
            print(f"[Discord] Escalation found: status={escalation.status}, callback_status={escalation.callback_status}")
            
            # Resolve the escalation
            try:
                resolved = escalation_repo.resolve_escalation(
                    reference_id=reference_id,
                    human_answer=answer,
                    resolution_notes=f"Resolved by {interaction.user.name}",
                )
                print(f"[Discord] resolve_escalation returned: {resolved}")
            except Exception as e:
                logger.error(f"[Discord] Exception during resolve_escalation: {e}", exc_info=True)
                try:
                    await interaction.followup.send(
                        f"❌ Failed to resolve escalation: `{reference_id}` - {str(e)}",
                        ephemeral=True
                    )
                except:
                    pass
                return
            
            if not resolved:
                try:
                    await interaction.followup.send(
                        f"❌ Failed to resolve escalation: `{reference_id}`",
                        ephemeral=True
                    )
                except:
                    pass
                logger.error(f"[Discord] Failed to resolve: {reference_id}")
                return
            
            print(f"[Discord] Escalation resolved, now queuing callback...")
            
            # Queue callback
            try:
                callback_service = get_escalation_callback_service()
                print(f"[Discord] Got callback service: {callback_service}")
                callback_queued = await callback_service.queue_callback(reference_id)
                print(f"[Discord] queue_callback returned: {callback_queued}")
            except Exception as e:
                logger.warning(f"[Discord] Failed to queue callback: {e}", exc_info=True)
                callback_queued = False
            
            if not callback_queued:
                logger.warning(f"[Discord] Callback queue failed for {reference_id}")
            
            print(f"[Discord] Updating Discord embed status...")
            
            # Update Discord embed
            try:
                await self.update_escalation_status(
                    reference_id=reference_id,
                    status="RESOLVED",
                    callback_status="QUEUED",
                )
            except Exception as e:
                logger.error(f"[Discord] Failed to update escalation status: {e}", exc_info=True)
            
            print(f"[Discord] Sending success response...")
            
            # Send success message via followup
            try:
                success_msg = (
                    f"✅ **Escalation Resolved**\n"
                    f"**Reference ID:** `{reference_id}`\n"
                    f"**Status:** Resolved & Callback Queued\n"
                    f"**Adviser:** {interaction.user.mention}"
                )
                await interaction.followup.send(success_msg)
                logger.info(f"[Discord] Success message sent for {reference_id}")
            except Exception as e:
                logger.warning(f"[Discord] Failed to send success message: {e}")
                # Try to send at least an acknowledgment
                try:
                    await interaction.followup.send(f"✅ Escalation {reference_id} resolved successfully")
                except:
                    pass
            
            logger.info(
                f"[Discord] Escalation resolved successfully: {reference_id} "
                f"by {interaction.user.name}, callback queued"
            )
            print(f"[Discord] Resolution completed and user notified")
            
        
        except Exception as e:
            logger.error(f"[Discord] Error handling resolve command: {e}", exc_info=True)
            print(f"[_handle_resolve_command] ERROR: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass


# Global instance
_discord_service_instance: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get or create the global Discord service."""
    global _discord_service_instance
    if _discord_service_instance is None:
        _discord_service_instance = DiscordService()
    return _discord_service_instance
