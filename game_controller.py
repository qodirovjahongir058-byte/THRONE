from __future__ import annotations

import logging

from aiogram import Bot

from game_engine import GameState
from game_flow import game_flow


logger = logging.getLogger("throne.game_controller")


async def start_first_night(
    bot: Bot,
    game: GameState,
) -> bool:
    """
    Start the first night of a THRONE game.

    This controller connects the bot with the existing
    GameFlow system without changing the game state logic.
    """

    async def send_message(text: str) -> None:
        await bot.send_message(
            chat_id=game.chat_id,
            text=text,
        )

    try:
        result = await game_flow.start_first_night(
            game=game,
            send_message=send_message,
        )

    except Exception:
        logger.exception(
            "Failed to start first night for game_id=%s",
            game.game_id,
        )
        return False

    return result.success


def register_game(game: GameState) -> None:
    """Register a game in the automatic flow manager."""

    game_flow.register_game(game)


def unregister_game(game: GameState) -> None:
    """Remove a game from the automatic flow manager."""

    game_flow.unregister_game(game.game_id)
