from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from game_engine import GameState
from game_messages import private_role_message
from roles import get_role


async def send_role_to_player(
    bot: Bot,
    game: GameState,
    user_id: int,
) -> bool:
    """Send the assigned role privately to one player."""

    player = game.get_player(user_id)

    if player is None:
        return False

    if not player.role_key:
        return False

    role = get_role(player.role_key)

    if role is None:
        return False

    try:
        await bot.send_message(
            chat_id=user_id,
            text=private_role_message(
                role_name=role.name,
                side_name=role.side.value,
                ability=role.ability,
                victory_condition=role.victory_condition,
            ),
        )
    except (
        TelegramForbiddenError,
        TelegramBadRequest,
    ):
        return False

    return True


async def send_roles_to_all_players(
    bot: Bot,
    game: GameState,
) -> dict[int, bool]:
    """Send private role messages to every player."""

    results: dict[int, bool] = {}

    for player in game.players.values():
        results[player.user_id] = await send_role_to_player(
            bot=bot,
            game=game,
            user_id=player.user_id,
        )

    return results
