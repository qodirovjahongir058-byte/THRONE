import os

from dotenv import load_dotenv

load_dotenv()


def _get_required(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable is missing: {name}"
        )

    return value


BOT_TOKEN = _get_required("BOT_TOKEN")
CREATOR_ID = int(_get_required("CREATOR_ID"))

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "data/throne.db",
)

WEBAPP_URL = os.getenv("WEBAPP_URL", "")

CHANNEL_ID = os.getenv("CHANNEL_ID", "")

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()

TIMEZONE = os.getenv(
    "TIMEZONE",
    "Asia/Tashkent",
)
