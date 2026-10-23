
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from roles import (
    MIN_PLAYERS,
    MAX_PLAYERS,
    assign_roles,
)

router = Router()

# Hozircha lobbylar xotirada saqlanadi.
# Bot qayta ishga tushsa, lobbylar yo'qoladi.
LOBBIES: dict[int, dict] = {}


def lobby_keyboard(group_id: int) -> InlineKeyboardMarkup:
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
    players = lobby["players"]

    names = [
        f"• {player['name']}"
        for player in players.values()
    ]
    player_list = (
        "\n".join(names)
        if names
        else "Hali hech kim qo‘shilmadi."
    )

    return (
        "👑 <b>THRONE — YANGI O‘YIN</b>\n\n"
        "🏰 Qirollik uchun kurash boshlanish arafasida!\n"
        "⚔️ Qo‘shilish tugmasini bosing.\n\n"
        f"👥 O‘yinchilar: <b>{len(players)}/{MAX_PLAYERS}</b>\n"
        f"🎮 Boshlash uchun kamida {MIN_PLAYERS} o‘yinchi kerak.\n\n"
        f"<b>Ishtirokchilar:</b>\n{player_list}"
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
        await message.answer(
            "⚔️ Bu guruhda lobby allaqachon ochilgan."
        )
        return

    creator_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    LOBBIES[group_id] = {
        "players": {},
        "status": "lobby",
        "message_id": None,
        "creator_id": creator_id,
    }

    sent = await message.answer(
        lobby_text(LOBBIES[group_id]),
        reply_markup=lobby_keyboard(group_id),
    )

    LOBBIES[group_id]["message_id"] = sent.message_id


@router.callback_query(F.data.startswith("game:join:"))
async def join_game_handler(callback: CallbackQuery) -> None:
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
            "⛔ Lobby yaratuvchisi yoki guruh administratori "
            "o‘yinni boshlashi mumkin.",
            show_alert=True,
        )
        return

    players = lobby["players"]

    if len(players) < MIN_PLAYERS:
        await callback.answer(
            f"👥 Kamida {MIN_PLAYERS} o‘yinchi kerak.",
            show_alert=True,
        )
        return

    if len(players) > MAX_PLAYERS:
        await callback.answer(
            "❌ O‘yinchilar soni ruxsat etilgan chegaradan oshdi.",
            show_alert=True,
        )
        return

    # Ikki marta boshlashga urinishning oldini olish.
    lobby["status"] = "assigning"

    try:
        assignments = assign_roles(list(players.keys()))
    except (ValueError, IndexError):
        lobby["status"] = "lobby"
        await callback.answer(
            "⚠️ Rollarni taqsimlashda xatolik yuz berdi.",
            show_alert=True,
        )
        return

    delivered = []
    failed = []

    # Rollar faqat o'yinchilarning shaxsiy chatiga yuboriladi.
    for player_id, role in assignments.items():
        try:
            await callback.bot.send_message(
                chat_id=player_id,
                text=(
                    "👑 <b>THRONE — SIZNING ROLINGIZ</b>\n\n"
                    f"🎭 Rol: <b>{role.name}</b>\n"
                    f"🛡️ Jamoa: <b>{role.faction}</b>\n\n"
                    f"📜 {role.description}\n\n"
                    "🤫 Roolingizni guruhda oshkor qilmang."
                ),
            )
            delivered.append(player_id)
        except Exception:
            failed.append(player_id)

    if failed:
        # O'yin boshlanmaydi; yuborilgan vaqtinchalik
        # xabarlar ham bekor qilinadi.
        for player_id in delivered:
            try:
                await callback.bot.send_message(
                    chat_id=player_id,
                    text=(
                        "⚠️ <b>O‘YIN BOSHLANMADI</b>\n\n"
                        "Rol xabari sinov tariqasida yuborilgan edi. "
                        "Bu rol hozircha amal qilmaydi."
                    ),
                )
            except Exception:
                pass

        lobby["status"] = "lobby"

        await callback.message.answer(
            "⚠️ Ayrim o‘yinchilarga shaxsiy xabar yuborilmadi.\n\n"
            "Ular botga shaxsiy chatda /start yuborishsin. "
            "So‘ng o‘yinni qayta boshlashga urinib ko‘ring."
        )
        await callback.answer(
            "❌ Barcha rollar yuborilmadi.",
            show_alert=True,
        )
        return

    lobby["status"] = "starting"
    lobby["assignments"] = {
        player_id: role.id
        for player_id, role in assignments.items()
    }

    await callback.message.edit_text(
        "👑 <b>THRONE — ROLLAR TAQSIMLANDI!</b>\n\n"
        f"👥 O‘yinchilar: <b>{len(players)}</b>\n"
        "🎭 Har bir ishtirokchiga roli shaxsiy xabarda yuborildi.\n\n"
        "⏳ Keyingi bosqichda o‘yin fazalari va tungi "
        "harakatlar ulanadi.",
        reply_markup=None,
    )

    await callback.answer("👑 Rollar yuborildi!")
            
