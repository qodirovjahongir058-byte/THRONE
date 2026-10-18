import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_int_env(name: str, default: int = 0) -> int:
    """Environment o'zgaruvchisini butun songa aylantiradi."""
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} sozlamasi butun son bo'lishi kerak."
        ) from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str
    creator_id: int
    database_path: str
    webapp_url: str
    channel_id: int
    debug: bool

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()

        if not token:
            raise ValueError(
                "BOT_TOKEN topilmadi. .env faylini sozlang."
            )

        database_path = os.getenv(
            "DATABASE_PATH",
            "throne.db",
        ).strip()

        if not database_path:
            database_path = "throne.db"

        if not Path(database_path).is_absolute():
            database_path = str(BASE_DIR / database_path)

        return cls(
            bot_token=token,
            creator_id=get_int_env("CREATOR_ID"),
            database_path=database_path,
            webapp_url=os.getenv("WEBAPP_URL", "").strip(),
            channel_id=get_int_env("CHANNEL_ID"),
            debug=os.getenv("DEBUG", "false").strip().lower()
            in {"1", "true", "yes"},
        )


settings = Settings.from_env()
