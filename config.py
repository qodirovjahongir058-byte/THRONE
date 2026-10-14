import os
from pathlib import Path

from dotenv import load_dotenv

# Loyiha ildiz papkasi
BASE_DIR = Path(__file__).resolve().parent

# .env faylidagi sozlamalarni yuklash
load_dotenv(BASE_DIR / ".env")


def get_required_env(name: str) -> str:
    """Majburiy muhit o'zgaruvchisini tekshiradi."""
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} sozlamasi topilmadi. "
            "Uni hostingdagi Environment Variables bo'limida kiriting."
        )

    return value


def get_optional_env(name: str, default: str = "") -> str:
    """Ixtiyoriy muhit o'zgaruvchisini o'qiydi."""
    return os.getenv(name, default).strip()


# Telegram bot sozlamalari
BOT_TOKEN = get_required_env("BOT_TOKEN")
CREATOR_ID = int(get_required_env("CREATOR_ID"))

# Ma'lumotlar bazasi
DATABASE_PATH = get_optional_env(
    "DATABASE_PATH",
    str(BASE_DIR / "data" / "throne.db"),
)

# Mini App manzili
WEBAPP_URL = get_optional_env("WEBAPP_URL")

# Rasmiy kanal ID yoki username
CHANNEL_ID = get_optional_env("CHANNEL_ID")

# O'yin sozlamalari
MIN_PLAYERS = 7
MAX_PLAYERS = 35

LOBBY_DURATION = 120
NIGHT_DURATION = 90
DISCUSSION_DURATION = 120
VOTING_DURATION = 60
LAST_WORDS_DURATION = 30

# Qo'llab-quvvatlanadigan tillar
SUPPORTED_LANGUAGES = (
    "uz",
    "ru",
    "en",
    "tr",
    "ar",
    "ky",
)
