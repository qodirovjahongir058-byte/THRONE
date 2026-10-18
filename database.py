import aiosqlite
from pathlib import Path
from typing import Any


class Database:
    """THRONE uchun SQLite ma'lumotlar bazasi."""

    def __init__(self, database_path: str = "throne.db") -> None:
        self.database_path = database_path
        self._initialized = False

    async def initialize(self) -> None:
        """Jadvallarni yaratadi."""
        if self._initialized:
            return

        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL DEFAULT '',
                    gold INTEGER NOT NULL DEFAULT 0,
                    coin INTEGER NOT NULL DEFAULT 0,
                    diamond INTEGER NOT NULL DEFAULT 0,
                    games_played INTEGER NOT NULL DEFAULT 0,
                    games_won INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    round_number INTEGER NOT NULL DEFAULT 0,
                    winner TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS game_players (
                    game_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role_id TEXT,
                    team TEXT,
                    alive INTEGER NOT NULL DEFAULT 1,
                    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_id, user_id),
                    FOREIGN KEY (game_id)
                        REFERENCES games(game_id)
                        ON DELETE CASCADE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id)
                        REFERENCES games(game_id)
                        ON DELETE CASCADE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_games_chat
                ON games(chat_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_game
                ON game_history(game_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user
                ON transactions(user_id)
            """)

            await db.commit()

        self._initialized = True

    async def close(self) -> None:
        """Bu klassda doimiy ulanish saqlanmaydi."""
        return None

    async def ensure_player(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> None:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO players (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, username, full_name))
            await db.commit()

    async def get_player(self, user_id: int) -> dict[str, Any] | None:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM players WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_game(
        self,
        game_id: str,
        chat_id: int,
        creator_id: int,
        phase: str = "lobby",
    ) -> None:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO games (game_id, chat_id, creator_id, phase)
                VALUES (?, ?, ?, ?)
            """, (game_id, chat_id, creator_id, phase))
            await db.commit()

    async def update_game(
        self,
        game_id: str,
        *,
        phase: str | None = None,
        round_number: int | None = None,
        winner: str | None = None,
        finished: bool = False,
    ) -> bool:
        await self.initialize()

        fields = []
        values: list[Any] = []

        if phase is not None:
            fields.append("phase = ?")
            values.append(phase)

        if round_number is not None:
            fields.append("round_number = ?")
            values.append(round_number)

        if winner is not None:
            fields.append("winner = ?")
            values.append(winner)

        if finished:
            fields.append("finished_at = CURRENT_TIMESTAMP")

        if not fields:
            return False

        values.append(game_id)

        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                f"UPDATE games SET {', '.join(fields)} WHERE game_id = ?",
                values,
            )
            await db.commit()
            return cursor.rowcount > 0

    async def add_game_player(
        self,
        game_id: str,
        user_id: int,
        role_id: str | None = None,
        team: str | None = None,
    ) -> None:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO game_players
                    (game_id, user_id, role_id, team)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(game_id, user_id) DO UPDATE SET
                    role_id = excluded.role_id,
                    team = excluded.team
            """, (game_id, user_id, role_id, team))
            await db.commit()

    async def update_game_player(
        self,
        game_id: str,
        user_id: int,
        *,
        alive: bool | None = None,
        role_id: str | None = None,
        team: str | None = None,
    ) -> bool:
        await self.initialize()

        fields = []
        values: list[Any] = []

        if alive is not None:
            fields.append("alive = ?")
            values.append(int(alive))

        if role_id is not None:
            fields.append("role_id = ?")
            values.append(role_id)

        if team is not None:
            fields.append("team = ?")
            values.append(team)

        if not fields:
            return False

        values.extend([game_id, user_id])

        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                f"""
                UPDATE game_players
                SET {', '.join(fields)}
                WHERE game_id = ? AND user_id = ?
                """,
                values,
            )
            await db.commit()
            return cursor.rowcount > 0

    async def add_history(
        self,
        game_id: str,
        event_type: str,
        description: str,
    ) -> None:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO game_history
                    (game_id, event_type, description)
                VALUES (?, ?, ?)
            """, (game_id, event_type, description))
            await db.commit()

    async def add_transaction(
        self,
        user_id: int,
        currency: str,
        amount: int,
        reason: str,
    ) -> None:
        await self.initialize()

        if currency not in {"gold", "coin", "diamond"}:
            raise ValueError("Noma'lum valyuta turi.")

        if amount == 0:
            raise ValueError("Tranzaksiya miqdori nol bo'lishi mumkin emas.")

        column = currency

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO players (user_id)
                VALUES (?)
                ON CONFLICT(user_id) DO NOTHING
            """, (user_id,))

            cursor = await db.execute(
                f"SELECT {column} FROM players WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            current_amount = row[0]

            if current_amount + amount < 0:
                raise ValueError("Mablag' yetarli emas.")

            await db.execute(
                f"""
                UPDATE players
                SET {column} = {column} + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (amount, user_id),
            )

            await db.execute("""
                INSERT INTO transactions
                    (user_id, currency, amount, reason)
                VALUES (?, ?, ?, ?)
            """, (user_id, currency, amount, reason))

            await db.commit()

    async def get_game_history(
        self,
        game_id: str,
    ) -> list[dict[str, Any]]:
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT *
                FROM game_history
                WHERE game_id = ?
                ORDER BY id ASC
            """, (game_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def create_database(
    database_path: str = "throne.db",
) -> Database:
    database = Database(database_path)
    await database.initialize()
    return database
