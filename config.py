
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(Exception):
    """THRONE konfiguratsiyasidagi xatolar."""


@dataclass(frozen=True, slots=True)
class GameSettings:
    min_players: int = 7
    max_players: int = 50
    lobby_duration_seconds: int = 1200
    night_duration_seconds: int = 90
    discussion_duration_seconds: int = 120
    voting_duration_seconds: int = 60
    last_words_duration_seconds: int = 30
    max_revotes: int = 1

    def validate(self) -> None:
        if not 2 <= self.min_players <= self.max_players <= 50:
            raise ConfigError(
                "O'yinchilar soni noto'g'ri. "
                "min_players kamida 2, max_players esa "
                "min_players dan 50 gacha bo'lishi kerak."
            )

        durations = {
            "LOBBY_DURATION_SECONDS": self.lobby_duration_seconds,
            "NIGHT_DURATION_SECONDS": self.night_duration_seconds,
            "DISCUSSION_DURATION_SECONDS": self.discussion_duration_seconds,
            "VOTING_DURATION_SECONDS": self.voting_duration_seconds,
            "LAST_WORDS_DURATION_SECONDS": self.last_words_duration_seconds,
        }

        for name, value in durations.items():
            if value <= 0:
                raise ConfigError(
                    f"{name} musbat son bo'lishi kerak."
                )

        if self.max_revotes < 0:
            raise ConfigError("MAX_REVOTES manfiy bo'lishi mumkin emas.")


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    creator_id: int
    database_path: str = "data/throne.db"
    game: GameSettings = GameSettings()
    log_level: str = "INFO"
    timezone: str = "UTC"

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()

        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token == "your_telegram_bot_token_here":
            raise ConfigError(
                "BOT_TOKEN sozlanmagan. Haqiqiy tokenni "
                "hosting Environment Variables bo'limiga kiriting."
            )

        creator_id_text = os.getenv("CREATOR_ID", "").strip()
        try:
            creator_id = int(creator_id_text)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                "CREATOR_ID haqiqiy Telegram ID raqami bo'lishi kerak."
            ) from exc

        if creator_id <= 0:
            raise ConfigError("CREATOR_ID musbat son bo'lishi kerak.")

        def read_int(name: str, default: int) -> int:
            raw = os.getenv(name, str(default)).strip()
            try:
                return int(raw)
            except ValueError as exc:
                raise ConfigError(
                    f"{name} butun son bo'lishi kerak."
                ) from exc

        game = GameSettings(
            min_players=read_int("MIN_PLAYERS", 7),
            max_players=read_int("MAX_PLAYERS", 50),
            lobby_duration_seconds=read_int(
                "LOBBY_DURATION_SECONDS", 1200
            ),
            night_duration_seconds=read_int(
                "NIGHT_DURATION_SECONDS", 90
            ),
            discussion_duration_seconds=read_int(
                "DISCUSSION_DURATION_SECONDS", 120
            ),
            voting_duration_seconds=read_int(
                "VOTING_DURATION_SECONDS", 60
            ),
            last_words_duration_seconds=read_int(
                "LAST_WORDS_DURATION_SECONDS", 30
            ),
            max_revotes=read_int("MAX_REVOTES", 1),
        )
        game.validate()

        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        }:
            raise ConfigError("LOG_LEVEL noto'g'ri.")

        database_path = os.getenv(
            "DATABASE_PATH", "data/throne.db"
        ).strip()
        if not database_path:
            raise ConfigError("DATABASE_PATH bo'sh bo'lishi mumkin emas.")

        return cls(
            bot_token=token,
            creator_id=creator_id,
            database_path=database_path,
            game=game,
            log_level=log_level,
            timezone=os.getenv("TIMEZONE", "UTC").strip() or "UTC",
        )

    def prepare_directories(self) -> None:
        Path(self.database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )


def load_settings() -> Settings:
    settings = Settings.from_env()
    settings.prepare_directories()
    return settings
    
