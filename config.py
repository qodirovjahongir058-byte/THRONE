
from __future__ import annotations

import os

from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """THRONE konfiguratsiyasi bilan bog'liq xato."""


def _read_int(
    name: str,
    default: int,
    minimum: int = 0,
) -> int:
    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        value = default
    else:
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ConfigError(
                f"{name} butun son bo'lishi kerak."
            ) from exc

    if value < minimum:
        raise ConfigError(
            f"{name} kamida {minimum} bo'lishi kerak."
        )

    return value


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
        if self.min_players < 1:
            raise ConfigError(
                "min_players kamida 1 bo'lishi kerak."
            )

        if self.max_players < self.min_players:
            raise ConfigError(
                "max_players min_players dan kichik bo'lmasin."
            )

        durations = {
            "lobby_duration_seconds":
                self.lobby_duration_seconds,
            "night_duration_seconds":
                self.night_duration_seconds,
            "discussion_duration_seconds":
                self.discussion_duration_seconds,
            "voting_duration_seconds":
                self.voting_duration_seconds,
            "last_words_duration_seconds":
                self.last_words_duration_seconds,
        }

        for name, value in durations.items():
            if value < 1:
                raise ConfigError(
                    f"{name} kamida 1 soniya bo'lishi kerak."
                )

        if self.max_revotes < 0:
            raise ConfigError(
                "max_revotes manfiy bo'lishi mumkin emas."
            )


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    creator_id: int
    database_path: str
    game: GameSettings
    log_level: str = "INFO"
    timezone: str = "UTC"

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("BOT_TOKEN", "").strip()

        if not token:
            raise ConfigError(
                "BOT_TOKEN topilmadi. "
                "Uni muhit o'zgaruvchilarida sozlang."
            )

        creator_id = _read_int(
            "CREATOR_ID",
            default=0,
            minimum=1,
        )

        database_path = os.getenv(
            "DATABASE_PATH",
            "data/throne.db",
        ).strip()

        if not database_path:
            database_path = "data/throne.db"

        game = GameSettings(
            min_players=_read_int(
                "MIN_PLAYERS", 7, 1
            ),
            max_players=_read_int(
                "MAX_PLAYERS", 50, 1
            ),
            lobby_duration_seconds=_read_int(
                "LOBBY_DURATION_SECONDS", 1200, 1
            ),
            night_duration_seconds=_read_int(
                "NIGHT_DURATION_SECONDS", 90, 1
            ),
            discussion_duration_seconds=_read_int(
                "DISCUSSION_DURATION_SECONDS", 120, 1
            ),
            voting_duration_seconds=_read_int(
                "VOTING_DURATION_SECONDS", 60, 1
            ),
            last_words_duration_seconds=_read_int(
                "LAST_WORDS_DURATION_SECONDS", 30, 1
            ),
            max_revotes=_read_int(
                "MAX_REVOTES", 1, 0
            ),
        )

        game.validate()

        log_level = os.getenv(
            "LOG_LEVEL", "INFO"
        ).strip().upper()

        allowed_log_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if log_level not in allowed_log_levels:
            raise ConfigError(
                "LOG_LEVEL qiymati noto'g'ri."
            )

        timezone = os.getenv(
            "TIMEZONE", "UTC"
        ).strip() or "UTC"

        return cls(
            bot_token=token,
            creator_id=creator_id,
            database_path=database_path,
            game=game,
            log_level=log_level,
            timezone=timezone,
        )

    def prepare_directories(self) -> None:
        """Ma'lumotlar bazasi papkasini yaratadi."""
        path = Path(self.database_path)

        if str(path.parent) not in ("", "."):
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )


def load_settings() -> Settings:
    """Sozlamalarni yuklaydi va tekshiradi."""
    settings = Settings.from_env()
    settings.prepare_directories()
    return settings
    
