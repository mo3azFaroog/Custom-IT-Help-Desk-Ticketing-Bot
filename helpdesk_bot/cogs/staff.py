"""Staff-only commands (require the Manage Messages permission)."""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from .. import embeds
from ..bot import HelpDeskBot
from ..database import STATUSES


class Staff(commands.Cog):
    """Ticket triage, assignment and configuration."""

    def __init__(self, bot: HelpDeskBot) -> None:
        self.bot = bot

    @commands.command(name="update-status", aliases=["status"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def update_status(self, ctx: commands.Context, ticket_id: int, *, status: str):
        """Change a ticket's status: !update-status <id> <status>"""
        normalized = status.strip().title()
        if normalized not in STATUSES:
            return await ctx.send(f"❌ Invalid status. Use: {', '.join(STATUSES)}.")
        ok = await asyncio.to_thread(self.bot.db.set_status, ctx.guild.id, ticket_id, normalized)
        if not ok:
            return await ctx.send(f"❌ Ticket #{ticket_id} not found.")

        embed = discord.Embed(
            title="✅ Ticket Status Updated",
            description=f"Ticket #{ticket_id} is now **{normalized}**",
            color=0x2ECC71,
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        await self.bot.log_event(ctx.guild, embed)

    @commands.command(name="assign")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def assign(self, ctx: commands.Context, ticket_id: int, member: discord.Member):
        """Assign a ticket to a team member: !assign <id> @member"""
        ok = await asyncio.to_thread(self.bot.db.assign, ctx.guild.id, ticket_id, member.id)
        if not ok:
            return await ctx.send(f"❌ Ticket #{ticket_id} not found.")
        embed = discord.Embed(
            title="👤 Ticket Assigned",
            description=f"Ticket #{ticket_id} assigned to {member.mention} by {ctx.author.mention}",
            color=embeds.BRAND_COLOR,
        )
        await ctx.send(embed=embed)
        await self.bot.log_event(ctx.guild, embed)

    @commands.command(name="tickets", aliases=["list"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def tickets(self, ctx: commands.Context, *, status: str | None = None):
        """List recent tickets, optionally by status: !tickets [status]"""
        normalized = status.strip().title() if status else None
        if normalized and normalized not in STATUSES:
            return await ctx.send(f"❌ Invalid status. Use: {', '.join(STATUSES)}.")
        rows = await asyncio.to_thread(self.bot.db.list_tickets, ctx.guild.id, normalized, None, 15)
        if not rows:
            return await ctx.send("ℹ️ No tickets found.")
        lines = [
            f"{embeds.STATUS_EMOJI[t['status']]} **#{t['id']}** · {t['priority']} · "
            f"{embeds.clip(t['title'], 50)} — <@{t['created_by']}>"
            for t in rows
        ]
        title = f"🎫 {normalized} tickets" if normalized else "🎫 Recent tickets"
        await ctx.send(embed=discord.Embed(title=title, description="\n".join(lines), color=embeds.BRAND_COLOR))

    @commands.command(name="helpdesk-stats", aliases=["stats"])
    @commands.guild_only()
    async def stats(self, ctx: commands.Context):
        """Show ticket statistics: !helpdesk-stats"""
        counts = await asyncio.to_thread(self.bot.db.stats, ctx.guild.id)
        embed = discord.Embed(title="📊 Help Desk Statistics", color=0x9B59B6)
        embed.add_field(name="Total", value=str(sum(counts.values())), inline=True)
        for status in STATUSES:
            embed.add_field(name=f"{embeds.STATUS_EMOJI[status]} {status}", value=str(counts[status]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="setlogchannel")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the audit-log channel: !setlogchannel #channel"""
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links):
            return await ctx.send(f"❌ I need Send Messages and Embed Links in {channel.mention}.")
        await asyncio.to_thread(self.bot.db.set_setting, ctx.guild.id, "log_channel_id", str(channel.id))
        await ctx.send(f"✅ Log channel set to {channel.mention}.")

    @commands.command(name="getlogchannel")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def get_log_channel(self, ctx: commands.Context):
        """Show the current log channel: !getlogchannel"""
        raw = await asyncio.to_thread(self.bot.db.get_setting, ctx.guild.id, "log_channel_id")
        if raw and ctx.guild.get_channel(int(raw)):
            await ctx.send(f"📝 Log channel: <#{raw}>")
        else:
            await ctx.send(f"ℹ️ No log channel set. Use `{ctx.prefix}setlogchannel #channel`.")


async def setup(bot: HelpDeskBot) -> None:
    await bot.add_cog(Staff(bot))
