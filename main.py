
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import ConfigError, load_settings
from database import Database
from game_actions import GameActionManager
from game_controller import GameController
from game_engine import GameEngine
from game_lobby import GameLobby
from game_partners import GamePartners
from game_timer import GameTimer
from game_voting import GameVoting
from handlers import create_handlers


logger = logging.getLogger("throne")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | "
        "%name)s | %(message)s".replace("%name)s", "%(name)s"),
    )


def create_dispatcher(
    controller: GameController,
) -> Dispatcher:
    dp = Dispatcher()

    dp.include_router(create_handlers(controller))

    @dp.message(CommandStart())
    async def start_command(message: Message) -> None:
        await message.answer(
            "👑 THRONE botiga xush kelibsiz!\n\n"
            "O'yin guruhida /newgame buyrug'i orqali "
            "yangi lobby oching.\n"
            "/help — buyruqlar ro'yxati."
        )

    @dp.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "👑 THRONE — qirollik strategiya o'yini\n\n"
            "/newgame — yangi o'yin ochish\n"
            "/join — o'yinga qo'shilish\n"
            "/leave — lobbydan chiqish\n"
            "/startgame — o'yinni boshlash\n"
            "/stopgame — o'yinni to'xtatish\n"
            "/status — o'yin holati\n"
            "/id — Telegram ID raqamlari\n"
            "/help — yordam"
        )

    @dp.message(Command("id"))
    async def id_command(message: Message) -> None:
        user_id = (
            message.from_user.id
            if message.from_user
            else "Noma'lum"
        )
        await message.answer(
            f"Telegram ID: {user_id}\n"
            f"Chat ID: {message.chat.id}"
        )

    return dp


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    database: Database | None = None
    bot: Bot | None = None
    timer: GameTimer | None = None
    controller: GameController | None = None

    try:
        database = Database(
            db_path=settings.database_path
        )
        bot = Bot(token=settings.bot_token)

        lobby = GameLobby(database)
        engine = GameEngine()
        timer = GameTimer()
        voting = GameVoting()
        actions = GameActionManager()
        partners = GamePartners()

        controller = GameController(
            bot=bot,
            database=database,
            lobby=lobby,
            engine=engine,
            timer=timer,
            voting=voting,
            actions=actions,
            partners=partners,
        )

        dp = create_dispatcher(controller)

        logger.info("THRONE bot ishga tushmoqda.")
        await dp.start_polling(
            bot,
            close_bot_session=False,
        )

    except (ConfigError, ValueError):
        logger.exception("Konfiguratsiya xatosi.")
        raise

    except Exception:
        logger.exception("Bot ishlashida xatolik.")
        raise

    finally:
        if controller is not None:
            await controller.close()

        if timer is not None:
            await timer.close()

        if database is not None:
            database.close()

        if bot is not None:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("THRONE bot to'xtatildi.")
    
