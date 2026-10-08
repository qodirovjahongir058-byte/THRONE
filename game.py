from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from game_engine import PlayerState
from game_messages import (
    game_full_message,
    game_not_started_message,
    game_started_message,
    game_stopped_message,
    lobby_message,
    not_enough_players_message,
    permission_denied_message,
    player_already_joined_message,
    player_joined_message,
)
from game_service import game_service
from game_state import MAX_PLAYERS, MIN_PLAYERS
from keyboards import lobby_keyboard

router = Router()


def _display_name(message: Message) -> str:
    """Return a safe display name for a Telegram user."""

    user = message.from_user

    if user is None:
        return "O‘yinchi"

    if user.full_name:
        return user.full_name

    return str(user.id)


def _is_group(message: Message) -> bool:
    """Return True when the message comes from a group."""

    return message.chat.type in {
        "group",
        "supergroup",
    }


async def _is_chat_admin(
    message: Message,
    user_id: int,
) -> bool:
    """Check whether a Telegram user is an administrator."""

    member = await message.bot.get_chat_member(
        chat_id=message.chat.id,
        user_id=user_id,
    )

    return member.status in {
        "administrator",
        "creator",
    }


@router.message(Command("newgame"))
async def new_game_handler(message: Message) -> None:
    """Create a new THRONE game in a group."""

    if not _is_group(message):
        await message.answer(
            "⚠️ <b>THRONE</b> o‘yini faqat guruhlarda "
            "boshlanadi."
        )
        return

    if message.from_user is None:
        return

    if not await _is_chat_admin(
        message,
        message.from_user.id,
    ):
        await message.answer(
            permission_denied_message(),
        )
        return

    result = game_service.create_game(
        chat_id=message.chat.id,
    )

    if not result.success or result.game is None:
        await message.answer(
            "⚠️ Bu guruhda allaqachon faol o‘yin mavjud."
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


@router.callback_query(F.data == "throne:join")
async def join_game_handler(
    callback: CallbackQuery,
) -> None:
    """Join the current group game."""

    if callback.message is None:
        await callback.answer()
        return

    user = callback.from_user
    chat_id = callback.message.chat.id

    game = game_service.get_game(chat_id)

    if game is None:
        await callback.answer(
            "O‘yin topilmadi.",
            show_alert=True,
        )
        return

    if game.player_count() >= MAX_PLAYERS:
        await callback.answer(
            "O‘yinchilar soni maksimal chegaraga yetgan.",
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
            await callback.answer(
                player_already_joined_message(),
                show_alert=True,
            )
            return

        if result.message == "game_full":
            await callback.answer(
                game_full_message(),
                show_alert=True,
            )
            return

        await callback.answer(
            "⚠️ O‘yinga qo‘shilib bo‘lmadi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "Siz o‘yinga qo‘shildingiz!",
    )

    await callback.message.edit_text(
        lobby_message(
            player_count=result.game.player_count(),
            min_players=MIN_PLAYERS,
            max_players=MAX_PLAYERS,
        ),
        reply_markup=lobby_keyboard(),
    )

    await callback.message.answer(
        player_joined_message(
            display_name=player.display_name,
            player_count=result.game.player_count(),
            max_players=MAX_PLAYERS,
        ),
    )


@router.callback_query(F.data == "throne:players")
async def players_handler(
    callback: CallbackQuery,
) -> None:
    """Show the current player list."""

    if callback.message is None:
        await callback.answer()
        return

    game = game_service.get_game(
        callback.message.chat.id,
    )

    if game is None:
        await callback.answer(
            "O‘yin topilmadi.",
            show_alert=True,
        )
        return

    if not game.players:
        await callback.answer(
            "Hali hech kim qo‘shilmagan.",
            show_alert=True,
        )
        return

    players = "\n".join(
        f"• {player.display_name}"
        for player in game.players.values()
    )

    await callback.answer()

    await callback.message.answer(
        "👥 <b>O‘yinchilar</b>\n\n"
        f"{players}\n\n"
        f"Jami: <b>{game.player_count()}/{MAX_PLAYERS}</b>"
    )


@router.callback_query(F.data == "throne:start")
async def start_game_handler(
    callback: CallbackQuery,
) -> None:
    """Start the game. Only group administrators may do this."""

    if callback.message is None:
        await callback.answer()
        return

    user = callback.from_user
    message = callback.message

    if not await _is_chat_admin(
        message,
        user.id,
    ):
        await callback.answer(
            "Faqat guruh administratori o‘yinni boshlashi mumkin.",
            show_alert=True,
        )
        return

    game = game_service.get_game(message.chat.id)

    if game is None:
        await callback.answer(
            "O‘yin topilmadi.",
            show_alert=True,
        )
        return

    if game.player_count() < MIN_PLAYERS:
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

    if not result.success:
        await callback.answer(
            "O‘yinni boshlashda xatolik yuz berdi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "O‘yin boshlandi!",
    )

    await message.edit_text(
        game_started_message(),
    )


@router.callback_query(F.data == "throne:stop")
async def stop_game_handler(
    callback: CallbackQuery,
) -> None:
    """Stop the current game. Only group administrators may do this."""

    if callback.message is None:
        await callback.answer()
        return

    user = callback.from_user
    message = callback.message

    if not await _is_chat_admin(
        message,
        user.id,
    ):
        await callback.answer(
            "Faqat guruh administratori o‘yinni bekor qilishi mumkin.",
            show_alert=True,
        )
        return

    result = game_service.stop_game(
        chat_id=message.chat.id,
    )

    if not result.success:
        await callback.answer(
            "O‘yinni to‘xtatib bo‘lmadi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "O‘yin to‘xtatildi.",
    )

    await message.edit_text(
        game_stopped_message(),
  )
