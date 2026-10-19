
"""THRONE — SQLite database layer.

Python 3.12+
Dependency: aiosqlite
"""

from __future__ import annotations

import os
import json
import time
import logging
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/throne.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'uz',
    title TEXT NOT NULL DEFAULT 'Oddiy fuqaro',
    level INTEGER NOT NULL DEFAULT 1,
    experience INTEGER NOT NULL DEFAULT 0,
    gold INTEGER NOT NULL DEFAULT 0,
    coin INTEGER NOT NULL DEFAULT 0,
    diamonds INTEGER NOT NULL DEFAULT 0,
    elite_pass INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0,
    games_won INTEGER NOT NULL DEFAULT 0,
    games_lost INTEGER NOT NULL DEFAULT 0,
    duels_played INTEGER NOT NULL DEFAULT 0,
    duels_won INTEGER NOT NULL DEFAULT 0,
    duels_lost INTEGER NOT NULL DEFAULT 0,
    clan_id INTEGER,
    partner_id INTEGER,
    favorite_role TEXT,
    avatar TEXT,
    created_at INTEGER NOT NULL,
    last_active INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    phase TEXT NOT NULL DEFAULT 'LOBBY',
    round_number INTEGER NOT NULL DEFAULT 0,
    winner TEXT,
    started_at INTEGER,
    finished_at INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_games_chat_phase
ON games(chat_id, phase);

CREATE TABLE IF NOT EXISTS game_players (
    game_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    role_id TEXT,
    team TEXT,
    alive INTEGER NOT NULL DEFAULT 1,
    joined_at INTEGER NOT NULL,
    eliminated_at INTEGER,
    elimination_reason TEXT,
    PRIMARY KEY (game_id, user_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_players_user
ON game_players(user_id);

CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    round_number INTEGER NOT NULL DEFAULT 0,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}',
    created_at INTEGER NOT NULL,
    FOREIGN KEY (game_id) REFERENCES games(game_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    currency TEXT NOT NULL,
    amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    reference_id TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievements (
    user_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, achievement_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    acquired_at INTEGER NOT NULL,
    UNIQUE (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clans (
    clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL UNIQUE,
    rank TEXT NOT NULL DEFAULT 'MEMBER',
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (clan_id, user_id),
    FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    settings_json TEXT NOT NULL DEFAULT '{}',
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);
"""


class Database:
    """Asynchronous SQLite access layer for THRONE."""

    def __init__(self, path: str | Path | None = None):
        self.path = str(path or DATABASE_PATH)
        self._initialized = False

    async def connect(self) -> aiosqlite.Connection:
        """Create a database connection."""
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")
        return db

    async def initialize(self) -> None:
        """Create tables and indexes if they do not exist."""
        async with await self.connect() as db:
            await db.executescript(SCHEMA)
            await db.commit()

        self._initialized = True
        logger.info("THRONE database initialized: %s", self.path)

    async def execute(
        self,
        query: str,
        parameters: tuple | dict = (),
    ) -> int:
        async with await self.connect() as db:
            cursor = await db.execute(query, parameters)
            await db.commit()
            return cursor.lastrowid or cursor.rowcount

    async def fetchone(
        self,
        query: str,
        parameters: tuple | dict = (),
    ) -> dict[str, Any] | None:
        async with await self.connect() as db:
            cursor = await db.execute(query, parameters)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(
        self,
        query: str,
        parameters: tuple | dict = (),
    ) -> list[dict[str, Any]]:
        async with await self.connect() as db:
            cursor = await db.execute(query, parameters)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )

    async def create_user(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        now = int(time.time())

        await self.execute(
            """
            INSERT INTO users (
                user_id, username, full_name, created_at, last_active
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = excluded.last_active
            """,
            (user_id, username, full_name, now, now),
        )

        allowed = {
            "language", "title", "level", "experience",
            "gold", "coin", "diamonds", "elite_pass",
            "favorite_role", "avatar",
        }
        updates = {key: value for key, value in fields.items()
                   if key in allowed}

        if updates:
            await self.update_user(user_id, **updates)

        user = await self.get_user(user_id)
        if user is None:
            raise RuntimeError("Foydalanuvchi bazaga yozilmadi.")
        return user

    async def update_user(self, user_id: int, **fields: Any) -> bool:
        allowed = {
            "username", "full_name", "language", "title",
            "level", "experience", "gold", "coin", "diamonds",
            "elite_pass", "games_played", "games_won", "games_lost",
            "duels_played", "duels_won", "duels_lost", "clan_id",
            "partner_id", "favorite_role", "avatar", "last_active",
        }
        updates = {key: value for key, value in fields.items()
                   if key in allowed}

        if not updates:
            return False

        updates["last_active"] = int(time.time())
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [user_id]

        changed = await self.execute(
            f"UPDATE users SET {assignments} WHERE user_id = ?",
            tuple(values),
        )
        return changed > 0

    async def add_currency(
        self,
        user_id: int,
        currency: str,
        amount: int,
        reason: str,
        reference_id: str | None = None,
    ) -> int:
        """Change a balance and record the transaction atomically."""
        columns = {
            "gold": "gold",
            "coin": "coin",
            "diamonds": "diamonds",
        }
        column = columns.get(currency.lower())
        if column is None:
            raise ValueError("Noma'lum valyuta turi.")

        if amount == 0:
            user = await self.get_user(user_id)
            if user is None:
                raise ValueError("Foydalanuvchi topilmadi.")
            return int(user[column])

        async with await self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            try:
                cursor = await db.execute(
                    f"SELECT {column} FROM users WHERE user_id = ?",
                    (user_id,),
                )
                row = await cursor.fetchone()
                if row is None:
                    raise ValueError("Foydalanuvchi topilmadi.")

                new_balance = int(row[column]) + amount
                if new_balance < 0:
                    raise ValueError("Mablag' yetarli emas.")

                await db.execute(
                    f"UPDATE users SET {column} = ?, last_active = ? "
                    "WHERE user_id = ?",
                    (new_balance, int(time.time()), user_id),
                )
                await db.execute(
                    """
                    INSERT INTO transactions (
                        user_id, currency, amount, reason,
                        reference_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id, currency.lower(), amount, reason,
                        reference_id, int(time.time()),
                    ),
                )
                await db.commit()
                return new_balance
            except Exception:
                await db.rollback()
                raise

    async def create_game(
        self,
        game_id: str,
        chat_id: int,
        creator_id: int,
        phase: str = "LOBBY",
    ) -> None:
        now = int(time.time())
        await self.execute(
            """
            INSERT INTO games (
                game_id, chat_id, creator_id, phase,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (game_id, chat_id, creator_id, phase, now, now),
        )

    async def get_game(self, game_id: str) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,),
        )

    async def update_game(self, game_id: str, **fields: Any) -> bool:
        allowed = {
            "phase", "round_number", "winner",
            "started_at", "finished_at",
        }
        updates = {key: value for key, value in fields.items()
                   if key in allowed}
        if not updates:
            return False

        updates["updated_at"] = int(time.time())
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [game_id]

        changed = await self.execute(
            f"UPDATE games SET {assignments} WHERE game_id = ?",
            tuple(values),
        )
        return changed > 0

    async def add_game_player(
        self,
        game_id: str,
        user_id: int,
        role_id: str | None = None,
        team: str | None = None,
    ) -> None:
        now = int(time.time())
        async with await self.connect() as db:
            await db.execute(
                """
                INSERT INTO game_players (
                    game_id, user_id, role_id, team, joined_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(game_id, user_id) DO UPDATE SET
                    role_id = excluded.role_id,
                    team = excluded.team
                """,
                (game_id, user_id, role_id, team, now),
            )
            await db.commit()

    async def get_game_players(
        self,
        game_id: str,
        alive_only: bool = False,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM game_players WHERE game_id = ?"
        if alive_only:
            query += " AND alive = 1"
        query += " ORDER BY joined_at"
        return await self.fetchall(query, (game_id,))

    async def eliminate_game_player(
        self,
        game_id: str,
        user_id: int,
        reason: str = "",
    ) -> bool:
        changed = await self.execute(
            """
            UPDATE game_players
            SET alive = 0, eliminated_at = ?, elimination_reason = ?
            WHERE game_id = ? AND user_id = ? AND alive = 1
            """,
            (int(time.time()), reason, game_id, user_id),
        )
        return changed > 0

    async def add_history(
        self,
        game_id: str,
        event_type: str,
        description: str,
        round_number: int = 0,
        data: dict[str, Any] | None = None,
    ) -> int:
        return await self.execute(
            """
            INSERT INTO game_history (
                game_id, round_number, event_type,
                description, data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                round_number,
                event_type,
                description,
                json.dumps(data or {}, ensure_ascii=False),
                int(time.time()),
            ),
        )

    async def get_game_history(
        self,
        game_id: str,
    ) -> list[dict[str, Any]]:
        history = await self.fetchall(
            """
            SELECT * FROM game_history
            WHERE game_id = ?
            ORDER BY id
            """,
            (game_id,),
        )
        for event in history:
            try:
                event["data"] = json.loads(event.pop("data_json", "{}"))
            except (TypeError, json.JSONDecodeError):
                event["data"] = {}
        return history

    async def add_achievement(
        self,
        user_id: int,
        achievement_id: str,
    ) -> bool:
        try:
            await self.execute(
                """
                INSERT INTO achievements (user_id, achievement_id, unlocked_at)
                VALUES (?, ?, ?)
                """,
                (user_id, achievement_id, int(time.time())),
            )
            return True
        except aiosqlite.IntegrityError:
            return False

    async def get_achievements(
        self,
        user_id: int,
    ) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY unlocked_at",
            (user_id,),
        )

    async def add_inventory_item(
        self,
        user_id: int,
        item_id: str,
        quantity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if quantity <= 0:
            raise ValueError("Miqdor musbat bo'lishi kerak.")

        await self.execute(
            """
            INSERT INTO inventory (
                user_id, item_id, quantity, metadata_json, acquired_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                quantity = inventory.quantity + excluded.quantity,
                metadata_json = excluded.metadata_json
            """,
            (
                user_id,
                item_id,
                quantity,
                json.dumps(metadata or {}, ensure_ascii=False),
                int(time.time()),
            ),
        )

    async def get_inventory(
        self,
        user_id: int,
    ) -> list[dict[str, Any]]:
        items = await self.fetchall(
            "SELECT * FROM inventory WHERE user_id = ? ORDER BY acquired_at",
            (user_id,),
        )
        for item in items:
            try:
                item["metadata"] = json.loads(
                    item.pop("metadata_json", "{}")
                )
            except (TypeError, json.JSONDecodeError):
                item["metadata"] = {}
        return items

    async def get_leaderboard(
        self,
        limit: int = 10,
        order_by: str = "games_won",
    ) -> list[dict[str, Any]]:
        allowed = {
            "games_won", "games_played", "level",
            "experience", "gold", "coin", "diamonds",
        }
        if order_by not in allowed:
            order_by = "games_won"

        limit = max(1, min(int(limit), 100))
        return await self.fetchall(
            f"""
            SELECT user_id, full_name, username, level,
                   experience, games_played, games_won,
                   gold, coin, diamonds
            FROM users
            ORDER BY {order_by} DESC, user_id ASC
            LIMIT ?
            """,
            (limit,),
        )

    async def set_user_settings(
        self,
        user_id: int,
        settings: dict[str, Any],
    ) -> None:
        await self.execute(
            """
            INSERT INTO user_settings (user_id, settings_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                json.dumps(settings, ensure_ascii=False),
                int(time.time()),
            ),
        )

    async def get_user_settings(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        row = await self.fetchone(
            "SELECT settings_json FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        if not row:
            return {}
        try:
            return json.loads(row["settings_json"])
        except (TypeError, json.JSONDecodeError):
            return {}

    async def close(self) -> None:
        """Connections are opened per operation; nothing persistent to close."""
        return None


# Shared instance for modules that prefer a single imported database object.
db = Database()


async def init_db() -> None:
    """Compatibility helper for application startup."""
    await db.initialize()


async def get_user(user_id: int) -> dict[str, Any] | None:
    return await db.get_user(user_id)


async def create_user(
    user_id: int,
    full_name: str,
    username: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    return await db.create_user(user_id, full_name, username, **fields)


async def update_user(user_id: int, **fields: Any) -> bool:
    return await db.update_user(user_id, **fields)


async def add_currency(
    user_id: int,
    currency: str,
    amount: int,
    reason: str,
    reference_id: str | None = None,
) -> int:
    return await db.add_currency(
        user_id, currency, amount, reason, reference_id
    )


async def close_db() -> None:
    await db.close()
            
