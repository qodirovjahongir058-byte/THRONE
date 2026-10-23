
import aiosqlite
from pathlib import Path
from datetime import date, datetime, timedelta

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
                oltin INTEGER NOT NULL DEFAULT 0 CHECK (oltin >= 0),
                almaz INTEGER NOT NULL DEFAULT 0 CHECK (almaz >= 0),
                koin INTEGER NOT NULL DEFAULT 0 CHECK (koin >= 0),
                xp INTEGER NOT NULL DEFAULT 0 CHECK (xp >= 0),
                level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1),
                daily_last_claim TEXT,
                daily_streak INTEGER NOT NULL DEFAULT 0
                    CHECK (daily_streak >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration for databases created by older versions.
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in await cursor.fetchall()}
        await cursor.close()

        if "daily_last_claim" not in columns:
            await db.execute(
                "ALTER TABLE users ADD COLUMN daily_last_claim TEXT"
            )

        if "daily_streak" not in columns:
            await db.execute("""
                ALTER TABLE users ADD COLUMN daily_streak INTEGER
                NOT NULL DEFAULT 0
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
    """Set a supported language."""
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


DAILY_REWARDS = [
    {"oltin": 100, "xp": 0},
    {"oltin": 150, "xp": 0},
    {"oltin": 200, "xp": 10},
    {"oltin": 250, "xp": 0},
    {"oltin": 350, "xp": 20},
    {"oltin": 500, "xp": 0},
    {"oltin": 750, "xp": 30},
]


async def claim_daily_bonus(
    database_path: str,
    user_id: int,
    today: date | None = None,
) -> dict:
    """
    Claim a daily reward once per calendar day.

    Returns:
        {"ok": True, "day": int, "oltin": int, "xp": int}
    or {"ok": False, "reason": "..."}.
    """
    claim_date = today or datetime.now().date()
    today_text = claim_date.isoformat()

    async with aiosqlite.connect(database_path) as db:
        await db.execute("BEGIN IMMEDIATE")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT daily_last_claim, daily_streak "
            "FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()

        if row is None:
            await db.rollback()
            return {"ok": False, "reason": "user_not_found"}

        last_claim_text = row["daily_last_claim"]
        streak = row["daily_streak"] or 0

        if last_claim_text == today_text:
            await db.rollback()
            return {"ok": False, "reason": "already_claimed"}

        if last_claim_text:
            try:
                last_claim = date.fromisoformat(last_claim_text)
            except ValueError:
                last_claim = None

            if last_claim == claim_date - timedelta(days=1):
                streak = (streak % 7) + 1
            else:
                streak = 1
        else:
            streak = 1

        reward = DAILY_REWARDS[streak - 1]

        await db.execute("""
            UPDATE users
            SET oltin = oltin + ?,
                xp = xp + ?,
                daily_last_claim = ?,
                daily_streak = ?
            WHERE user_id = ?
        """, (
            reward["oltin"],
            reward["xp"],
            today_text,
            streak,
            user_id,
        ))

        await db.commit()

    return {
        "ok": True,
        "day": streak,
        "oltin": reward["oltin"],
        "xp": reward["xp"],
    }
    
