
import asyncio
import logging
import uuid

import aiosqlite
from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from database import Database
from game_engine import Game
from role_assignment import assign_roles
from roles import ROLES


logger = logging.getLogger("THRONE.game_handlers")
router = Router(name="throne_game_handlers")

database = Database(settings.database_path)

MIN_PLAYERS = 7
MAX_PLAYERS = 36

# Guruhdagi joriy o'yinlar.
active_games: dict[int, dict] = {}

# Bir guruhda bir vaqtning o'zida ikkita o'yin ochilmasin.
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
    """Foydalanuvchi guruh administratori ekanini tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }
    except Exception:
        logger.exception("Guruh administratorini tekshirishda xatolik")
        return False


async def get_database_active_game(chat_id: int):
    """Guruhda tugamagan o'yin borligini bazadan tekshiradi."""
    await database.initialize()

    async with aiosqlite.connect(database.database_path) as db:
        cursor = await db.execute(
            """
            SELECT game_id, creator_id, phase
            FROM games
            WHERE chat_id = ?
              AND UPPER(phase) NOT IN ('FINISHED', 'STOPPED')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (chat_id,),
        )
        return await cursor.fetchone()


async def get_game_players(game_id: str) -> list[int]:
    """O'yin ishtirokchilarining Telegram ID raqamlarini qaytaradi."""
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
        return [int(row[0]) for row in rows]


async def get_game_player_details(game_id: str) -> list[dict]:
    """O'yinchilar va ularning ismlarini bazadan oladi."""
    await database.initialize()

    async with aiosqlite.connect(database.database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT gp.user_id, p.full_name, p.username
            FROM game_players AS gp
            LEFT JOIN players AS p ON p.user_id = gp.user_id
            WHERE gp.game_id = ?
            ORDER BY gp.joined_at ASC
            """,
            (game_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.message(Command("newgame"))
async def new_game(message: Message, bot: Bot) -> None:
    """Guruhda yangi o'yin uchun lobbi ochadi."""
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

    async with get_group_lock(chat_id):
        existing = await get_database_active_game(chat_id)

        if existing is not None:
            await message.answer(
                "⚔️ Bu guruhda allaqachon faol o‘yin bor.\n\n"
                "Avval joriy o‘yin tugashi kerak."
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
            await database.add_history(
                game_id,
                "LOBBY_CREATED",
                "Yangi o‘yin uchun lobbi ochildi.",
            )
        except Exception:
            logger.exception("Lobbi yaratishda xatolik")
            await message.answer(
                "❌ O‘yinni yaratib bo‘lmadi. Qayta urinib ko‘ring."
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
        f"⚔️ Boshlash uchun kamida {MIN_PLAYERS} kishi kerak.\n\n"
        "O‘yinga qo‘shilish uchun tugmani bosing.\n"
        "Guruh administratori /startgame buyrug‘i bilan boshlaydi.",
        reply_markup=lobby_keyboard(game_id),
    )


@router.callback_query(
    lambda query: (
        query.data is not None
        and query.data.startswith("throne_join:")
    )
)
async def join_game(query: CallbackQuery, bot: Bot) -> None:
    """Foydalanuvchini faol lobbiga qo'shadi."""
    if not query.from_user or not query.message:
        await query.answer(
            "O‘yin ma’lumotlari topilmadi.",
            show_alert=True,
        )
        return

    chat = query.message.chat

    if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await query.answer(
            "Guruhdagi o‘yin tugmasidan foydalaning.",
            show_alert=True,
        )
        return

    game_id = query.data.split(":", 1)[1]
    chat_id = chat.id
    user = query.from_user

    async with get_group_lock(chat_id):
        existing = await get_database_active_game(chat_id)

        if existing is None or existing[0] != game_id:
            await query.answer(
                "Bu o‘yin endi faol emas.",
                show_alert=True,
            )
            return

        if str(existing[2]).upper() != "LOBBY":
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

        try:
            await database.ensure_player(
                user_id=user.id,
                full_name=user.full_name,
                username=user.username,
            )
            await database.add_game_player(
                game_id=game_id,
                user_id=user.id,
            )
            await database.add_history(
                game_id,
                "PLAYER_JOINED",
                f"{user.full_name} o‘yinga qo‘shildi.",
            )
        except Exception:
            logger.exception("O'yinchini qo'shishda xatolik")
            await query.answer(
                "Qo‘shilishda xatolik yuz berdi. Qayta urinib ko‘ring.",
                show_alert=True,
            )
            return

        updated_count = len(players) + 1

        if chat_id in active_games:
            active_games[chat_id]["players"] = players + [user.id]

    await query.answer("Siz o‘yinga qo‘shildingiz!")

    try:
        await query.message.edit_text(
            "👑 <b>THRONE — Yangi o‘yin</b>\n\n"
            "🏰 Qirollik eshiklari ochiq!\n"
            f"👥 O‘yinchilar: {updated_count}/{MAX_PLAYERS}\n"
            f"⚔️ Boshlash uchun kamida {MIN_PLAYERS} kishi kerak.\n\n"
            "Guruh administratori /startgame orqali o‘yinni boshlaydi.",
            reply_markup=lobby_keyboard(game_id),
        )
    except Exception:
        logger.debug(
            "Lobbi xabarini yangilab bo‘lmadi.",
            exc_info=True,
        )


@router.message(Command("startgame"))
async def start_game(message: Message, bot: Bot) -> None:
    """O'yinni boshlaydi, rollarni tarqatadi va birinchi tunni ochadi."""
    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer("O‘yinni guruhda boshlash kerak.")
        return

    if not message.from_user:
        return

    chat_id = message.chat.id
    requester_id = message.from_user.id

    if not await is_group_admin(bot, chat_id, requester_id):
        await message.answer(
            "🔒 O‘yinni faqat guruh administratori boshlashi mumkin."
        )
        return

    # Avval lobbi ma'lumotlarini tekshirib, o'yinni ROLE_REVEAL holatiga o'tkazamiz.
    async with get_group_lock(chat_id):
        existing = await get_database_active_game(chat_id)

        if existing is None:
            await message.answer(
                "❌ Faol lobbi topilmadi. /newgame orqali yangi o‘yin oching."
            )
            return

        game_id, creator_id, phase = existing

        if str(phase).upper() != "LOBBY":
            await message.answer(
                "⚔️ O‘yin allaqachon boshlangan yoki faol bosqichda."
            )
            return

        player_rows = await get_game_player_details(game_id)
        player_ids = [int(row["user_id"]) for row in player_rows]

        if len(player_ids) < MIN_PLAYERS:
            await message.answer(
                f"❌ Boshlash uchun kamida {MIN_PLAYERS} o‘yinchi kerak.\n"
                f"Hozir: {len(player_ids)}/{MAX_PLAYERS}"
            )
            return

        if len(player_ids) > MAX_PLAYERS:
            await message.answer(
                f"❌ O‘yinchilar soni {MAX_PLAYERS} nafardan oshmasligi kerak."
            )
            return

        game = Game(
            chat_id=chat_id,
            creator_id=int(creator_id),
            game_id=str(game_id),
        )

        for row in player_rows:
            user_id = int(row["user_id"])
            name = row["full_name"] or str(user_id)
            username = row["username"]

            added, error_message = game.add_player(
                user_id=user_id,
                name=name,
                username=username,
            )
            if not added:
                await message.answer(f"❌ {error_message}")
                return

        started, start_message = game.start(requester_is_admin=True)
        if not started:
            await message.answer(f"❌ {start_message}")
            return

        # Rollarning tasodifiy taqsimoti.
        result = assign_roles(game)

        if not result.success:
            await message.answer(
                f"❌ Rollarni taqsimlab bo‘lmadi: {result.message}"
            )
            return

        # Rollarni ma'lumotlar bazasiga yozamiz.
        try:
            for user_id, role in result.assignments.items():
                await database.update_game_player(
                    str(game_id),
                    int(user_id),
                    role_id=role.id,
                    team=role.team.value,
                )

            await database.update_game(
                str(game_id),
                phase="ROLE_REVEAL",
                round_number=0,
            )
            await database.add_history(
                str(game_id),
                "ROLES_ASSIGNED",
                f"{len(player_ids)} o‘yinchiga rollar taqsimlandi.",
            )
        except Exception:
            logger.exception("Rollarni bazaga saqlashda xatolik")
            await message.answer(
                "❌ Rollarni saqlashda xatolik yuz berdi. "
                "O‘yin boshlanmadi."
            )
            return

        active_games[chat_id] = {
            "game_id": str(game_id),
            "creator_id": int(creator_id),
            "players": player_ids,
            "phase": "ROLE_REVEAL",
            "game": game,
        }

    # Har bir o'yinchiga rolini shaxsiy xabarda yuboramiz.
    failed_users: list[int] = []

    for user_id, role in result.assignments.items():
        role_name = role.name
        team_name = role.team.value

        private_text = (
            "👑 <b>THRONE — Sizning rolingiz</b>\n\n"
            f"🎭 <b>Rol:</b> {role_name}\n"
            f"🏰 <b>Jamoa:</b> {team_name}\n\n"
            f"⚔️ <b>Qobiliyat:</b> {role.ability}\n"
            f"🏆 <b>Maqsad:</b> {role.win_condition}\n\n"
            "🤫 Rolingizni boshqa o‘yinchilarga oshkor qilmang."
        )

        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=private_text,
                parse_mode="HTML",
            )
        except Exception:
            logger.warning(
                "Rolni shaxsiy xabarda yuborib bo'lmadi: user_id=%s",
                user_id,
            )
            failed_users.append(int(user_id))

    # Telegram bot foydalanuvchi bilan avval shaxsiy chat ochmagan bo'lsa,
    # bot unga birinchi bo'lib yozolmasligi mumkin.
    if failed_users:
        async with get_group_lock(chat_id):
            await database.update_game(
                str(game_id),
                phase="STOPPED",
                finished=True,
            )
            await database.add_history(
                str(game_id),
                "GAME_STOPPED",
                "Ayrim o‘yinchilarga rolni shaxsiy xabarda yuborib bo‘lmadi.",
            )

            if chat_id in active_games:
                active_games[chat_id]["phase"] = "STOPPED"

        await message.answer(
            "⛔ <b>O‘yin to‘xtatildi.</b>\n\n"
            "Quyidagi o‘yinchilarga shaxsiy xabar yuborilmadi:\n"
            f"👥 Soni: {len(failed_users)}\n\n"
            "Ular botni ochib, /start buyrug‘ini yuborishlari kerak. "
            "Shundan so‘ng /newgame orqali yangi o‘yin oching."
        )
        return

    # Barcha rollar yuborilgach, birinchi tunni boshlaymiz.
    night_started, night_message = game.begin_night()

    if not night_started:
        async with get_group_lock(chat_id):
            await database.update_game(
                str(game_id),
                phase="STOPPED",
                finished=True,
            )
            await database.add_history(
                str(game_id),
                "GAME_STOPPED",
                f"Birinchi tunni boshlash xatosi: {night_message}",
            )
            if chat_id in active_games:
                active_games[chat_id]["phase"] = "STOPPED"

        await message.answer(
            "❌ Birinchi tunni boshlashda xatolik yuz berdi. "
            "O‘yin to‘xtatildi."
        )
        return

    async with get_group_lock(chat_id):
        await database.update_game(
            str(game_id),
            phase=game.phase.value,
            round_number=game.round_number,
        )
        await database.add_history(
            str(game_id),
            "NIGHT_STARTED",
            f"{game.round_number}-tun boshlandi.",
        )

        if chat_id in active_games:
            active_games[chat_id]["phase"] = game.phase.value
            active_games[chat_id]["game"] = game

    await message.answer(
        "👑 <b>THRONE — O‘YIN BOSHLANDI</b>\n\n"
        f"👥 <b>Ishtirokchilar:</b> {len(player_ids)}\n"
        "🎭 Rollar o‘yinchilarga shaxsiy xabarda yuborildi.\n\n"
        f"🌙 <b>{game.round_number}-tun boshlandi.</b>\n"
        "Har bir o‘yinchi o‘z rolini sir saqlashi kerak."
        )
                                                  
