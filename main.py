
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import Database

from game_handlers import router as game_router
from night_action_handlers import router as night_action_router
from night_resolution_handlers import (
    router as night_resolution_router,
)
from day_phase_handlers import router as day_phase_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("THRONE")


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = Dispatcher()

    # 1. O'yin lobbi va boshlanishi.
    dp.include_router(game_router)

    # 2. Tungi harakatlar.
    dp.include_router(night_action_router)

    # 3. Tun natijalarini hisoblash.
    dp.include_router(night_resolution_router)

    # 4. Kunduzgi muhokama va ovoz berish.
    dp.include_router(day_phase_router)

    database = Database(settings.database_path)

    try:
        await database.initialize()
        logger.info("THRONE ma'lumotlar bazasi tayyor.")

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("THRONE bot ishga tushmoqda.")

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    finally:
        await database.close()
        await bot.session.close()
        logger.info("THRONE bot to'xtadi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
        
