
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from game_state import GamePhase, GameState, PlayerState


class DatabaseError(Exception):
    """THRONE ma'lumotlar bazasi xatosi."""


class ActiveGameConflict(DatabaseError):
    """Akkaunt boshqa faol o'yinda qatnashmoqda."""


class Database:
    """THRONE uchun SQLite ma'lumotlar bazasi."""

    def __init__(
        self,
        db_path: str = "data/throne.db",
    ) -> None:
        self.db_path = db_path

        if db_path != ":memory:":
            Path(db_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self.connection = sqlite3.connect(
            db_path,
            timeout=30,
            isolation_level=None,
        )
        self.connection.row_factory = sqlite3.Row

        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 30000")

        if db_path != ":memory:":
            self.connection.execute("PRAGMA journal_mode = WAL")

        self.initialize()

    def initialize(self) -> None:
        """Kerakli jadvallarni yaratadi."""

        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    round_number INTEGER NOT NULL DEFAULT 0,
                    winner TEXT,
                    end_reason TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    phase_started_at TEXT,
                    phase_deadline REAL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_games_chat_phase
                ON games(chat_id, phase);

                CREATE TABLE IF NOT EXISTS game_players (
                    game_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    role_id TEXT,
                    team TEXT,
                    status TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    eliminated_at TEXT,
                    elimination_reason TEXT,
                    last_words TEXT,
                    ability_uses_json TEXT NOT NULL DEFAULT '{}',
                    ability_data_json TEXT NOT NULL DEFAULT '{}',
                    partner_ids_json TEXT NOT NULL DEFAULT '[]',
                    PRIMARY KEY (game_id, user_id),
                    FOREIGN KEY (game_id)
                        REFERENCES games(game_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_game_players_user
                ON game_players(user_id);

                CREATE TABLE IF NOT EXISTS active_game_locks (
                    user_id INTEGER PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    chat_id INTEGER NOT NULL,
                    locked_at TEXT NOT NULL,
                    FOREIGN KEY (game_id)
                        REFERENCES games(game_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_active_locks_game
                ON active_game_locks(game_id);

                CREATE TABLE IF NOT EXISTS player_profiles (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    gold INTEGER NOT NULL DEFAULT 0,
                    coin INTEGER NOT NULL DEFAULT 0,
                    diamond INTEGER NOT NULL DEFAULT 0,
                    rp INTEGER NOT NULL DEFAULT 0,
                    language TEXT NOT NULL DEFAULT 'uz',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    @staticmethod
    def _json(data: Any) -> str:
        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _enum_value(value: Any) -> Any:
        return getattr(value, "value", value)

    def create_game(self, game: GameState) -> None:
        """Yangi o'yinni bazaga yozadi."""

        try:
            self.connection.execute(
                """
                INSERT INTO games (
                    game_id, chat_id, creator_id, phase,
                    round_number, created_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game.game_id,
                    game.chat_id,
                    game.creator_id,
                    game.phase.value,
                    game.round_number,
                    game.created_at.isoformat(),
                    self._json(game.metadata),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DatabaseError(
                f"O'yinni saqlab bo'lmadi: {exc}"
            ) from exc

    def save_game(self, game: GameState) -> None:
        """O'yin holati va ishtirokchilarini saqlaydi."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO games (
                    game_id, chat_id, creator_id, phase,
                    round_number, winner, end_reason, created_at,
                    started_at, finished_at, phase_started_at,
                    phase_deadline, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(game_id) DO UPDATE SET
                    phase = excluded.phase,
                    round_number = excluded.round_number,
                    winner = excluded.winner,
                    end_reason = excluded.end_reason,
                    started_at = excluded.started_at,
                    finished_at = excluded.finished_at,
                    phase_started_at = excluded.phase_started_at,
                    phase_deadline = excluded.phase_deadline,
                    metadata_json = excluded.metadata_json
                """,
                (
                    game.game_id,
                    game.chat_id,
                    game.creator_id,
                    game.phase.value,
                    game.round_number,
                    self._enum_value(game.winner),
                    self._enum_value(game.end_reason),
                    game.created_at.isoformat(),
                    (
                        game.started_at.isoformat()
                        if game.started_at else None
                    ),
                    (
                        game.finished_at.isoformat()
                        if game.finished_at else None
                    ),
                    (
                        game.phase_started_at.isoformat()
                        if game.phase_started_at else None
                    ),
                    (
                        game.phase_deadline.timestamp()
                        if hasattr(game.phase_deadline, "timestamp")
                        else game.phase_deadline
                    ),
                    self._json(game.metadata),
                ),
            )

            self.connection.execute(
                "DELETE FROM game_players WHERE game_id = ?",
                (game.game_id,),
            )

            for player in game.players.values():
                self.connection.execute(
                    """
                    INSERT INTO game_players (
                        game_id, user_id, full_name, username,
                        role_id, team, status, joined_at,
                        eliminated_at, elimination_reason, last_words,
                        ability_uses_json, ability_data_json,
                        partner_ids_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        game.game_id,
                        player.user_id,
                        player.full_name,
                        player.username,
                        player.role_id,
                        self._enum_value(player.team),
                        self._enum_value(player.status),
                        player.joined_at.isoformat(),
                        (
                            player.eliminated_at.isoformat()
                            if player.eliminated_at else None
                        ),
                        player.elimination_reason,
                        player.last_words,
                        self._json(player.ability_uses),
                        self._json(player.ability_data),
                        self._json(sorted(player.partner_ids)),
                    ),
                )

    def join_game(
        self,
        game: GameState,
        player: PlayerState,
    ) -> None:
        """
        O'yinchini o'yinga qo'shadi.

        BEGIN IMMEDIATE bir akkauntning parallel so'rovlarda
        bir nechta faol o'yinga kirishini oldini olishga yordam beradi.
        """

        terminal_phases = {
            GamePhase.FINISHED.value,
            GamePhase.STOPPED.value,
        }

        self.connection.execute("BEGIN IMMEDIATE")

        try:
            existing_game = self.connection.execute(
                """
                SELECT phase FROM games
                WHERE game_id = ?
                """,
                (game.game_id,),
            ).fetchone()

            if existing_game is None:
                raise DatabaseError(
                    "Avval o'yinni create_game() bilan saqlang."
                )

            if existing_game["phase"] != GamePhase.LOBBY.value:
                raise DatabaseError(
                    "O'yin lobby bosqichida emas."
                )

            lock = self.connection.execute(
                """
                SELECT user_id, game_id
                FROM active_game_locks
                WHERE user_id = ?
                """,
                (player.user_id,),
            ).fetchone()

            if lock is not None:
                other_game = self.connection.execute(
                    """
                    SELECT phase FROM games
                    WHERE game_id = ?
                    """,
                    (lock["game_id"],),
                ).fetchone()

                if (
                    other_game is not None
                    and other_game["phase"] not in terminal_phases
                ):
                    raise ActiveGameConflict(
                        "Bu akkaunt allaqachon boshqa faol "
                        "o'yinda qatnashmoqda."
                    )

                # Oldingi o'yin tugagan bo'lsa, eski qulfni tozalash.
                self.connection.execute(
                    """
                    DELETE FROM active_game_locks
                    WHERE user_id = ?
                    """,
                    (player.user_id,),
                )

            self.connection.execute(
                """
                INSERT INTO game_players (
                    game_id, user_id, full_name, username,
                    role_id, team, status, joined_at,
                    eliminated_at, elimination_reason, last_words,
                    ability_uses_json, ability_data_json,
                    partner_ids_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game.game_id,
                    player.user_id,
                    player.full_name,
                    player.username,
                    player.role_id,
                    self._enum_value(player.team),
                    self._enum_value(player.status),
                    player.joined_at.isoformat(),
                    None,
                    None,
                    player.last_words,
                    self._json(player.ability_uses),
                    self._json(player.ability_data),
                    self._json(sorted(player.partner_ids)),
                ),
            )

            self.connection.execute(
                """
                INSERT INTO active_game_locks (
                    user_id, game_id, chat_id, locked_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    player.user_id,
                    game.game_id,
                    game.chat_id,
                    player.joined_at.isoformat(),
                ),
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def release_game_locks(self, game_id: str) -> None:
        """O'yin tugaganda qatnashchilar qulfini bo'shatadi."""

        with self.connection:
            self.connection.execute(
                """
                DELETE FROM active_game_locks
                WHERE game_id = ?
                """,
                (game_id,),
            )

    def finish_game(self, game: GameState) -> None:
        """O'yin tugagan holatini saqlab, qulflarni bo'shatadi."""

        if game.phase not in {
            GamePhase.FINISHED,
            GamePhase.STOPPED,
        }:
            raise DatabaseError(
                "Qulfni bo'shatishdan oldin o'yinni yakunlang."
            )

        self.connection.execute("BEGIN IMMEDIATE")

        try:
            self.save_game(game)

            self.connection.execute(
                """
                DELETE FROM active_game_locks
                WHERE game_id = ?
                """,
                (game.game_id,),
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def get_active_game_id(
        self,
        user_id: int,
    ) -> str | None:
        """Akkaunt qatnashayotgan faol o'yin ID sini qaytaradi."""

        row = self.connection.execute(
            """
            SELECT l.game_id
            FROM active_game_locks AS l
            JOIN games AS g ON g.game_id = l.game_id
            WHERE l.user_id = ?
              AND g.phase NOT IN (?, ?)
            """,
            (
                user_id,
                GamePhase.FINISHED.value,
                GamePhase.STOPPED.value,
            ),
        ).fetchone()

        return row["game_id"] if row else None

    def get_game_record(
        self,
        game_id: str,
    ) -> dict[str, Any] | None:
        """O'yin haqidagi bazaviy ma'lumotlarni oladi."""

        row = self.connection.execute(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,),
        ).fetchone()

        return dict(row) if row else None

    def get_game_players(
        self,
        game_id: str,
    ) -> list[dict[str, Any]]:
        """O'yin ishtirokchilarini bazadan oladi."""

        rows = self.connection.execute(
            """
            SELECT * FROM game_players
            WHERE game_id = ?
            ORDER BY joined_at
            """,
            (game_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    def save_profile(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> None:
        """O'yinchi profilini yaratadi yoki yangilaydi."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO player_profiles (
                    user_id, full_name, username
                )
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    username = excluded.username,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, full_name, username),
            )

    def get_profile(
        self,
        user_id: int,
    ) -> dict[str, Any] | None:
        """O'yinchi profilini qaytaradi."""

        row = self.connection.execute(
            """
            SELECT * FROM player_profiles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        return dict(row) if row else None

    def close(self) -> None:
        """Ma'lumotlar bazasi ulanishini yopadi."""

        self.connection.close()


def create_database(
    db_path: str = "data/throne.db",
) -> Database:
    """Ma'lumotlar bazasini yaratish uchun yordamchi funksiya."""

    return Database(db_path)
                
