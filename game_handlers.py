import asyncio
import logging
import uuid

import aiosqlite
from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import settings
from database import Database


logger = logging.getLogger("THRONE.game_handlers")
router = Router(name="throne_game_handlers")

database = Database(settings.database_path)

MIN_PLAYERS = 7
MAX_PLAYERS = 36

# Guruhdagi joriy o'yinlar.
# Kalit — Telegram guruhining chat_id raqami.
active_games: dict[int, dict] = {}

# Bir guruhda bir vaqtda ikki o'yin ochilishining oldini oladi.
_group_locks: dict[int, asyncio.Lock] = {}


def get_group_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in _group_locks:
        _group_locks[chat_id] = asyncio.Lock()
    return _group_locks[chat_id]


def lobby_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ O‘yinga qo‘shilish",
                    callback_data=f"throne_join:{game_id}",
                )
            ]
        ]
    )


async def is_group_admin(
    bot: Bot,
    chat_id: int,
    user_id: int,
) -> bool:
    """Buyruq yuborgan foydalanuvchi guruh adminimi?"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }
    except Exception:
        logger.exception("Guruh adminini tekshirishda xatolik")
        return False


async def get_database_active_game(chat_id: int):
    """
    Bazada ushbu guruh uchun faol o'yin borligini tekshiradi.
    Bot qayta ishga tushganidan keyin ham eski faol o'yin
    yangi o'yin ochilishiga to'sqinlik qiladi.
    """
    await database.initialize()

    async with aiosqlite.connect(database.database_path) as db:
        cursor = await db.execute(
            """
            SELECT game_id, creator_id, phase
            FROM games
            WHERE chat_id = ?
              AND UPPER(phase) NOT IN (
                  'FINISHED',
                  'STOPPED'
              )
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (chat_id,),
        )
        return await cursor.fetchone()


async def get_game_players(game_id: str) -> list[int]:
    await database.initialize()

    async with aiosqlite.connect(database.database_path) as db:
        cursor = await db.execute(
            """
            SELECT user_id
            FROM game_players
            WHERE game_id = ?
            ORDER BY joined_at ASC
            """,
            (game_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


@router.message(Command("newgame"))
async def new_game(message: Message, bot: Bot) -> None:
    """Guruhda yangi o'yin ochadi."""
    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer(
            "⚔️ Yangi o‘yinni Telegram guruhida oching."
        )
        return

    if not message.from_user:
        return

    chat_id = message.chat.id
    creator_id = message.from_user.id

    if not await is_group_admin(bot, chat_id, creator_id):
        await message.answer(
            "🔒 Yangi o‘yinni faqat guruh administratori ochishi mumkin."
        )
        return

    lock = get_group_lock(chat_id)

    async with lock:
        existing = await get_database_active_game(chat_id)

        if existing is not None:
            await message.answer(
                "⚔️ Bu guruhda o‘yin allaqachon faol.\n\n"
                "Yangi o‘yin ochish uchun avval joriy o‘yin "
                "tugashi yoki to‘xtatilishi kerak."
            )
            return

        game_id = str(uuid.uuid4())

        try:
            await database.create_game(
                game_id=game_id,
                chat_id=chat_id,
                creator_id=creator_id,
                phase="LOBBY",
            )
        except aiosqlite.IntegrityError:
            await message.answer(
                "❌ O‘yinni yaratib bo‘lmadi. "
                "Iltimos, qayta urinib ko‘ring."
            )
            return

        active_games[chat_id] = {
            "game_id": game_id,
            "creator_id": creator_id,
            "players": [],
            "phase": "LOBBY",
        }

    await message.answer(
        "👑 <b>THRONE — Yangi o‘yin</b>\n\n"
        "🏰 Qirollik eshiklari ochildi!\n"
        f"👥 O‘yinchilar: 0/{MAX_PLAYERS}\n"
        f"⚔️ O‘yinni boshlash uchun kamida {MIN_PLAYERS} kishi kerak.\n\n"
        "O‘yinga qo‘shilish uchun quyidagi tugmani bosing.\n"
        "Guruh administratori o‘yinni /startgame orqali boshlaydi.",
        reply_markup=lobby_keyboard(game_id),
    )


@router.callback_query(lambda query: (
    query.data is not None
    and query.data.startswith("throne_join:")
))
async def join_game(query: CallbackQuery, bot: Bot) -> None:
    """O'yinchini faol o'yinga qo'shadi."""
    if not query.from_user or not query.message:
        await query.answer("O‘yin ma’lumotlari topilmadi.", show_alert=True)
        return

    chat = query.message.chat

    if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await query.answer(
            "O‘yinga guruhdagi tugma orqali qo‘shiling.",
            show_alert=True,
        )
        return

    game_id = query.data.split(":", 1)[1]
    chat_id = chat.id
    user = query.from_user

    lock = get_group_lock(chat_id)

    async with lock:
        existing = await get_database_active_game(chat_id)

        if existing is None or existing[0] != game_id:
            await query.answer(
                "Bu o‘yin endi faol emas.",
                show_alert=True,
            )
            return

        phase = str(existing[2]).upper()

        if phase != "LOBBY":
            await query.answer(
                "O‘yinga qo‘shilish vaqti tugagan.",
                show_alert=True,
            )
            return

        players = await get_game_players(game_id)

        if user.id in players:
            await query.answer(
                "Siz allaqachon o‘yinga qo‘shilgansiz.",
                show_alert=True,
            )
            return

        if len(players) >= MAX_PLAYERS:
            await query.answer(
                "O‘yinchilar soni maksimal chegaraga yetdi.",
                show_alert=True,
            )
            return

        await database.ensure_player(
            user_id=user.id,
            full_name=user.full_name,
            username=user.username,
        )

        await database.add_game_player(
            game_id=game_id,
            user_id=user.id,
        )

        if chat_id in active_games:
            active_games[chat_id]["players"] = players + [user.id]

        updated_count = len(players) + 1

    await query.answer("Siz o‘yinga qo‘shildingiz!")

    try:
        await query.message.edit_text(
            "👑 <b>THRONE — Yangi o‘yin</b>\n\n"
            "🏰 Qirollik eshiklari ochiq!\n"
            f"👥 O‘yinchilar: {updated_count}/{MAX_PLAYERS}\n"
            f"⚔️ Boshlash uchun kamida {MIN_PLAYERS} kishi kerak.\n\n"
            "Guruh administratori /startgame buyrug‘i bilan o‘yinni boshlaydi.",
            reply_markup=lobby_keyboard(game_id),
        )
    except Exception:
        logger.debug("Lobbi xabarini yangilab bo'lmadi", exc_info=True)


@router.message(Command("startgame"))
async def start_game(message: Message, bot: Bot) -> None:
    """Lobbidagi o'yinchilar sonini tekshiradi."""
    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer(
            "O‘yinni guruhda boshlash kerak."
        )
        return

    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_group_admin(bot, chat_id, user_id):
        await message.answer(
            "🔒 O‘yinni faqat guruh administratori boshlashi mumkin."
        )
        return

    lock = get_group_lock(chat_id)

    async with lock:
        existing = await get_database_active_game(chat_id)

        if existing is None:
            await message.answer(
                "❌ Faol lobbi topilmadi. /newgame orqali yangi o‘yin oching."
            )
            return

        game_id, creator_id, phase = existing
        phase = str(phase).upper()

        if phase != "LOBBY":
            await message.answer(
                "⚔️ O‘yin allaqachon boshlangan yoki faol bosqichda."
            )
            return

        players = await get_game_players(game_id)

        if len(players) < MIN_PLAYERS:
            await message.answer(
                f"❌ O‘yinni boshlash uchun kamida {MIN_PLAYERS} o‘yinchi kerak.\n"
                f"Hozir: {len(players)}/{MAX_PLAYERS}"
            )
            return

        # O'yin holatini bazada saqlaymiz.
        await database.update_game(
            game_id,
            phase="ROLE_REVEAL",
        )

        if chat_id in active_games:
            active_games[chat_id]["phase"] = "ROLE_REVEAL"

    await message.answer(
        "👑 <b>THRONE</b>\n\n"
        f"⚔️ O‘yin boshlanishi tasdiqlandi!\n"
        f"👥 Ishtirokchilar: {len(players)}\n\n"
        "⚠️ Rollarni taqsimlash va tun bosqichini boshlash "
        "keyingi integratsiya bosqichida ulanadi."
      )
