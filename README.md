# IT Help Desk Ticketing Bot

[![CI](https://github.com/mo3azFaroog/Custom-IT-Help-Desk-Ticketing-Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/mo3azFaroog/Custom-IT-Help-Desk-Ticketing-Bot/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2)
![License](https://img.shields.io/badge/license-MIT-green)

A Discord bot that turns a server into a lightweight IT support desk: members open tickets, staff triage and assign them, and every action is written to an audit-log channel. Data is stored in SQLite, so there is nothing else to install or host.

## Features

- Ticket lifecycle: create, view, reply, history, close
- Priorities (`Low`, `Medium`, `High`, `Critical`) with colour-coded embeds
- Statuses: `Open`, `In Progress`, `Resolved`, `Closed`
- Staff tools: update status, assign to a team member, list/filter tickets, statistics
- Per-server data and per-server audit-log channel (safe to add to several servers)
- Access control: members see only their own tickets; staff see all
- Input validation, cooldowns, and friendly error messages
- Unit-tested data layer and CI (lint + tests)

## Quick start

1. Create a bot at the [Discord Developer Portal](https://discord.com/developers/applications), enable the **Message Content Intent**, and invite it with the `bot` scope plus *Send Messages* and *Embed Links*.
2. Install and configure:

   ```bash
   git clone https://github.com/mo3azFaroog/Custom-IT-Help-Desk-Ticketing-Bot.git
   cd Custom-IT-Help-Desk-Ticketing-Bot
   python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env                               # then put your token in .env
   ```

3. Run: `python -m helpdesk_bot`

> **Never commit your bot token.** It lives only in `.env`, which is git-ignored. If a token was ever exposed, reset it in the Developer Portal.

## Commands

| Command | Who | Description |
|---|---|---|
| `!create-ticket <priority> <title> \| <description>` | Everyone | Open a ticket |
| `!view-ticket <id>` | Owner / staff | Show ticket details |
| `!reply <id> <message>` | Owner / staff | Add a reply |
| `!history <id>` | Owner / staff | Show the conversation |
| `!close <id>` | Owner / staff | Close a ticket |
| `!my-tickets` | Everyone | Your recent tickets |
| `!update-status <id> <status>` | Staff | Change status |
| `!assign <id> @member` | Staff | Assign a ticket |
| `!tickets [status]` | Staff | List recent tickets |
| `!getlogchannel` | Staff | Show log channel |
| `!setlogchannel #channel` | Manage Server | Set audit-log channel |
| `!helpdesk-stats` | Everyone | Ticket counts by status |
| `!help` | Everyone | Command list |

"Staff" means the **Manage Messages** permission.

Example: `!create-ticket high VPN won't connect | Timeout since this morning on the office Wi-Fi`

## Project layout

```
helpdesk_bot/
├── __main__.py     # entry point (python -m helpdesk_bot)
├── bot.py          # bot class, audit logging, error handling
├── config.py       # environment configuration
├── database.py     # SQLite data layer
├── embeds.py       # embed helpers
└── cogs/           # tickets.py, staff.py, help.py
tests/              # pytest suite for the data layer
```

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Upgrading from v1

v2 uses a new schema (per-server tickets, constraints, `bot_settings`). The old `help_desk.db` is not migrated automatically; start with a fresh file (default `help_desk.db`) or set `DATABASE_PATH`.

## Roadmap

Ticket categories, search, auto-escalation by priority, slash commands, web dashboard.

## License

MIT
