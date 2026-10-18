
from __future__ import annotations

import html
import logging
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from game_actions import ActionType, create_action
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

logger = logging.getLogger("throne.handlers.game")
router = Router(name="throne_game")


# ------------------------------------------------------------
# Yordamchi funksiyalar
# ------------------------------------------------------------

def _is_group(message: Message) -> bool:
    return message.chat.type in {"group", "supergroup"}


def _display_name(player: PlayerState) -> str:
    name = player.display_name or player.username or f"User {player.user_id}"
    return html.escape(name)


async def _is_chat_admin(message: Message, user_id: int) -> bool:
    try:
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
        )
        return member.status in {"administrator", "creator"}
    except TelegramAPIError:
        logger.warning("Adminni tekshirish muvaffaqiyatsiz.", exc_info=True)
        return False


def _find_player_game(
    user_id: int,
    required_phase: GamePhase | None = None,
) -> GameState | None:
    matches = [
        game
        for game in game_service._games.values()
        if game.get_player(user_id) is not None
        and game.status == GameStatus.ACTIVE
        and (
            required_phase is None
            or game.phase == required_phase
        )
    ]

    if len(matches) != 1:
        return None

    return matches[0]


def _action_label(action_type: ActionType) -> str:
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


def _alive_targets(
    game: GameState,
    actor_id: int,
) -> list[tuple[int, str]]:
    return [
        (player.user_id, _display_name(player))
        for player in game.alive_players()
        if player.user_id != actor_id
    ]


async def _safe_edit(
    message: Message,
    text: str,
    reply_markup: Any = None,
) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramAPIError:
        logger.warning("Xabarni tahrirlash muvaffaqiyatsiz.", exc_info=True)


async def _send_night_actions(bot: Any, game: GameState) -> None:
    """Tungi harakat tugmalarini o'yinchilarga shaxsiy yuboradi."""
    for player in game.alive_players():
        runtime = build_role_runtime_info(player)

        if runtime is None:
            logger.warning("Rol topilmadi: user_id=%s", player.user_id)
            continue

        buttons = [
            (
                _action_label(rule.action_type),
                f"throne:night:{rule.action_type.value}:"
                f"{1 if rule.requires_target else 0}",
            )
            for rule in runtime.action_rules
        ]

        text = (
            "🌙 <b>Tun boshlandi.</b>\n\n"
            "O'z rolingiz uchun tungi harakatni tanlang."
        )

        if not buttons:
            text = (
                "🌙 <b>Tun boshlandi.</b>\n\n"
                "Bu tun uchun faol tungi qobiliyatingiz yo'q."
            )

        try:
            await bot.send_message(
                chat_id=player.user_id,
                text=text,
                reply_markup=night_action_keyboard(buttons) if buttons else None,
            )
        except TelegramAPIError:
            logger.warning(
                "Tungi xabar yuborilmadi: user_id=%s",
                player.user_id,
                exc_info=True,
            )


# ------------------------------------------------------------
# Yangi o'yin ochish
# ------------------------------------------------------------

@router.message(Command("newgame"))
async def new_game_handler(message: Message) -> None:
    if not _is_group(message):
        await message.answer("⚠️ THRONE o'yini faqat guruhda boshlanadi.")
        return

    if message.from_user is None:
        return

    if not await _is_chat_admin(message, message.from_user.id):
        await message.answer(permission_denied_message())
        return

    result = game_service.create_game(chat_id=message.chat.id)

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


# ------------------------------------------------------------
# O'yinga qo'shilish
# ------------------------------------------------------------

@router.callback_query(F.data == "throne:join")
async def join_game_handler(callback: CallbackQuery) -> None:
    message = callback.message

    if message is None:
        await callback.answer()
        return

    if message.chat.type not in {"group", "supergroup"}:
        await callback.answer("O'yinga guruh orqali qo'shiling.", show_alert=True)
        return

    game = game_service.get_game(message.chat.id)

    if game is None:
        await callback.answer("O'yin topilmadi.", show_alert=True)
        return

    if game.status != GameStatus.WAITING or game.phase != GamePhase.LOBBY:
        await callback.answer("Kutish xonasi yopilgan.", show_alert=True)
        return

    if game.player_count() >= MAX_PLAYERS:
        await callback.answer(game_full_message(), show_alert=True)
        return

    user = callback.from_user
    player = PlayerState(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    result = game_service.add_player(message.chat.id, player)

    if not result.success or result.game is None:
        error = {
            "player_already_joined": player_already_joined_message(),
            "game_full": game_full_message(),
        }.get(result.message, "⚠️ O'yinga qo'shilib bo'lmadi.")

        await callback.answer(error, show_alert=True)
        return

    await callback.answer("Siz o'yinga qo'shildingiz!")

    await _safe_edit(
        message,
        lobby_message(
            player_count=result.game.player_count(),
            min_players=MIN_PLAYERS,
            max_players=MAX_PLAYERS,
        ),
        reply_markup=lobby_keyboard(),
    )

    try:
        await message.answer(
            player_joined_message(
                display_name=_display_name(player),
                player_count=result.game.player_count(),
                max_players=MAX_PLAYERS,
            )
        )
    except TelegramAPIError:
        logger.warning("Qo'shilish xabari yuborilmadi.", exc_info=True)


# ------------------------------------------------------------
# O'yinchilar ro'yxati
# ------------------------------------------------------------

@router.callback_query(F.data == "throne:players")
async def players_handler(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    game = game_service.get_game(callback.message.chat.id)

    if game is None:
        await callback.answer("O'yin topilmadi.", show_alert=True)
        return

    if not game.players:
        await callback.answer("Hali hech kim qo'shilmagan.", show_alert=True)
        return

    names = "\n".join(
        f"• {_display_name(player)}"
        for player in game.players.values()
    )

    await callback.answer()
    await callback.message.answer(
        "👥 <b>O'yinchilar</b>\n\n"
        f"{names}\n\n"
        f"Jami: <b>{game.player_count()}/{MAX_PLAYERS}</b>"
    )


# ------------------------------------------------------------
# O'yinni boshlash
# ------------------------------------------------------------

@router.callback_query(F.data == "throne:start")
async def start_game_handler(callback: CallbackQuery) -> None:
    message = callback.message

    if message is None:
        await callback.answer()
        return

    if not _is_group(message):
        await callback.answer("O'yinni guruhda boshlang.", show_alert=True)
        return

    if not await _is_chat_admin(message, callback.from_user.id):
        await callback.answer(
            "Faqat guruh administratori boshlashi mumkin.",
            show_alert=True,
        )
        return

    game = game_service.get_game(message.chat.id)

    if game is None:
        await callback.answer("O'yin topilmadi.", show_alert=True)
        return

    if game.status != GameStatus.WAITING or game.phase != GamePhase.LOBBY:
        await callback.answer("O'yin allaqachon boshlangan.", show_alert=True)
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

    result = game_service.start_game(message.chat.id)

    if not result.success or result.game is None:
        await callback.answer(
            "O'yinni boshlashda xatolik yuz berdi.",
            show_alert=True,
        )
        return

    game = result.game
    await callback.answer("O'yin boshlandi!")

    try:
        delivery = await send_roles_to_all_players(bot=message.bot, game=game)
    except Exception:
        logger.exception("Rollarni yuborishda xatolik: game_id=%s", game.game_id)
        delivery = {}

    await _safe_edit(message, role_reveal_message())

    failed = sum(1 for sent in delivery.values() if not sent)
    if failed or len(delivery) < game.player_count():
        await message.answer(
            "📜 <b>Rollar taqsimlandi.</b>\n\n"
            "⚠️ Ayrim o'yinchilarga shaxsiy xabar yetmadi. "
            "Ular botga kirib /start yuborishi kerak."
        )
    else:
        await message.answer(
            "⚔️ <b>O'yin boshlandi!</b>\n\n"
            "Rollar shaxsiy xabarda yuborildi."
        )

    try:
        flow_result = await game_flow.start_first_night(
            game=game,
            send_message=message.answer,
            send_private_message=lambda user_id, text: message.bot.send_message(
                chat_id=user_id,
                text=text,
            ),
        )
    except Exception:
        logger.exception("Birinchi tunni boshlashda xatolik: game_id=%s", game.game_id)
        flow_result = None

    if flow_result is None or not flow_result.success:
        await message.answer(
            "⚠️ Birinchi tunni boshlashda xatolik yuz berdi. "
            "Server loglarini tekshiring."
        )
        return

    await _send_night_actions(message.bot, game)


# ------------------------------------------------------------
# Tungi harakatni tanlash
# ------------------------------------------------------------

@router.callback_query(F.data.startswith("throne:night:"))
async def night_action_handler(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 4 or parts[3] not in {"0", "1"}:
        await callback.answer("Harakat ma'lumotlari noto'g'ri.", show_alert=True)
        return

    try:
        action_type = ActionType(parts[2])
    except ValueError:
        await callback.answer("Noma'lum tungi harakat.", show_alert=True)
        return

    user_id = callback.from_user.id
    game = _find_player_game(user_id, GamePhase.NIGHT)

    if game is None:
        await callback.answer("Siz uchun faol tun topilmadi.", show_alert=True)
        return

    player = game.get_player(user_id)
    if player is None or not player.alive:
        await callback.answer("Siz harakat qila olmaysiz.", show_alert=True)
        return

    if player.blocked:
        await callback.answer("Qobiliyatingiz bu tun bloklangan.", show_alert=True)
        return

    if player.has_acted:
        await callback.answer("Tungi harakatingiz tanlangan.", show_alert=True)
        return

    runtime = build_role_runtime_info(player)
    rule = next(
        (
            item for item in runtime.action_rules
            if item.action_type == action_type
        ),
        None,
    ) if runtime else None

    if rule is None:
        await callback.answer("Bu harakat rolingizga tegishli emas.", show_alert=True)
        return

    requires_target = parts[3] == "1"
    if rule.requires_target != requires_target:
        await callback.answer("Harakat turi mos kelmadi.", show_alert=True)
        return

    if requires_target:
        targets = _alive_targets(game, user_id)
        if not targets:
            await callback.answer("Nishon mavjud emas.", show_alert=True)
            return

        await callback.answer()
        await callback.message.edit_text(
            "🌙 <b>Nishonni tanlang:</b>",
            reply_markup=target_keyboard(
                targets=targets,
                callback_prefix=f"throne:nighttarget:{action_type.value}",
            ),
        )
        return

    action = create_action(actor_id=user_id, action_type=action_type)
    result = game_flow.submit_night_action(game=game, action=action)

    if not result.success:
        await callback.answer("Harakat qabul qilinmadi.", show_alert=True)
        return

    await callback.answer("Tungi harakatingiz qabul qilindi.")
    await _safe_edit(
        callback.message,
        "🌙 <b>Tungi harakat tanlandi.</b>\n\n"
        f"✨ Harakat: <b>{_action_label(action_type)}</b>\n\n"
        "Natija tun yakunida aniqlanadi.",
    )


# ------------------------------------------------------------
# Tungi harakat uchun nishon tanlash
# ------------------------------------------------------------

@router.callback_query(F.data.startswith("throne:nighttarget:"))
async def night_target_handler(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Nishon ma'lumotlari noto'g'ri.", show_alert=True)
        return

    try:
        action_type = ActionType(parts[2])
        target_id = int(parts[3])
    except ValueError:
        await callback.answer("Nishon ma'lumotlari noto'g'ri.", show_alert=True)
        return

    user_id = callback.from_user.id
    game = _find_player_game(user_id, GamePhase.NIGHT)

    if game is None:
        await callback.answer("Faol tun topilmadi.", show_alert=True)
        return

    actor = game.get_player(user_id)
    target = game.get_player(target_id)

    if actor is None or not actor.alive:
        await callback.answer("Siz harakat qila olmaysiz.", show_alert=True)
        return

    if actor.blocked:
        await callback.answer("Qobiliyatingiz bu tun bloklangan.", show_alert=True)
        return

    if actor.has_acted:
        await callback.answer("Tungi harakatingiz tanlangan.", show_alert=True)
        return

    if target is None:
        await callback.answer(target_not_found_message(), show_alert=True)
        return

    if not target.alive:
        await callback.answer(target_not_alive_message(), show_alert=True)
        return

    if target_id == user_id:
        await callback.answer("O'zingizni nishon qila olmaysiz.", show_alert=True)
        return

    runtime = build_role_runtime_info(actor)
    rule = next(
        (
            item for item in runtime.action_rules
            if item.action_type == action_type
        ),
        None,
    ) if runtime else None

    if rule is None or not rule.requires_target:
        await callback.answer("Bu harakat rolingizga mos emas.", show_alert=True)
        return

    action = create_action(
        actor_id=user_id,
        action_type=action_type,
        target_id=target_id,
    )
    result = game_flow.submit_night_action(game=game, action=action)

    if not result.success:
        await callback.answer("Harakat qabul qilinmadi.", show_alert=True)
        return

    await callback.answer("Tungi harakatingiz qabul qilindi.")
    await _safe_edit(
        callback.message,
        "🌙 <b>Tungi harakat tanlandi.</b>\n\n"
        f"✨ Harakat: <b>{_action_label(action_type)}</b>\n"
        f"🎯 Nishon: <b>{_display_name(target)}</b>\n\n"
        "Natija tun yakunida aniqlanadi.",
    )


# ------------------------------------------------------------
# Ovoz berish
# ------------------------------------------------------------

@router.callback_query(F.data.startswith("throne:vote:"))
async def vote_handler(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ovoz ma'lumotlari noto'g'ri.", show_alert=True)
        return

    try:
        target_id = int(parts[2])
    except ValueError:
        await callback.answer("Nishon noto'g'ri.", show_alert=True)
        return

    voter_id = callback.from_user.id
    game = _find_player_game(voter_id)

    if game is None or game.phase not in {GamePhase.VOTING, GamePhase.REVOTE}:
        await callback.answer("Hozir ovoz berish faol emas.", show_alert=True)
        return

    voter = game.get_player(voter_id)
    target = game.get_player(target_id)

    if voter is None or not voter.alive:
        await callback.answer("Ovoz berish uchun tirik o'yinchi bo'lishingiz kerak.", show_alert=True)
        return

    if target is None or not target.alive:
        await callback.answer("Tanlangan o'yinchi tirik emas.", show_alert=True)
        return

    if voter_id == target_id:
        await callback.answer("O'zingizga ovoz bera olmaysiz.", show_alert=True)
        return

    revote_targets = game.metadata.get("revote_targets")
    if (
        game.phase == GamePhase.REVOTE
        and revote_targets is not None
        and target_id not in revote_targets
    ):
        await callback.answer(
            "Qayta ovoz berishda faqat teng ovoz olgan nomzodlarni tanlang.",
            show_alert=True,
        )
        return

    if voter.voted_for is not None:
        await callback.answer("Siz allaqachon ovoz bergansiz.", show_alert=True)
        return

    accepted = vote_system.submit_vote(
        game=game,
        voter_id=voter_id,
        target_id=target_id,
    )

    if not accepted:
        await callback.answer("Ovozingiz qabul qilinmadi.", show_alert=True)
        return

    await callback.answer("Ovozingiz qabul qilindi.")


# ------------------------------------------------------------
# So'nggi so'zlar
# ------------------------------------------------------------

@router.message(F.chat.type == "private", F.text)
async def last_words_private_handler(message: Message) -> None:
  game = _find_player_game(
        user_id=message.from_user.id,
        required_phase=GamePhase.LAST_WORDS,
    )

    if game is None or game.last_words_player_id != message.from_user.id:
        return

    result = last_words_system.submit(
        game=game,
        player_id=message.from_user.id,
        text=message.text,
    )

    if not result.success:
        await message.answer(
            "⚠️ So'nggi so'z qabul qilinmadi. Vaqt tugamaganini tekshiring."
        )
        return

    await message.answer(
        "🕯️ <b>So'nggi so'zingiz saqlandi.</b>\n\n"
        "Xabaringiz vaqt tugagach guruhda e'lon qilinadi."
    )


# ------------------------------------------------------------
# O'yinni to'xtatish
# ------------------------------------------------------------

@router.callback_query(F.data == "throne:stop")
async def stop_game_handler(callback: CallbackQuery) -> None:
    message = callback.message

    if message is None:
        await callback.answer()
        return

    if not _is_group(message):
        await callback.answer("O'yinni guruhda to'xtating.", show_alert=True)
        return

    if not await _is_chat_admin(message, callback.from_user.id):
        await callback.answer(permission_denied_message(), show_alert=True)
        return

    game = game_service.get_game(message.chat.id)

    if game is None:
        await callback.answer("O'yin topilmadi.", show_alert=True)
        return

    result = game_service.stop_game(message.chat.id)

    if not result.success:
        await callback.answer("O'yinni to'xtatib bo'lmadi.", show_alert=True)
        return

    game_flow.unregister_game(game.game_id)
    game_service.remove_game(message.chat.id)

    await callback.answer("O'yin to'xtatildi.")
    await _safe_edit(message, game_stopped_message())

  
