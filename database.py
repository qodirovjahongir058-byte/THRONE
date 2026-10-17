from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from config import DATABASE_PATH

logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi manzili
DB_PATH = DATABASE_PATH


# =========================================================
# DATABASE CONNECTION
# =========================================================

async def _connect() -> aiosqlite.Connection:
    """
    Ma'lumotlar bazasiga yangi asinxron ulanish ochadi.
    Foreign key va SQLite kutish vaqtini sozlaydi.
    """
    if DB_PATH != ":memory:":
        Path(DB_PATH).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    db = await aiosqlite.connect(DB_PATH)

    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 5000")

    return db


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """
    Ma'lumotlar bazasiga xavfsiz ulanish konteksti.

    Foydalanish:
        async with get_db() as db:
            cursor = await db.execute("SELECT 1")
    """
    db = await _connect()

    try:
        yield db
    finally:
        await db.close()
        # =========================================================
# DATABASE INITIALIZATION
# =========================================================

async def init_db() -> None:
    """
    THRONE uchun boshlang'ich jadvallarni yaratadi.

    Mavjud jadvallarni o'chirmaydi.
    Mavjud foydalanuvchi ma'lumotlarini saqlab qoladi.
    """
    db = await _connect()

    try:
        # WAL rejimi bir nechta o'qish operatsiyasiga yordam beradi.
        await db.execute("PRAGMA journal_mode = WAL")

        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'uz',

                gold INTEGER NOT NULL DEFAULT 0
                    CHECK (gold >= 0),

                coin INTEGER NOT NULL DEFAULT 0
                    CHECK (coin >= 0),

                diamond INTEGER NOT NULL DEFAULT 0
                    CHECK (diamond >= 0),

                elite_pass_until TEXT,

                is_banned INTEGER NOT NULL DEFAULT 0
                    CHECK (is_banned IN (0, 1)),

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_active_at TEXT
            );

            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'LOBBY',
                phase TEXT NOT NULL DEFAULT 'LOBBY',

                round_number INTEGER NOT NULL DEFAULT 0,
                night_number INTEGER NOT NULL DEFAULT 0,

                state_json TEXT NOT NULL DEFAULT '{}',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_games_chat_status
                ON games(chat_id, status);

            CREATE TABLE IF NOT EXISTS game_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                role_key TEXT,
                faction TEXT,

                is_alive INTEGER NOT NULL DEFAULT 1
                    CHECK (is_alive IN (0, 1)),

                is_connected INTEGER NOT NULL DEFAULT 1
                    CHECK (is_connected IN (0, 1)),

                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                eliminated_at TEXT,

                FOREIGN KEY (game_id)
                    REFERENCES games(game_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE RESTRICT,

                UNIQUE (game_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_game_players_user
                ON game_players(user_id);

            CREATE INDEX IF NOT EXISTS idx_game_players_game_alive
                ON game_players(game_id, is_alive);

            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                currency TEXT NOT NULL,

                amount INTEGER NOT NULL,
                balance_after INTEGER,

                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_user
                ON transactions(user_id, created_at);

            CREATE TABLE IF NOT EXISTS families (
                family_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                owner_id INTEGER NOT NULL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (owner_id)
                    REFERENCES users(user_id)
                    ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS family_members (
                family_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                family_role TEXT NOT NULL DEFAULT 'MEMBER',
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (family_id, user_id),

                FOREIGN KEY (family_id)
                    REFERENCES families(family_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_family_members_user
                ON family_members(user_id);

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,

                notifications_enabled INTEGER NOT NULL DEFAULT 1
                    CHECK (notifications_enabled IN (0, 1)),

                private_messages_enabled INTEGER NOT NULL DEFAULT 1
                    CHECK (private_messages_enabled IN (0, 1)),

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_activity_log_user
                ON activity_log(user_id, created_at);
            """
    )
           # Boshlang'ich sxema versiyasini qayd etamiz.
        cursor = await db.execute(
            "SELECT COUNT(*) FROM schema_version"
        )
        row = await cursor.fetchone()

        if row is not None and row[0] == 0:
            await db.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (1,),
            )

        await db.commit()

        logger.info("THRONE ma'lumotlar bazasi tayyor.")

    except Exception:
        await db.rollback()
        logger.exception("Ma'lumotlar bazasini yaratishda xato yuz berdi.")
        raise

    finally:
        await db.close()


# =========================================================
# USER MANAGEMENT
# =========================================================

async def register_user(
    user_id: int,
    username: str | None = None,
    display_name: str = "",
    language: str = "uz",
) -> None:
    """
    Foydalanuvchini ro'yxatdan o'tkazadi.

    Oldindan mavjud foydalanuvchining balansini
    qayta nolga tushirmaydi.
    """
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id,
                username,
                display_name,
                language
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                language = excluded.language,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                username,
                display_name,
                language,
            ),
        )

        await db.commit()


async def get_user(user_id: int) -> dict | None:
    """Foydalanuvchi ma'lumotlarini lug'at ko'rinishida qaytaradi."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        return dict(row)


async def update_user_activity(user_id: int) -> None:
    """Foydalanuvchining oxirgi faollik vaqtini yangilaydi."""
    async with get_db() as db:
        await db.execute(
            """
            UPDATE users
            SET last_active_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )

        await db.commit()
      # =========================================================
# GAME MANAGEMENT
# =========================================================

async def create_game_record(
    chat_id: int,
    creator_id: int,
) -> int:
    """
    Yangi o'yin yozuvini yaratadi va game_id qaytaradi.

    Bu funksiya o'yinni avtomatik boshlamaydi.
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO games (
                chat_id,
                creator_id,
                status,
                phase
            )
            VALUES (?, ?, 'LOBBY', 'LOBBY')
            """,
            (chat_id, creator_id),
        )

        await db.commit()

        if cursor.lastrowid is None:
            raise RuntimeError("O'yin ID raqamini olish imkoni bo'lmadi.")

        return int(cursor.lastrowid)


async def get_game_record(game_id: int) -> dict | None:
    """O'yin yozuvini ID orqali topadi."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,),
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        return dict(row)


async def update_game_record(
    game_id: int,
    status: str,
    phase: str,
    round_number: int,
    night_number: int,
    state_json: str,
) -> bool:
    """
    O'yin holatini bazada yangilaydi.

    O'yin logikasi va holatning to'g'riligi
    game engine tomonidan boshqarilishi kerak.
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            UPDATE games
            SET status = ?,
                phase = ?,
                round_number = ?,
                night_number = ?,
                state_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE game_id = ?
            """,
            (
                status,
                phase,
                round_number,
                night_number,
                state_json,
                game_id,
            ),
        )

        await db.commit()

        return cursor.rowcount > 0


# =========================================================
# HEALTH CHECK
# =========================================================

async def check_database() -> bool:
    """Bazaga ulanish va oddiy so'rovni tekshiradi."""
    try:
        
        async with get_db() as db:
            cursor = await db.execute("SELECT 1")
            row = await cursor.fetchone()

            return row is not None and row[0] == 1

    except Exception:
        logger.exception("Ma'lumotlar bazasi tekshiruvi muvaffaqiyatsiz.")
        return False  
async def init_database() -> None:
    """Ma'lumotlar bazasini ishga tushiradi."""
    await init_db()
