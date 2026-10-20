
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import ConfigError, load_settings
from database import Database


logger = logging.getLogger("throne")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        stream=sys.stdout,
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_command(message: Message) -> None:
        await message.answer(
            "👑 <b>THRONE qirolligiga xush kelibsiz!</b>\n\n"
            "Bu yerda sizni strategiya, ittifoqlar va "
            "qirollik uchun kurash kutmoqda.\n\n"
            "📜 Buyruqlar:\n"
            "/start — bot bilan tanishish\n"
            "/help — yordam olish\n\n"
            "⚔️ Guruhdagi o'yin funksiyalari keyingi "
            "integratsiya bosqichida ulanadi.",
            parse_mode="HTML",
        )

    @dp.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "📜 <b>THRONE — YORDAM</b>\n\n"
            "/start — boshlash\n"
            "/help — buyruqlar haqida ma'lumot\n\n"
            "👑 Guruh o'yinini boshqarish buyruqlari "
            "o'yin handlerlari ulangandan keyin ishlaydi.",
            parse_mode="HTML",
        )

    @dp.message(Command("id"))
    async def id_command(message: Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id

        await message.answer(
            f"👤 Telegram ID: <code>{user_id}</code>\n"
            f"💬 Chat ID: <code>{chat_id}</code>",
            parse_mode="HTML",
        )

    return dp


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    logger.info("THRONE ishga tushmoqda...")

    database: Database | None = None
    bot: Bot | None = None

    try:
        database = Database(
            db_path=settings.database_path,
        )

        bot = Bot(
            token=settings.bot_token,
        )

        dp = create_dispatcher()

        logger.info("Ma'lumotlar bazasi tayyor.")
        logger.info("Telegram polling boshlanmoqda.")

        await dp.start_polling(
            bot,
            close_bot_session=False,
        )

    finally:
        if database is not None:
            database.close()

        if bot is not None:
            await bot.session.close()

        logger.info("THRONE bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ConfigError, ValueError) as exc:
        print(f"Konfiguratsiya xatosi: {exc}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("THRONE bot qo'lda to'xtatildi.")
        
