"""Custom help command."""

from __future__ import annotations

import discord
from discord.ext import commands

from .. import embeds
from ..bot import HelpDeskBot
from ..database import PRIORITIES, STATUSES


class Help(commands.Cog):
    def __init__(self, bot: HelpDeskBot) -> None:
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx: commands.Context):
        """Show all commands."""
        p = ctx.prefix
        embed = discord.Embed(
            title="📚 IT Help Desk — Commands",
            description=f"Priorities: {', '.join(PRIORITIES)}",
            color=embeds.BRAND_COLOR,
        )
        embed.add_field(
            name="🎫 Tickets",
            value=(
                f"`{p}create-ticket <priority> <title> | <description>`\n"
                f"`{p}view-ticket <id>` · `{p}reply <id> <message>`\n"
                f"`{p}history <id>` · `{p}close <id>` · `{p}my-tickets`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Staff (Manage Messages)",
            value=(
                f"`{p}update-status <id> <status>` — {', '.join(STATUSES)}\n"
                f"`{p}assign <id> @member` · `{p}tickets [status]`\n"
                f"`{p}getlogchannel`"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ Admin (Manage Server)",
            value=f"`{p}setlogchannel #channel`",
            inline=False,
        )
        embed.add_field(name="📊 Stats", value=f"`{p}helpdesk-stats`", inline=False)
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: HelpDeskBot) -> None:
    await bot.add_cog(Help(bot))
