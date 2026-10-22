"""SQLite data-access layer for the IT Help Desk bot.

All functions open a short-lived connection, so they are safe to call from
``asyncio.to_thread`` and never leave a connection dangling on errors.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

PRIORITIES = ("Low", "Medium", "High", "Critical")
STATUSES = ("Open", "In Progress", "Resolved", "Closed")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    priority    TEXT NOT NULL CHECK (priority IN ('Low','Medium','High','Critical')),
    status      TEXT NOT NULL DEFAULT 'Open'
                CHECK (status IN ('Open','In Progress','Resolved','Closed')),
    created_by  TEXT NOT NULL,
    assigned_to TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS replies (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL REFERENCES tickets (id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    replied_by TEXT NOT NULL,
    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_settings (
    guild_id TEXT NOT NULL,
    key      TEXT NOT NULL,
    value    TEXT,
    PRIMARY KEY (guild_id, key)
);

CREATE INDEX IF NOT EXISTS idx_tickets_guild_status ON tickets (guild_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_by   ON tickets (created_by);
CREATE INDEX IF NOT EXISTS idx_replies_ticket_id    ON replies (ticket_id);
"""


class Database:
    """Thin wrapper around a SQLite file."""

    def __init__(self, path: str) -> None:
        self.path = path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self) -> None:
        """Create tables and indexes if they do not exist yet."""
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ------------------------------------------------------------ tickets
    def create_ticket(
        self, guild_id: int, user_id: int, title: str, description: str, priority: str
    ) -> int:
        if priority not in PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO tickets (guild_id, title, description, priority, created_by) "
                "VALUES (?, ?, ?, ?, ?)",
                (str(guild_id), title, description, priority, str(user_id)),
            )
            return int(cur.lastrowid)

    def get_ticket(self, guild_id: int, ticket_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE id = ? AND guild_id = ?",
                (ticket_id, str(guild_id)),
            ).fetchone()
        return dict(row) if row else None

    def list_tickets(
        self,
        guild_id: int,
        status: str | None = None,
        assigned_to: int | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM tickets WHERE guild_id = ?"
        params: list[Any] = [str(guild_id)]
        if status:
            query += " AND status = ?"
            params.append(status)
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(str(assigned_to))
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params)]

    def set_status(self, guild_id: int, ticket_id: int, status: str) -> bool:
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}")
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND guild_id = ?",
                (status, ticket_id, str(guild_id)),
            )
            return cur.rowcount > 0

    def assign(self, guild_id: int, ticket_id: int, staff_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE tickets SET assigned_to = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND guild_id = ?",
                (str(staff_id), ticket_id, str(guild_id)),
            )
            return cur.rowcount > 0

    def stats(self, guild_id: int) -> dict[str, int]:
        counts = {s: 0 for s in STATUSES}
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT status, COUNT(*) AS n FROM tickets WHERE guild_id = ? GROUP BY status",
                (str(guild_id),),
            ):
                counts[row["status"]] = row["n"]
        return counts

    # ------------------------------------------------------------ replies
    def add_reply(self, ticket_id: int, user_id: int, message: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO replies (ticket_id, message, replied_by) VALUES (?, ?, ?)",
                (ticket_id, message, str(user_id)),
            )
            conn.execute(
                "UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (ticket_id,),
            )
            return int(cur.lastrowid)

    def get_replies(self, ticket_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM replies WHERE ticket_id = ? ORDER BY replied_at, id",
                (ticket_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ----------------------------------------------------------- settings
    def set_setting(self, guild_id: int, key: str, value: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO bot_settings (guild_id, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT (guild_id, key) DO UPDATE SET value = excluded.value",
                (str(guild_id), key, value),
            )

    def get_setting(self, guild_id: int, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM bot_settings WHERE guild_id = ? AND key = ?",
                (str(guild_id), key),
            ).fetchone()
        return row["value"] if row else None
