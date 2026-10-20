
from __future__ import annotations

import logging
from html import escape

from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from game_controller import GameController


logger = logging.getLogger(__name__)


def create_handlers(
    controller: GameController,
) -> Router:
    router = Router(name="throne_handlers")

    async def is_group_admin(
        message: Message,
        bot: Bot,
    ) -> bool:
        if message.chat.type not in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            await message.answer(
                "Bu buyruqni guruhda ishlating."
            )
            return False

        if message.from_user is None:
            await message.answer(
                "Foydalanuvchini aniqlab bo'lmadi."
            )
            return False

        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
            )
        except Exception:
            logger.exception(
                "Guruh administratori tekshiruvi xatosi."
            )
            await message.answer(
                "Administratorlikni tekshirib bo'lmadi. "
                "Botning guruhdagi ruxsatlarini tekshiring."
            )
            return False

        if member.status not in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ):
            await message.answer(
                "⛔ Bu buyruq faqat guruh adminlari uchun."
            )
            return False

        return True

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer(
            "👑 <b>THRONE qirolligiga xush kelibsiz!</b>\n\n"
            "Strategiya, ittifoqlar va qirollik uchun kurash "
            "sizni kutmoqda.\n\n"
            "Guruhda o'yin boshlash uchun /newgame buyrug'idan "
            "foydalaning.\n"
            "Buyruqlar ro'yxati: /help",
            parse_mode="HTML",
        )

    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(
            "📜 <b>THRONE buyruqlari</b>\n\n"
            "/newgame — yangi lobby ochish (admin)\n"
            "/join — o'yinga qo'shilish\n"
            "/leave — lobbydan chiqish\n"
            "/startgame — o'yinni boshlash (admin)\n"
            "/stopgame — o'yinni to'xtatish (admin)\n"
            "/status — o'yin holatini ko'rish\n"
            "/id — Telegram ID raqamlarini ko'rish\n"
            "/help — yordam\n\n"
            "⚔️ O'yin buyruqlarini guruhda ishlating.",
            parse_mode="HTML",
        )

    @router.message(Command("id"))
    async def id_handler(message: Message) -> None:
        user_id = (
            message.from_user.id
            if message.from_user
            else "Noma'lum"
        )

        await message.answer(
            f"👤 Telegram ID: <code>{user_id}</code>\n"
            f"💬 Chat ID: <code>{message.chat.id}</code>",
            parse_mode="HTML",
        )

    @router.message(Command("newgame"))
    async def newgame_handler(
        message: Message,
        bot: Bot,
    ) -> None:
        if not await is_group_admin(message, bot):
            return

        if message.from_user is None:
            return

        result = await controller.create_game(
            chat_id=message.chat.id,
            creator_id=message.from_user.id,
            creator_name=message.from_user.full_name,
            username=message.from_user.username,
        )

        await message.answer(
            ("✅ " if result.success else "❌ ")
            + escape(result.message)
        )

    @router.message(Command("join"))
    async def join_handler(
        message: Message,
    ) -> None:
        if message.chat.type not in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            await message.answer(
                "O'yinga qo'shilish uchun guruhda /join yozing."
            )
            return

        if message.from_user is None:
            return

        result = await controller.join_game(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )

        await message.answer(
            ("✅ " if result.success else "❌ ")
            + escape(result.message)
        )

    @router.message(Command("leave"))
    async def leave_handler(
        message: Message,
    ) -> None:
        if message.chat.type not in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            await message.answer(
                "Bu buyruqni o'yin guruhida ishlating."
            )
            return

        if message.from_user is None:
            return

        result = await controller.leave_game(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        )

        await message.answer(
            ("✅ " if result.success else "❌ ")
            + escape(result.message)
        )

    @router.message(Command("startgame"))
    async def startgame_handler(
        message: Message,
        bot: Bot,
    ) -> None:
        if not await is_group_admin(message, bot):
            return

        if message.from_user is None:
            return

        result = await controller.start_game(
            chat_id=message.chat.id,
            requester_id=message.from_user.id,
        )

        await message.answer(
            ("✅ " if result.success else "❌ ")
            + escape(result.message)
        )

    @router.message(Command("stopgame"))
    async def stopgame_handler(
        message: Message,
        bot: Bot,
    ) -> None:
        if not await is_group_admin(message, bot):
            return

        if message.from_user is None:
            return

        result = await controller.stop_game(
            chat_id=message.chat.id,
            requester_id=message.from_user.id,
        )

        await message.answer(
            ("✅ " if result.success else "❌ ")
            + escape(result.message)
        )

    @router.message(Command("status"))
    async def status_handler(
        message: Message,
    ) -> None:
        game = controller.get_game(message.chat.id)

        if game is None:
            await message.answer(
                "ℹ️ Bu guruhda o'yin topilmadi."
            )
            return

        phase = escape(str(game.phase.value))
        await message.answer(
            "👑 <b>THRONE — O'YIN HOLATI</b>\n\n"
            f"🎮 O'yin ID: <code>{escape(game.game_id)}</code>\n"
            f"📍 Bosqich: <b>{phase}</b>\n"
            f"👥 O'yinchilar: {game.player_count}/"
            f"{game.max_players}\n"
            f"❤️ Tirik o'yinchilar: {game.alive_count}",
            parse_mode="HTML",
        )

    return router
      
