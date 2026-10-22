"""Bot class: wiring, cog loading, audit logging and global error handling."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from .config import Config
from .database import Database

log = logging.getLogger("helpdesk")

EXTENSIONS = (
    "helpdesk_bot.cogs.tickets",
    "helpdesk_bot.cogs.staff",
    "helpdesk_bot.cogs.help",
)


class HelpDeskBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # required for prefix commands
        super().__init__(command_prefix=config.prefix, intents=intents, help_command=None)
        self.config = config
        self.db = Database(config.db_path)

    async def setup_hook(self) -> None:
        self.db.init()
        for ext in EXTENSIONS:
            await self.load_extension(ext)
        log.info("Loaded %d extensions", len(EXTENSIONS))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%s) in %d guild(s)", self.user, self.user.id, len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=f"{self.config.prefix}help"
            )
        )

    async def log_event(self, guild: discord.Guild, embed: discord.Embed) -> None:
        """Post an audit embed to the guild's configured log channel, if any."""
        raw = await asyncio.to_thread(self.db.get_setting, guild.id, "log_channel_id")
        if not raw:
            return
        channel: discord.abc.GuildChannel | None = guild.get_channel(int(raw))
        if not isinstance(channel, discord.abc.Messageable):
            return
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            log.warning("Could not write to log channel %s: %s", raw, exc)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            error = error.original  # type: ignore[assignment]

        prefix = self.config.prefix
        usage = f"`{prefix}{ctx.command.qualified_name} {ctx.command.signature}`" if ctx.command else ""

        if isinstance(error, commands.MissingRequiredArgument):
            msg = f"❌ Missing argument `{error.param.name}`. Usage: {usage}"
        elif isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            msg = f"❌ Invalid argument. Usage: {usage}"
        elif isinstance(error, commands.MissingPermissions):
            msg = "🚫 You need staff permissions (Manage Messages) to use this command."
        elif isinstance(error, commands.NoPrivateMessage):
            msg = "🚫 This command can only be used in a server."
        elif isinstance(error, commands.CommandOnCooldown):
            msg = f"⏳ Slow down! Try again in {error.retry_after:.0f}s."
        else:
            log.exception("Unhandled error in command %s", ctx.command, exc_info=error)
            msg = "❌ Something went wrong. Please try again later."
        await ctx.send(msg)
