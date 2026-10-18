
import logging

from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery

from game_actions import GameActionManager
from game_engine import GamePhase
from game_handlers import active_games
from night_actions import (
    build_night_action_keyboard,
    parse_night_action_callback,
    submit_night_action,
)
from roles import get_role

logger = logging.getLogger("THRONE.night_action_handlers")
router = Router(name="throne_night_action_handlers")


def find_active_game(game_id: str):
    """Xotiradagi faol o'yinni topadi."""
    for chat_id, session in active_games.items():
        if session.get("game_id") == game_id:
            game = session.get("game")
            if game is not None:
                return chat_id, session, game
    return None


async def send_night_action_prompts(
    bot: Bot,
    game_id: str,
) -> None:
    """Tirik va faol roli bor o'yinchilarga tungi tanlov yuboradi."""
    found = find_active_game(game_id)

    if found is None:
        logger.warning("Faol o'yin topilmadi: %s", game_id)
        return

    _, _, game = found

    if game.phase != GamePhase.NIGHT:
        return

    for player in game.alive_players:
        role = get_role(player.role_id or "")

        if role is None or role.action is None:
            continue

        keyboard = build_night_action_keyboard(
            game,
            player.user_id,
        )

        if keyboard is None:
            continue

        try:
            await bot.send_message(
                chat_id=player.user_id,
                text=(
                    "🌙 <b>THRONE — Tungi harakat</b>\n\n"
                    f"🎭 <b>Rol:</b> {role.name}\n"
                    f"⚔️ <b>Qobiliyat:</b> {role.ability}\n\n"
                    "Harakatingiz uchun nishonni tanlang. "
                    "Tanlovingiz maxfiy saqlanadi."
                ),
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception(
                "Tungi xabar yuborilmadi: user_id=%s",
                player.user_id,
            )


@router.callback_query(
    lambda query: query.data is not None
    and query.data.startswith("throne_night|")
)
async def handle_night_action(query: CallbackQuery) -> None:
    """Tungi harakatni qabul qiladi va tekshiradi."""
    if not query.from_user or not query.message:
        await query.answer(
            "O'yinchi ma'lumotlari topilmadi.",
            show_alert=True,
        )
        return

    if (
        query.message.chat.type != ChatType.PRIVATE
        or query.message.chat.id != query.from_user.id
    ):
        await query.answer(
            "Tungi harakatni bot bilan shaxsiy chatda tanlang.",
            show_alert=True,
        )
        return

    parsed = parse_night_action_callback(query.data or "")

    if parsed is None:
        await query.answer(
            "Tugma ma'lumoti noto'g'ri.",
            show_alert=True,
        )
        return

    game_id, action_type, target_id = parsed
    found = find_active_game(game_id)

    if found is None:
        await query.answer(
            "Bu o'yin faol emas yoki bot qayta ishga tushgan.",
            show_alert=True,
        )
        return

    _, _, game = found

    result = submit_night_action(
        game=game,
        actor_id=query.from_user.id,
        action_type=action_type,
        target_id=None if target_id == 0 else target_id,
    )

    await query.answer(
        result.message,
        show_alert=not result.success,
    )

    if result.success:
        try:
            await query.message.edit_text(
                "🌙 <b>Tungi harakatingiz qabul qilindi.</b>\n\n"
                "Tanlovingiz maxfiy saqlanadi.",
                reply_markup=None,
            )
        except Exception:
            logger.debug(
                "Tungi xabarni yangilab bo'lmadi.",
                exc_info=True,
            )


@router.callback_query(
    lambda query: query.data is not None
    and query.data.startswith("throne_cancel|")
)
async def handle_cancel_night_action(
    query: CallbackQuery,
) -> None:
    """O'yinchining avvalgi tungi harakatini bekor qiladi."""
    if not query.from_user or not query.message:
        await query.answer(
            "O'yinchi ma'lumotlari topilmadi.",
            show_alert=True,
        )
        return

    if (
        query.message.chat.type != ChatType.PRIVATE
        or query.message.chat.id != query.from_user.id
    ):
        await query.answer(
            "Bu tugma faqat shaxsiy chatda ishlaydi.",
            show_alert=True,
        )
        return

    parts = (query.data or "").split("|")

    if len(parts) != 2:
        await query.answer(
            "Tugma ma'lumoti noto'g'ri.",
            show_alert=True,
        )
        return

    found = find_active_game(parts[1])

    if found is None:
        await query.answer(
            "Bu o'yin faol emas.",
            show_alert=True,
        )
        return

    _, _, game = found

    result = GameActionManager.cancel_action(
        game,
        query.from_user.id,
    )

    await query.answer(
        result.message,
        show_alert=not result.success,
    )

    if result.success:
        keyboard = build_night_action_keyboard(
            game,
            query.from_user.id,
        )

        try:
            await query.message.edit_text(
                "🌙 <b>Tungi harakat bekor qilindi.</b>\n\n"
                "Yangi nishonni tanlang:",
                reply_markup=keyboard,
            )
        except Exception:
            logger.debug(
                "Bekor qilish xabarini yangilab bo'lmadi.",
                exc_info=True,
      )
          
