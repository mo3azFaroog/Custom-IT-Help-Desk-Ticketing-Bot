"""Runtime configuration, loaded from environment variables / a ``.env`` file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    token: str
    prefix: str
    db_path: str


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Copy .env.example to .env and add your bot token."
        )
    return Config(
        token=token,
        prefix=os.getenv("BOT_PREFIX", "!"),
        db_path=os.getenv("DATABASE_PATH", "help_desk.db"),
    )
