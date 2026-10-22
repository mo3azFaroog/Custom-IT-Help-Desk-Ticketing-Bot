"""User-facing ticket commands."""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from .. import embeds
from ..bot import HelpDeskBot
from ..database import PRIORITIES

MAX_TITLE = 100
MAX_TEXT = 1000


def is_staff(member: discord.Member) -> bool:
    return member.guild_permissions.manage_messages


class Tickets(commands.Cog):
    """Create, view, reply to and close tickets."""

    def __init__(self, bot: HelpDeskBot) -> None:
        self.bot = bot

    async def _fetch(self, ctx: commands.Context, ticket_id: int):
        """Return the ticket if it exists and the author may access it, else reply and return None."""
        ticket = await asyncio.to_thread(self.bot.db.get_ticket, ctx.guild.id, ticket_id)
        if not ticket:
            await ctx.send(f"❌ Ticket #{ticket_id} not found.")
            return None
        if str(ctx.author.id) != ticket["created_by"] and not is_staff(ctx.author):
            await ctx.send("🚫 You can only access tickets you created.")
            return None
        return ticket

    @commands.command(name="create-ticket", aliases=["new", "ticket"])
    @commands.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def create_ticket(self, ctx: commands.Context, priority: str, *, details: str):
        """Create a ticket: !create-ticket <priority> <title> | <description>"""
        priority = priority.capitalize()
        if priority not in PRIORITIES:
            return await ctx.send(f"❌ Priority must be one of: {', '.join(PRIORITIES)}.")
        title, sep, description = details.partition("|")
        title, description = title.strip(), description.strip()
        if not sep or not title or not description:
            return await ctx.send(
                f"❌ Use the format: `{ctx.prefix}create-ticket <priority> <title> | <description>`"
            )
        if len(title) > MAX_TITLE or len(description) > MAX_TEXT:
            return await ctx.send(
                f"❌ Title max {MAX_TITLE} characters, description max {MAX_TEXT} characters."
            )

        ticket_id = await asyncio.to_thread(
            self.bot.db.create_ticket, ctx.guild.id, ctx.author.id, title, description, priority
        )
        ticket = await asyncio.to_thread(self.bot.db.get_ticket, ctx.guild.id, ticket_id)
        embed = embeds.ticket_embed(ticket, "🎫 Ticket Created —")
        embed.set_footer(text=f"Use {ctx.prefix}view-ticket {ticket_id} to see details")
        await ctx.send(embed=embed)
        await self.bot.log_event(
            ctx.guild, embeds.ticket_embed(ticket, f"🆕 New ticket by {ctx.author} —")
        )

    @commands.command(name="view-ticket", aliases=["view"])
    @commands.guild_only()
    async def view_ticket(self, ctx: commands.Context, ticket_id: int):
        """View a ticket: !view-ticket <id>"""
        ticket = await self._fetch(ctx, ticket_id)
        if ticket:
            await ctx.send(embed=embeds.ticket_embed(ticket))

    @commands.command(name="reply")
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def reply(self, ctx: commands.Context, ticket_id: int, *, message: str):
        """Reply to a ticket: !reply <id> <message>"""
        ticket = await self._fetch(ctx, ticket_id)
        if not ticket:
            return
        if ticket["status"] == "Closed":
            return await ctx.send(f"🔒 Ticket #{ticket_id} is closed and cannot be replied to.")
        if len(message) > MAX_TEXT:
            return await ctx.send(f"❌ Replies are limited to {MAX_TEXT} characters.")

        await asyncio.to_thread(self.bot.db.add_reply, ticket_id, ctx.author.id, message)
        embed = discord.Embed(
            title=f"💬 Reply to Ticket #{ticket_id}", description=message, color=0x9B59B6
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Use {ctx.prefix}history {ticket_id} to view all replies")
        await ctx.send(embed=embed)
        log_embed = embed.copy()
        log_embed.title = f"💬 {ctx.author} replied to ticket #{ticket_id}"
        await self.bot.log_event(ctx.guild, log_embed)

    @commands.command(name="history")
    @commands.guild_only()
    async def history(self, ctx: commands.Context, ticket_id: int):
        """Show a ticket's conversation: !history <id>"""
        ticket = await self._fetch(ctx, ticket_id)
        if not ticket:
            return
        replies = await asyncio.to_thread(self.bot.db.get_replies, ticket_id)
        if not replies:
            return await ctx.send(f"ℹ️ No replies yet for ticket #{ticket_id}.")

        shown = replies[-24:]  # Discord allows at most 25 embed fields
        embed = discord.Embed(
            title=f"📜 Ticket #{ticket_id} History",
            description=embeds.clip(f"**Subject:** {ticket['title']}", 4000),
            color=0xE67E22,
        )
        for r in shown:
            embed.add_field(
                name=f"#{r['id']} · {r['replied_at']} UTC",
                value=embeds.clip(f"<@{r['replied_by']}>: {r['message']}", 1024),
                inline=False,
            )
        if len(replies) > len(shown):
            embed.set_footer(text=f"Showing the latest {len(shown)} of {len(replies)} replies")
        await ctx.send(embed=embed)

    @commands.command(name="close")
    @commands.guild_only()
    async def close(self, ctx: commands.Context, ticket_id: int):
        """Close a ticket you created (staff can close any): !close <id>"""
        ticket = await self._fetch(ctx, ticket_id)
        if not ticket:
            return
        if ticket["status"] == "Closed":
            return await ctx.send(f"ℹ️ Ticket #{ticket_id} is already closed.")
        await asyncio.to_thread(self.bot.db.set_status, ctx.guild.id, ticket_id, "Closed")
        await ctx.send(f"✅ Ticket #{ticket_id} closed by {ctx.author.mention}.")
        await self.bot.log_event(
            ctx.guild,
            discord.Embed(
                title=f"🔒 Ticket #{ticket_id} closed",
                description=f"Closed by {ctx.author.mention}",
                color=0x95A5A6,
            ),
        )

    @commands.command(name="my-tickets", aliases=["mytickets"])
    @commands.guild_only()
    async def my_tickets(self, ctx: commands.Context):
        """List your most recent tickets: !my-tickets"""
        rows = await asyncio.to_thread(self.bot.db.list_tickets, ctx.guild.id, None, None, 50)
        mine = [t for t in rows if t["created_by"] == str(ctx.author.id)][:10]
        if not mine:
            return await ctx.send("ℹ️ You have no tickets yet.")
        lines = [
            f"{embeds.STATUS_EMOJI[t['status']]} **#{t['id']}** · {t['priority']} · "
            f"{embeds.clip(t['title'], 60)}"
            for t in mine
        ]
        await ctx.send(embed=discord.Embed(title="🎫 Your tickets", description="\n".join(lines), color=embeds.BRAND_COLOR))


async def setup(bot: HelpDeskBot) -> None:
    await bot.add_cog(Tickets(bot))

