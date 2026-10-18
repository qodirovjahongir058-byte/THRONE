import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import Database


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("THRONE")


async def main() -> None:
    """THRONE botini ishga tushiradi."""
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dispatcher = Dispatcher()
    database = Database(settings.database_path)

    try:
        await database.initialize()

        bot_info = await bot.get_me()
        logger.info(
            "THRONE ishga tushmoqda: @%s (ID: %s)",
            bot_info.username,
            bot_info.id,
        )

        # Keyingi bosqichlarda o'yin va buyruq handlerlari ulanadi.
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )

    finally:
        await database.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("THRONE bot to'xtatildi.")
