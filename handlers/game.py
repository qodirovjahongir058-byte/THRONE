from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from game_actions import ActionType, create_action
from game_controller import start_first_night
from game_engine import GameState, PlayerState
from game_flow import game_flow
from game_messages import (
    game_full_message,
    game_stopped_message,
    lobby_message,
    not_enough_players_message,
    permission_denied_message,
    player_already_joined_message,
    player_joined_message,
    role_reveal_message,
    target_not_alive_message,
    target_not_found_message,
)
from game_service import game_service
from game_state import (
    GamePhase,
    GameStatus,
    MAX_PLAYERS,
    MIN_PLAYERS,
)
from keyboards import (
    lobby_keyboard,
    night_action_keyboard,
    target_keyboard,
)
from last_words import last_words_system
from role_engine import build_role_runtime_info
from role_notifications import send_roles_to_all_players
from vote_system import vote_system


logger = logging.getLogger(__name__)

router = Router(name="throne_game")


# ============================================================
# UMUMIY YORDAMCHI FUNKSIYALAR
# ============================================================

def _is_group(message: Message) -> bool:
    """Xabar guruhdan kelganini tekshirish."""
    return message.chat.type in {"group", "supergroup"}


async def _is_chat_admin(
    message: Message,
    user_id: int,
) -> bool:
    """Foydalanuvchi guruh administratori ekanini tekshirish."""
    try:
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
        )

        return member.status in {"administrator", "creator"}

    except TelegramAPIError:
        logger.exception(
            "Guruh administratori tekshiruvida xato: chat_id=%s",
            message.chat.id,
        )
        return False


def _display_name(player: PlayerState) -> str:
    """O'yinchining ko'rsatiladigan ismi."""
    return player.display_name or f"User {player.user_id}"


def _find_player_game(
    user_id: int,
    required_phase: GamePhase,
) -> GameState | None:
    """
    Foydalanuvchi qatnashayotgan kerakli bosqichdagi o'yinni topish.

    Agar foydalanuvchi bir nechta mos o'yinda qatnashsa,
    noto'g'ri o'yinga harakat yubormaslik uchun None qaytariladi.
    """
    matches = [
        game
        for game in game_service._games.values()
        if game.get_player(user_id) is not None
        and game.phase == required_phase
        and game.status == GameStatus.ACTIVE
    ]

    if len(matches) != 1:
        if len(matches) > 1:
            logger.warning(
                "Foydalanuvchi bir nechta mos o'yinda qatnashmoqda: "
                "user_id=%s, phase=%s",
                user_id,
                required_phase.value,
            )
        return None

    return matches[0]


def _action_label(action_type: ActionType) -> str:
    """Tungi harakat uchun tugma matni."""
    labels = {
        ActionType.OBSERVE: "👁 Kuzatish",
        ActionType.PROTECT: "🛡 Himoya",
        ActionType.BLOCK: "🔒 Bloklash",
        ActionType.POISON: "☠️ Zaharlash",
        ActionType.WEAKEN: "🩸 Zaiflashtirish",
        ActionType.ATTACK: "⚔️ Hujum",
        ActionType.SPECIAL: "✨ Maxsus",
    }

    return labels.get(action_type, "✨ Maxsus")


def _get_alive_targets(
    game: GameState,
    actor_id: int,
) -> list[tuple[int, str]]:
    """Tirik va o'zidan boshqa o'yinchilar ro'yxati."""
    return [
        (player.user_id, _display_name(player))
        for player in game.alive_players()
        if player.user_id != actor_id
    ]


# ============================================================
# TUNGI HARAKATLARNI SHAXSIY XABARDA YUBORISH
# ============================================================

async def _send_night_actions(
    bot,
    game: GameState,
) -> None:
    """
    Har bir tirik o'yinchiga uning roliga mos tungi
    harakat tugmalarini yuborish.

    Bir o'yinchiga xabar yuborilmasa, qolgan o'yinchilar
    uchun yuborish davom etadi.
    """
    for player in game.alive_players():
        runtime_info = build_role_runtime_info(player)

        if runtime_info is None:
            logger.warning(
                "O'yinchi roli aniqlanmadi: user_id=%s",
                player.user_id,
            )
            continue

        buttons: list[tuple[str, str]] = []

        for rule in runtime_info.action_rules:
            buttons.append(
                (
                    _action_label(rule.action_type),
                    (
                        "throne:night:"
                        f"{rule.action_type.value}:"
                        f"{1 if rule.requires_target else 0}"
                    ),
                )
            )

        if buttons:
            text = (
                "🌙 <b>Tun boshlandi.</b>\n\n"
                "O'z rolingiz uchun mavjud tungi "
                "harakatni tanlang."
            )
            markup = night_action_keyboard(buttons)
        else:
            text = (
                "🌙 <b>Tun boshlandi.</b>\n\n"
                "Sizning rolingizda bu tun uchun "
                "faol tungi qobiliyat mavjud emas."
            )
            markup = None

        try:
            await bot.send_message(
                chat_id=player.user_id,
                text=text,
                reply_markup=markup,
            )

        except TelegramAPIError:
            logger.warning(
                "Tungi xabar yuborilmadi: user_id=%s",
                player.user_id,
                exc_info=True,
            )


# ============================================================
# YANGI O'YIN OCHISH
# ============================================================

@router.message(Command("newgame"))
async def new_game_handler(
    message: Message,
) -> None:
    """Guruhda yangi THRONE o'yinini ochish."""

    if not _is_group(message):
        await message.answer(
            "⚠️ <b>THRONE</b> o'yini faqat guruhlarda boshlanadi."
        )
        return

    if message.from_user is None:
        return

    if not await _is_chat_admin(
        message,
        message.from_user.id,
    ):
        await message.answer(permission_denied_message())
        return

    result = game_service.create_game(
        chat_id=message.chat.id,
    )

    if not result.success or result.game is None:
        await message.answer(
            "⚠️ Bu guruhda allaqachon faol o'yin mavjud."
        )
        return

    await message.answer(
        lobby_message(
            player_count=result.game.player_count(),
            min_players=MIN_PLAYERS,
            max_players=MAX_PLAYERS,
        ),
        reply_markup=lobby_keyboard(),
    )


# ============================================================
# O'YINGA QO'SHILISH
# ============================================================

@router.callback_query(F.data == "throne:join")
async def join_game_handler(
    callback: CallbackQuery,
) -> None:
    """O'yinchini kutish xonasiga qo'shish."""

    if callback.message is None:
        await callback.answer()
        return

    user = callback.from_user
    chat_id = callback.message.chat.id

    game = game_service.get_game(chat_id)

    if game is None:
        await callback.answer(
            "O'yin topilmadi.",
            show_alert=True,
        )
        return

    if game.phase != GamePhase.LOBBY:
        await callback.answer(
            "O'yin boshlangan yoki kutish xonasi yopilgan.",
            show_alert=True,
        )
        return

    if game.player_count() >= MAX_PLAYERS:
        await callback.answer(
            game_full_message(),
            show_alert=True,
        )
        return

    player = PlayerState(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    result = game_service.add_player(
        chat_id=chat_id,
        player=player,
    )

    if not result.success or result.game is None:
        if result.message == "player_already_joined":
            answer = player_already_joined_message()
        elif result.message == "game_full":
            answer = game_full_message()
        else:
            answer = "⚠️ O'yinga qo'shilib bo'lmadi."

        await callback.answer(
            answer,
            show_alert=True,
        )
        return

    await callback.answer("Siz o'yinga qo'shildingiz!")

    try:
        await callback.message.edit_text(
            lobby_message(
                player_count=result.game.player_count(),
                min_players=MIN_PLAYERS,
                max_players=MAX_PLAYERS,
            ),
            reply_markup=lobby_keyboard(),
        )
    except TelegramAPIError:
        logger.warning(
            "Kutish xonasi xabarini yangilab bo'lmadi.",
            exc_info=True,
        )

    await callback.message.answer(
        player_joined_message(
            display_name=_display_name(player),
            player_count=result.game.player_count(),
            max_players=MAX_PLAYERS,
        )
    )


# ============================================================
# O'YINCHILAR RO'YXATI
# ============================================================

@router.callback_query(F.data == "throne:players")
async def players_handler(
    callback: CallbackQuery,
) -> None:
    """Kutish xonasidagi o'yinchilarni ko'rsatish."""

    if callback.message is None:
        await callback.answer()
        return

    game = game_service.get_game(
        callback.message.chat.id
    )

    if game is None:
        await callback.answer(
            "O'yin topilmadi.",
            show_alert=True,
        )
        return

    if not game.players:
        await callback.answer(
            "Hali hech kim qo'shilmagan.",
            show_alert=True,
        )
        return

    players = "\n".join(
        f"• {_display_name(player)}"
        for player in game.players.values()
    )

    await callback.answer()

    await callback.message.answer(
        "👥 <b>O'yinchilar</b>\n\n"
        f"{players}\n\n"
        f"Jami: <b>{game.player_count()}/{MAX_PLAYERS}</b>"
    )


# ============================================================
# O'YINNI BOSHLASH
# ============================================================

@router.callback_query(F.data == "throne:start")
async def start_game_handler(
    callback: CallbackQuery,
) -> None:
    """Rollarni taqsimlash va birinchi tunni boshlash."""

    if callback.message is None:
        await callback.answer()
        return

    message = callback.message
    user = callback.from_user

    if not _is_group(message):
        await callback.answer(
            "O'yinni faqat guruhda boshlash mumkin.",
            show_alert=True,
        )
        return

    if not await _is_chat_admin(message, user.id):
        await callback.answer(
            "Faqat guruh administratori o'yinni boshlashi mumkin.",
            show_alert=True,
        )
        return

    game = game_service.get_game(message.chat.id)

    if game is None:
        await callback.answer(
            "O'yin topilmadi.",
            show_alert=True,
        )
        return

    if game.phase != GamePhase.LOBBY:
        await callback.answer(
            "O'yin allaqachon boshlangan.",
            show_alert=True,
        )
        return

    if not MIN_PLAYERS <= game.player_count() <= MAX_PLAYERS:
        await callback.answer(
            not_enough_players_message(
                current_count=game.player_count(),
                min_players=MIN_PLAYERS,
            ),
            show_alert=True,
        )
        return

    result = game_service.start_game(
        chat_id=message.chat.id,
    )

    if not result.success or result.game is None:
        await callback.answer(
            "O'yinni boshlashda xatolik yuz berdi.",
            show_alert=True,
        )
        return

    game = result.game

    await callback.answer("O'yin boshlandi!")

    try:
        delivery_results = await send_roles_to_all_players(
            bot=message.bot,
            game=game,
        )
    except Exception:
        logger.exception(
            "Rollarni yuborishda xatolik: game_id=%s",
            game.game_id,
        )
        delivery_results = {}

    failed_count = sum(
        1
        for delivered in delivery_results.values()
        if not delivered
    )

    try:
        await message.edit_text(role_reveal_message())
    except TelegramAPIError:
        logger.warning(
            "Kutish xonasi xabarini yangilab bo'lmadi.",
            exc_info=True,
        )

    if failed_count > 0 or len(delivery_results) < game.player_count():
        await message.answer(
            "📜 <b>Rollar taqsimlandi.</b>\n\n"
            "⚠️ Ayrim o'yinchilarga shaxsiy xabar yetib bormadi. "
            "Ular botga kirib, <b>/start</b> yuborishi kerak."
        )
    else:
        await message.answer(
            "⚔️ <b>O'yin boshlandi!</b>\n\n"
            "📜 Rollar o'yinchilarga shaxsiy xabarda yuborildi."
        )

    try:
        night_started = await start_first_night(
            bot=message.bot,
            game=game,
        )
    except Exception:
        logger.exception(
            "Birinchi tunni boshlashda xatolik: game_id=%s",
            game.game_id,
        )
        night_started = False

    if not night_started:
        await message.answer(
            "⚠️ Birinchi tunni boshlashda xatolik yuz berdi. "
            "Administrator loglarni tekshirishi kerak."
        )
        return

    await _send_night_actions(
        bot=message.bot,
        game=game,
    )


# ============================================================
# TUNGI HARAKATNI TANLASH
# ============================================================

@router.callback_query(F.data.startswith("throne:night:"))
async def night_action_handler(
    callback: CallbackQuery,
) -> None:
    """Tungi harakatni tanlash va nishon so'rash."""

    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")

    if len(parts) != 4:
        await callback.answer(
            "⚠️ Harakat ma'lumotlari noto'g'ri.",
            show_alert=True,
        )
        return

    _, _, action_value, requires_target_value = parts

    if requires_target_value not in {"0", "1"}:
        await callback.answer(
            "⚠️ Harakat ma'lumotlari noto'g'ri.",
            show_alert=True,
        )
        return

    try:
        action_type = ActionType(action_value)
    except ValueError:
        await callback.answer(
            "⚠️ Noma'lum tungi harakat.",
            show_alert=True,
        )
        return

    requires_target = requires_target_value == "1"

    game = _find_player_game(
        user_id=callback.from_user.id,
        required_phase=GamePhase.NIGHT,
    )

    if game is None:
        await callback.answer(
            "🌙 Siz uchun faol tun topilmadi.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id
    player = game.get_player(user_id)

    if player is None or not player.alive:
        await callback.answer(
            "Siz bu vaqtda harakat qila olmaysiz.",
            show_alert=True,
        )
        return

    runtime_info = build_role_runtime_info(player)

    if runtime_info is None:
        await callback.answer(
            "⚠️ Roli aniqlanmadi.",
            show_alert=True,
        )
        return

    rule = next(
        (
            item
            for item in runtime_info.action_rules
            if item.action_type == action_type
        ),
        None,
    )

    if rule is None:
        await callback.answer(
            "Bu harakat sizning rolingizga tegishli emas.",
            show_alert=True,
        )
        return

    if rule.requires_target != requires_target:
        await callback.answer(
            "⚠️ Harakat turi mos kelmadi.",
            show_alert=True,
        )
        return

    if requires_target:
        targets = _get_alive_targets(
            game=game,
            actor_id=user_id,
        )

        if not targets:
            await callback.answer(
                "Hozir nishon mavjud emas.",
                show_alert=True,
            )
            return

        await callback.answer()

        await callback.message.edit_text(
            "🌙 <b>Nishonni tanlang:</b>",
            reply_markup=target_keyboard(
                targets=targets,
                callback_prefix=(
                    f"throne:nighttarget:{action_type.value}"
                ),
            ),
        )
        return

    action = create_action(
        actor_id=user_id,
        action_type=action_type,
    )

    result = game_flow.submit_night_action(
        game=game,
        action=action,
    )

    if not result.success:
        await callback.answer(
            "⚠️ Harakat qabul qilinmadi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "✅ Tungi harakatingiz qabul qilindi."
    )

    try:
        await callback.message.edit_text(
            "🌙 <b>Tungi harakat tanlandi.</b>\n\n"
            f"⚔️ Harakat: <b>{_action_label(action_type)}</b>\n\n"
            "Natija tun yakunida aniqlanadi."
        )
    except TelegramAPIError:
        logger.warning(
            "Tungi harakat xabarini yangilab bo'lmadi.",
            exc_info=True,
        )


# ============================================================
# TUNGI HARAKAT UCHUN NISHON TANLASH
# ============================================================

@router.callback_query(F.data.startswith("throne:nighttarget:"))
async def night_target_handler(
    callback: CallbackQuery,
) -> None:
    """Tanlangan tungi harakatni nishonga qo'llash."""

    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")

    if len(parts) != 4:
        await callback.answer(
            "⚠️ Nishon ma'lumotlari noto'g'ri.",
            show_alert=True,
        )
        return

    _, _, action_value, target_value = parts

    try:
        action_type = ActionType(action_value)
        target_id = int(target_value)
    except ValueError:
        await callback.answer(
            "⚠️ Nishon ma'lumotlari noto'g'ri.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id

    game = _find_player_game(
        user_id=user_id,
        required_phase=GamePhase.NIGHT,
    )

    if game is None:
        await callback.answer(
            "🌙 Faol tun topilmadi.",
            show_alert=True,
        )
        return

    actor = game.get_player(user_id)
    target = game.get_player(target_id)

    if actor is None or not actor.alive:
        await callback.answer(
            "Siz bu vaqtda harakat qila olmaysiz.",
            show_alert=True,
        )
        return

    if target is None:
        await callback.answer(
            target_not_found_message(),
            show_alert=True,
        )
        return

    if not target.alive:
        await callback.answer(
            target_not_alive_message(),
            show_alert=True,
        )
        return

    if target_id == user_id:
        await callback.answer(
            "O'zingizni nishon sifatida tanlay olmaysiz.",
            show_alert=True,
        )
        return

    runtime_info = build_role_runtime_info(actor)

    if runtime_info is None:
        await callback.answer(
            "⚠️ Roli aniqlanmadi.",
            show_alert=True,
        )
        return

    rule = next(
        (
            item
            for item in runtime_info.action_rules
            if item.action_type == action_type
            and item.requires_target
        ),
        None,
    
