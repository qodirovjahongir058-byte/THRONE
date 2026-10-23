
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

router = Router()

# Hozircha lobbylar xotirada saqlanadi.
# Keyingi bosqichda ularni ma'lumotlar bazasiga o'tkazamiz.
LOBBIES: dict[int, dict] = {}

MAX_PLAYERS = 30
MIN_PLAYERS = 4


def lobby_keyboard(group_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ O‘yinga qo‘shilish",
                    callback_data=f"game:join:{group_id}",
                )
            ]
        ]
    )


def lobby_text(lobby: dict) -> str:
    players = lobby["players"]
    return (
        "👑 <b>THRONE — YANGI O‘YIN</b>\n\n"
        "🏰 Qirollik uchun kurash boshlanish arafasida!\n"
        "⚔️ O‘yinga qo‘shilish uchun tugmani bosing.\n\n"
        f"👥 O‘yinchilar: <b>{len(players)}/{MAX_PLAYERS}</b>\n"
        f"🎮 Boshlash uchun kamida {MIN_PLAYERS} o‘yinchi kerak."
    )


@router.message(Command("NewGame", ignore_case=True))
async def new_game_handler(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(
            "🏰 Yangi o‘yinni ochish uchun botni guruhda ishlating."
        )
        return

    group_id = message.chat.id

    if group_id in LOBBIES:
        await message.answer("⚔️ Bu guruhda lobby allaqachon ochilgan.")
        return

    LOBBIES[group_id] = {
        "players": {},
        "status": "lobby",
        "message_id": None,
    }

    sent = await message.answer(
        lobby_text(LOBBIES[group_id]),
        reply_markup=lobby_keyboard(group_id),
    )

    LOBBIES[group_id]["message_id"] = sent.message_id


@router.callback_query(F.data.startswith("game:join:"))
async def join_game_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("❌ So‘rovni bajarib bo‘lmadi.", show_alert=True)
        return

    try:
        group_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer("❌ Noto‘g‘ri so‘rov.", show_alert=True)
        return

    lobby = LOBBIES.get(group_id)

    if lobby is None or lobby["status"] != "lobby":
        await callback.answer("❌ Bu lobby faol emas.", show_alert=True)
        return

    if callback.message.chat.id != group_id:
        await callback.answer("❌ Bu tugma boshqa guruhga tegishli.", show_alert=True)
        return

    user = callback.from_user
    players = lobby["players"]

    if user.id in players:
        await callback.answer("✅ Siz allaqachon o‘yindasiz.")
        return

    if len(players) >= MAX_PLAYERS:
        await callback.answer("❌ Lobby to‘la!", show_alert=True)
        return

    players[user.id] = {
        "name": user.full_name,
        "username": user.username,
    }

    await callback.message.edit_text(
        lobby_text(lobby),
        reply_markup=lobby_keyboard(group_id),
    )
    await callback.answer("👑 Siz o‘yinga qo‘shildingiz!")
    
