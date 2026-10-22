
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    creator_id: int
    official_channel: str
    database_path: str


def load_config() -> Config:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    creator_id_text = os.getenv("CREATOR_ID", "").strip()
    channel = os.getenv(
        "OFFICIAL_CHANNEL", "@THRONE_Game"
    ).strip()
    database_path = os.getenv(
        "DATABASE_PATH", "data/throne.db"
    ).strip()

    if not token or token == "YOUR_BOT_TOKEN":
        raise ValueError(
            "BOT_TOKEN .env faylida sozlanmagan."
        )

    try:
        creator_id = int(creator_id_text)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "CREATOR_ID raqamli Telegram ID bo‘lishi kerak."
        ) from exc

    if creator_id <= 0:
        raise ValueError(
            "CREATOR_ID musbat son bo‘lishi kerak."
        )

    if not channel:
        raise ValueError(
            "OFFICIAL_CHANNEL bo‘sh bo‘lmasligi kerak."
        )

    if not database_path:
        raise ValueError(
            "DATABASE_PATH bo‘sh bo‘lmasligi kerak."
        )

    if database_path != ":memory:":
        Path(database_path).parent.mkdir(
            parents=True, exist_ok=True
        )

    return Config(
        bot_token=token,
        creator_id=creator_id,
        official_channel=channel,
        database_path=database_path,
    )
    
