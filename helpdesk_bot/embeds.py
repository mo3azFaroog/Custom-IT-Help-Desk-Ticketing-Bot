"""Embed builders shared by the cogs."""

from __future__ import annotations

from typing import Any

import discord

PRIORITY_COLORS = {
    "Low": 0x2ECC71,
    "Medium": 0xF1C40F,
    "High": 0xE67E22,
    "Critical": 0xE74C3C,
}
STATUS_EMOJI = {
    "Open": "🟢",
    "In Progress": "🟡",
    "Resolved": "🔵",
    "Closed": "⚫",
}
BRAND_COLOR = 0x3498DB


def clip(text: str, limit: int) -> str:
    """Trim text to Discord's embed limits."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def ticket_embed(ticket: dict[str, Any], title_prefix: str = "🎫 Ticket") -> discord.Embed:
    embed = discord.Embed(
        title=f"{title_prefix} #{ticket['id']}",
        description=clip(f"**{ticket['title']}**\n{ticket['description']}", 4000),
        color=PRIORITY_COLORS.get(ticket["priority"], BRAND_COLOR),
    )
    embed.add_field(name="Priority", value=ticket["priority"], inline=True)
    embed.add_field(
        name="Status",
        value=f"{STATUS_EMOJI.get(ticket['status'], '')} {ticket['status']}",
        inline=True,
    )
    assignee = f"<@{ticket['assigned_to']}>" if ticket.get("assigned_to") else "Unassigned"
    embed.add_field(name="Assigned to", value=assignee, inline=True)
    embed.add_field(name="Created by", value=f"<@{ticket['created_by']}>", inline=True)
    embed.add_field(name="Created (UTC)", value=ticket["created_at"], inline=True)
    embed.add_field(name="Updated (UTC)", value=ticket["updated_at"], inline=True)
    return embed
