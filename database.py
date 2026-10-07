from __future__ import annotations

from pathlib import Path

import aiosqlite

from config import DATABASE_PATH


async def init_database() -> None:
    """Create the database directory and initialize SQLite."""
    database_path = Path(DATABASE_PATH)

    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(database_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_games_chat_id
            ON games(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_games_chat_status
            ON games(chat_id, status)
            """
        )

        await db.commit()


async def get_connection() -> aiosqlite.Connection:
    """Return a configured SQLite connection."""
    database_path = Path(DATABASE_PATH)

    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(database_path)

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 5000")

    return db
