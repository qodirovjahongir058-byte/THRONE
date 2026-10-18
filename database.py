
import os
import aiosqlite

from config import (
    DATABASE_PATH,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


# ==================================================
# MA'LUMOTLAR BAZASI
# ==================================================

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'uz',
    gold INTEGER NOT NULL DEFAULT 0 CHECK (gold >= 0),
    coin INTEGER NOT NULL DEFAULT 0 CHECK (coin >= 0),
    diamond INTEGER NOT NULL DEFAULT 0 CHECK (diamond >= 0),
    elite_pass INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'LOBBY',
    phase TEXT NOT NULL DEFAULT 'LOBBY',
    round_number INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_games_chat_status
ON games (chat_id, status);

CREATE TABLE IF NOT EXISTS game_players (
    game_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id TEXT,
    team TEXT,
    is_alive INTEGER NOT NULL DEFAULT 1,
    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    eliminated_at TEXT,
    PRIMARY KEY (game_id, user_id),
    FOREIGN KEY (game_id)
        REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_players_user
ON game_players (user_id);

CREATE TABLE IF NOT EXISTS player_stats (
    user_id INTEGER PRIMARY KEY,
    games_played INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);
"""


async def init_db() -> None:
    """Bazani va kerakli jadvallarni yaratadi."""
    folder = os.path.dirname(DATABASE_PATH)

    if folder:
        os.makedirs(folder, exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript(SCHEMA)
        await db.commit()


async def register_user(
    user_id: int,
    username: str | None,
    first_name: str,
    language: str | None = None,
) -> None:
    """Foydalanuvchini ro'yxatdan o'tkazadi yoki yangilaydi."""
    selected_language = (
        language
        if language in SUPPORTED_LANGUAGES
        else DEFAULT_LANGUAGE
    )

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id, username, first_name, language
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_active = CURRENT_TIMESTAMP
            """,
            (user_id, username, first_name, selected_language),
        )

        await db.execute(
            """
            INSERT OR IGNORE INTO player_stats (user_id)
            VALUES (?)
            """,
            (user_id,),
        )

        await db.commit()


async def get_user(user_id: int) -> dict | None:
    """Foydalanuvchi ma'lumotlarini qaytaradi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        return dict(row) if row else None


async def set_language(
    user_id: int,
    language: str,
) -> bool:
    """Tilni o'zgartiradi. Til noto'g'ri bo'lsa False qaytaradi."""
    if language not in SUPPORTED_LANGUAGES:
        return False

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE users
            SET language = ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (language, user_id),
        )
        await db.commit()

        return cursor.rowcount > 0


async def update_activity(user_id: int) -> None:
    """Foydalanuvchining oxirgi faollik vaqtini yangilaydi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            UPDATE users
            SET last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        await db.commit()


async def get_balance(user_id: int) -> dict | None:
    """Gold, Coin va Diamond balanslarini qaytaradi."""
    user = await get_user(user_id)

    if user is None:
        return None

    return {
        "gold": user["gold"],
        "coin": user["coin"],
        "diamond": user["diamond"],
    }
    
