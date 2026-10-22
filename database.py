
import aiosqlite
from pathlib import Path

DEFAULT_LANGUAGE = "uz"

SUPPORTED_LANGUAGES = {
    "uz", "ru", "en", "tr", "ar",
    "ky", "kk", "tg", "fr", "de",
    "es", "az", "pt", "it", "zh",
    "ja", "ko", "hi", "id", "uk",
}

CURRENCIES = {"oltin", "almaz", "koin"}


async def init_db(database_path: str) -> None:
    """Create the database and required tables."""
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(
            parents=True, exist_ok=True
        )

    async with aiosqlite.connect(database_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'uz',
                oltin INTEGER NOT NULL DEFAULT 0
                    CHECK (oltin >= 0),
                almaz INTEGER NOT NULL DEFAULT 0
                    CHECK (almaz >= 0),
                koin INTEGER NOT NULL DEFAULT 0
                    CHECK (koin >= 0),
                xp INTEGER NOT NULL DEFAULT 0
                    CHECK (xp >= 0),
                level INTEGER NOT NULL DEFAULT 1
                    CHECK (level >= 1),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'uz',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id)
                    REFERENCES groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        await db.commit()


async def ensure_user(
    database_path: str,
    user_id: int,
    username: str | None = None,
    first_name: str = "",
) -> None:
    """Create a user if they do not exist; update their name."""
    async with aiosqlite.connect(database_path) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
        await db.commit()


async def get_user(
    database_path: str, user_id: int
) -> dict | None:
    """Return a user's profile as a dictionary."""
    async with aiosqlite.connect(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None


async def set_language(
    database_path: str,
    user_id: int,
    language: str,
) -> bool:
    """Set a supported language. Return False for invalid input."""
    language = language.strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        return False

    async with aiosqlite.connect(database_path) as db:
        cursor = await db.execute("""
            UPDATE users SET language = ?
            WHERE user_id = ?
        """, (language, user_id))
        await db.commit()
        updated = cursor.rowcount
        await cursor.close()

    return updated > 0


async def add_balance(
    database_path: str,
    user_id: int,
    currency: str,
    amount: int,
) -> bool:
    """Add currency. Reject invalid currencies and non-positive amounts."""
    currency = currency.strip().lower()

    if currency not in CURRENCIES or amount <= 0:
        return False

    # The column name is selected only from the fixed allowlist above.
    async with aiosqlite.connect(database_path) as db:
        cursor = await db.execute(
            f"UPDATE users SET {currency} = {currency} + ? "
            "WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()
        updated = cursor.rowcount
        await cursor.close()

    return updated > 0
    
