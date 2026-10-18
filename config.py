
import os

from dotenv import load_dotenv

load_dotenv()


# ==================================================
# YORDAMCHI FUNKSIYALAR
# ==================================================

def _get_int(name: str, default: int = 0) -> int:
    """Muhit o'zgaruvchisini butun songa aylantiradi."""
    value = os.getenv(name, str(default)).strip()

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} butun son bo'lishi kerak."
        ) from exc


# ==================================================
# BOT VA TIZIM SOZLAMALARI
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

CREATOR_ID = _get_int("CREATOR_ID")

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "data/throne.db",
).strip()

WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()


# ==================================================
# TILLAR
# ==================================================

LANGUAGE_NAMES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
    "ar": "🇸🇦 العربية",
    "ky": "🇰🇬 Кыргызча",
    "kk": "🇰🇿 Қазақша",
    "az": "🇦🇿 Azərbaycanca",
    "tg": "🇹🇯 Тоҷикӣ",
    "tk": "🇹🇲 Türkmençe",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
    "pt": "🇵🇹 Português",
    "it": "🇮🇹 Italiano",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "hi": "🇮🇳 हिन्दी",
    "id": "🇮🇩 Bahasa Indonesia",
}

SUPPORTED_LANGUAGES = tuple(LANGUAGE_NAMES.keys())

DEFAULT_LANGUAGE = "uz"


# ==================================================
# O'YIN SOZLAMALARI
# ==================================================

MIN_PLAYERS = 7
MAX_PLAYERS = 36

# Vaqtlar soniyalarda berilgan.
LAST_WORDS_DURATION = 30
NIGHT_DURATION = 60
DISCUSSION_DURATION = 60
VOTING_DURATION = 30

# Durang ovozdan keyingi qayta ovoz berish.
REVOTE_DURATION = 30
MAX_REVOTES = 1

# Bitta guruhda bir vaqtda bitta faol o'yin.
ONE_ACTIVE_GAME_PER_CHAT = True


# ==================================================
# XAVFSIZLIK VA FOYDALANUVCHI SOZLAMALARI
# ==================================================

# Bot egasining maxsus huquqlari o'yin kodida
# alohida tekshirilishi kerak.
CREATOR_INFINITE_REWARDS = True

# Faollik nazorati: kun hisobida.
INACTIVITY_WARNING_DAYS = 7
INACTIVITY_REMOVAL_DAYS = 14

# Qo'llab-quvvatlanadigan til tekshiruvi.
def is_supported_language(language: str) -> bool:
    return language in SUPPORTED_LANGUAGES


# ==================================================
# SOZLAMALARNI TEKSHIRISH
# ==================================================

def validate_config() -> None:
    """Bot ishga tushishidan oldin majburiy sozlamalarni tekshiradi."""

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env yoki Railway Variables "
            "bo'limini tekshiring."
        )

    if CREATOR_ID <= 0:
        raise RuntimeError(
            "CREATOR_ID musbat Telegram foydalanuvchi ID "
            "bo'lishi kerak."
        )

    if not DATABASE_PATH:
        raise RuntimeError(
            "DATABASE_PATH bo'sh bo'lishi mumkin emas."
        )

    if MIN_PLAYERS < 2 or MAX_PLAYERS < MIN_PLAYERS:
        raise RuntimeError(
            "O'yinchilar soni sozlamalari noto'g'ri."
        )

    if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
        raise RuntimeError(
            "DEFAULT_LANGUAGE qo'llab-quvvatlanmaydi."
)
        
