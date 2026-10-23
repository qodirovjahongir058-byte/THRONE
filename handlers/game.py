
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

router = Router()

# Hozircha lobbylar xotirada saqlanadi.
# Keyin ma'lumotlar bazasiga ko'chiramiz.
LOBBIES: dict[int, dict] = {}

MAX_PLAYERS = 30
MIN_PLAYERS = 4


def lobby_keyboard(group_id: int) -> InlineKeyboardMarkup:
    """Lobby tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ O‘yinga qo‘shilish",
                    callback_data=f"game:join:{group_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 O‘yinni boshlash",
                    callback_data=f"game:start:{group_id}",
                )
            ],
        ]
    )


def lobby_text(lobby: dict) -> str:
    """Lobbydagi o‘yinchilar ro‘yxati."""
    players = lobby["players"]
    names = [
        f"• {player['name']}"
        for player in players.values()
    ]

    player_list = "\n".join(names) if names else "Hali hech kim qo‘shilmadi."

    return (
        "👑 <b>THRONE — YANGI O‘YIN</b>\n\n"
        "🏰 Qirollik uchun kurash boshlanish arafasida!\n"
        "⚔️ O‘yinga qo‘shilish uchun tugmani bosing.\n\n"
        f"👥 O‘yinchilar: <b>{len(players)}/{MAX_PLAYERS}</b>\n"
        f"🎮 Boshlash uchun kamida {MIN_PLAYERS} o‘yinchi kerak.\n\n"
        f"<b>Ro‘yxat:</b>\n{player_list}"
    )


@router.message(Command("NewGame", ignore_case=True))
async def new_game_handler(message: Message) -> None:
    """Guruhda yangi lobby ochish."""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(
            "🏰 Yangi o‘yinni ochish uchun botni guruhda ishlating."
        )
        return

    group_id = message.chat.id

    if group_id in LOBBIES:
        await message.answer(
            "⚔️ Bu guruhda lobby allaqachon ochilgan."
        )
        return

    LOBBIES[group_id] = {
        "players": {},
        "status": "lobby",
        "message_id": None,
        "creator_id": (
            message.from_user.id
            if message.from_user
            else None
        ),
    }

    sent = await message.answer(
        lobby_text(LOBBIES[group_id]),
        reply_markup=lobby_keyboard(group_id),
    )

    LOBBIES[group_id]["message_id"] = sent.message_id


@router.callback_query(F.data.startswith("game:join:"))
async def join_game_handler(callback: CallbackQuery) -> None:
    """O‘yinchining lobbyga qo‘shilishi."""
    if (
        callback.from_user is None
        or callback.message is None
        or not callback.data
    ):
        await callback.answer(
            "❌ So‘rovni bajarib bo‘lmadi.",
            show_alert=True,
        )
        return

    try:
        group_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer(
            "❌ Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    lobby = LOBBIES.get(group_id)

    if (
        lobby is None
        or lobby["status"] != "lobby"
        or callback.message.chat.id != group_id
    ):
        await callback.answer(
            "❌ Bu lobby faol emas.",
            show_alert=True,
        )
        return

    user = callback.from_user
    players = lobby["players"]

    if user.id in players:
        await callback.answer(
            "✅ Siz allaqachon o‘yindasiz."
        )
        return

    if len(players) >= MAX_PLAYERS:
        await callback.answer(
            "❌ Lobby to‘la!",
            show_alert=True,
        )
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


@router.callback_query(F.data.startswith("game:start:"))
async def start_game_handler(callback: CallbackQuery) -> None:
    """Guruh administratori yoki yaratuvchi lobby o‘yinini boshlaydi."""
    if (
        callback.from_user is None
        or callback.message is None
        or not callback.data
    ):
        await callback.answer(
            "❌ So‘rovni bajarib bo‘lmadi.",
            show_alert=True,
        )
        return

    try:
        group_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer(
            "❌ Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    lobby = LOBBIES.get(group_id)

    if (
        lobby is None
        or lobby["status"] != "lobby"
        or callback.message.chat.id != group_id
    ):
        await callback.answer(
            "❌ Bu lobby faol emas.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id

    # Lobby yaratuvchisi yoki guruh administratori boshlashi mumkin.
    is_creator = user_id == lobby["creator_id"]
    is_admin = False

    try:
        member = await callback.bot.get_chat_member(
            chat_id=group_id,
            user_id=user_id,
        )
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False

    if not is_creator and not is_admin:
        await callback.answer(
            "⛔ O‘yinni faqat lobby yaratuvchisi "
            "yoki guruh administratori boshlashi mumkin.",
            show_alert=True,
        )
        return

    if len(lobby["players"]) < MIN_PLAYERS:
        await callback.answer(
            f"👥 O‘yinni boshlash uchun kamida "
            f"{MIN_PLAYERS} o‘yinchi kerak.",
            show_alert=True,
        )
        return

    # Bu bosqichda faqat boshlanish holati belgilanadi.
    # Rollarni taqsimlash keyingi bosqichda qo‘shiladi.
    lobby["status"] = "starting"

    await callback.message.edit_text(
        "👑 <b>THRONE — O‘YIN BOSHLANMOQDA!</b>\n\n"
        f"👥 O‘yinchilar: <b>{len(lobby['players'])}</b>\n"
        "🎭 Keyingi bosqichda rollar taqsimlanadi.",
        reply_markup=None,
    )

    await callback.answer("⚔️ O‘yin boshlanishi tasdiqlandi!")
        
