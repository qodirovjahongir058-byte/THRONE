from __future__ import annotations

import logging
from dataclasses import dataclass

from game_engine import GameState
from game_messages import (
    day_started_message,
    discussion_started_message,
    night_started_message,
    voting_started_message,
)
from game_scheduler import game_scheduler
from game_state import (
    DEFAULT_DISCUSSION_DURATION,
    DEFAULT_NIGHT_DURATION,
    DEFAULT_VOTING_DURATION,
    GamePhase,
)
from phase_manager import phase_manager


logger = logging.getLogger("throne.game_flow")


@dataclass(frozen=True, slots=True)
class FlowResult:
    """Result of a game flow operation."""

    success: bool
    message: str


class GameFlow:
    """Control the automatic THRONE game phase flow."""

    def __init__(self) -> None:
        self._games: dict[int, GameState] = {}

    def register_game(self, game: GameState) -> None:
        """Register a game for automatic phase management."""

        self._games[game.game_id] = game

    def unregister_game(self, game_id: int) -> None:
        """Remove a game from automatic phase management."""

        game_scheduler.cancel(game_id)
        self._games.pop(game_id, None)

    def get_game(self, game_id: int) -> GameState | None:
        """Return a registered game."""

        return self._games.get(game_id)

    async def start_first_night(
        self,
        game: GameState,
        send_message,
    ) -> FlowResult:
        """Start the first night after role reveal."""

        result = phase_manager.start_first_night(game)

        if not result.success:
            return FlowResult(
                success=False,
                message=result.message,
            )

        self.register_game(game)

        await send_message(
            night_started_message(game.night_number)
        )

        self._schedule_night(
            game=game,
            send_message=send_message,
        )

        return FlowResult(
            success=True,
            message="first_night_started",
        )

    def _schedule_night(
        self,
        game: GameState,
        send_message,
    ) -> None:
        """Schedule the end of the current night."""

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.NIGHT.value,
            duration=DEFAULT_NIGHT_DURATION,
            callback=lambda: self._finish_night(
                game=game,
                send_message=send_message,
            ),
        )

    async def _finish_night(
        self,
        game: GameState,
        send_message,
    ) -> None:
        """Finish the night and start the day."""

        if game.phase != GamePhase.NIGHT:
            return

        result = phase_manager.start_day(game)

        if not result.success:
            return

        await send_message(
            day_started_message(game.night_number)
        )

        await self.start_discussion(
            game=game,
            send_message=send_message,
        )

    async def start_discussion(
        self,
        game: GameState,
        send_message,
    ) -> FlowResult:
        """Start the discussion phase."""

        result = phase_manager.start_discussion(game)

        if not result.success:
            return FlowResult(
                success=False,
                message=result.message,
            )

        await send_message(
            discussion_started_message()
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.DISCUSSION.value,
            duration=DEFAULT_DISCUSSION_DURATION,
            callback=lambda: self._finish_discussion(
                game=game,
                send_message=send_message,
            ),
        )

        return FlowResult(
            success=True,
            message="discussion_started",
        )

    async def _finish_discussion(
        self,
        game: GameState,
        send_message,
    ) -> None:
        """Finish discussion and start voting."""

        if game.phase != GamePhase.DISCUSSION:
            return

        await self.start_voting(
            game=game,
            send_message=send_message,
        )

    async def start_voting(
        self,
        game: GameState,
        send_message,
    ) -> FlowResult:
        """Start the voting phase."""

        result = phase_manager.start_voting(game)

        if not result.success:
            return FlowResult(
                success=False,
                message=result.message,
            )

        await send_message(
            voting_started_message()
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.VOTING.value,
            duration=DEFAULT_VOTING_DURATION,
            callback=lambda: self._finish_voting(
                game=game,
                send_message=send_message,
            ),
        )

        return FlowResult(
            success=True,
            message="voting_started",
        )

    async def _finish_voting(
        self,
        game: GameState,
        send_message,
    ) -> None:
        """
        Finish voting.

        The actual vote-resolution system will be connected here.
        """

        if game.phase != GamePhase.VOTING:
            return

        logger.info(
            "Voting timer finished for game_id=%s",
            game.game_id,
        )

        await send_message(
            "⚖️ <b>Ovoz berish vaqti tugadi.</b>\n\n"
            "📜 Ovozlar natijasi qayta ishlanmoqda..."
        )

    def cancel_game(self, game: GameState) -> None:
        """Cancel all scheduled tasks for a game."""

        game_scheduler.cancel(game.game_id)
        self._games.pop(game.game_id, None)


game_flow = GameFlow()
