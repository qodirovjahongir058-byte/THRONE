from __future__ import annotations

import logging
from dataclasses import dataclass

from game_actions import GameAction
from game_engine import GameState
from game_messages import (
    day_started_message,
    discussion_started_message,
    night_started_message,
    voting_started_message,
)
from game_resolver import resolve_night
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

        # Every game gets its own temporary night action storage.
        game.metadata.setdefault("night_actions", [])

    def unregister_game(self, game_id: int) -> None:
        """Remove a game from automatic phase management."""

        game_scheduler.cancel(game_id)
        self._games.pop(game_id, None)

    def get_game(self, game_id: int) -> GameState | None:
        """Return a registered game."""

        return self._games.get(game_id)

    def submit_night_action(
        self,
        game: GameState,
        action: GameAction,
    ) -> FlowResult:
        """
        Store one player's night action.

        The action itself is not resolved immediately.
        All actions are resolved together when the night ends.
        """

        if game.phase != GamePhase.NIGHT:
            return FlowResult(
                success=False,
                message="night_not_active",
            )

        actor = game.get_player(action.actor_id)

        if actor is None:
            return FlowResult(
                success=False,
                message="player_not_found",
            )

        if not actor.alive:
            return FlowResult(
                success=False,
                message="player_not_alive",
            )

        night_actions = game.metadata.setdefault(
            "night_actions",
            [],
        )

        # One action per player for the current night.
        night_actions[:] = [
            existing
            for existing in night_actions
            if existing.actor_id != action.actor_id
        ]

        night_actions.append(action)

        actor.has_acted = True
        actor.metadata["night_action"] = action.action_type.value
        actor.metadata["night_target"] = action.target_id

        return FlowResult(
            success=True,
            message="night_action_saved",
        )

    def get_night_actions(
        self,
        game: GameState,
    ) -> list[GameAction]:
        """Return all currently stored night actions."""

        actions = game.metadata.get(
            "night_actions",
            [],
        )

        return list(actions)

    def clear_night_actions(
        self,
        game: GameState,
    ) -> None:
        """Clear actions after a night has been resolved."""

        game.metadata["night_actions"] = []

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
        self.clear_night_actions(game)

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
        """
        Resolve all submitted night actions and start the day.
        """

        if game.phase != GamePhase.NIGHT:
            return

        actions = self.get_night_actions(game)

        try:
            resolution = resolve_night(
                game=game,
                actions=actions,
            )
        except Exception:
            logger.exception(
                "Night resolution failed for game_id=%s",
                game.game_id,
            )

            await send_message(
                "⚠️ <b>Tungi harakatlarni qayta ishlashda xatolik yuz berdi.</b>"
            )
            return

        # Save the resolution data for later systems.
        game.metadata["last_night_results"] = list(
            resolution.context.results
        )

        game.metadata["last_night_eliminated"] = list(
            resolution.eliminated_player_ids
        )

        self.clear_night_actions(game)

        for player in game.players.values():
            player.has_acted = False

        result = phase_manager.start_day(game)

        if not result.success:
            return

        await send_message(
            day_started_message(game.night_number)
        )

        eliminated = resolution.eliminated_player_ids

        if eliminated:
            names: list[str] = []

            for player_id in eliminated:
                player = game.get_player(player_id)

                if player is not None:
                    names.append(
                        player.display_name
                    )

            if names:
                await send_message(
                    "🌅 <b>Tun yakuni</b>\n\n"
                    "⚔️ Tungi hujum natijasida:\n"
                    + "\n".join(
                        f"• {name}"
                        for name in names
                    )
                )
        else:
            await send_message(
                "🌅 <b>Tun yakuni</b>\n\n"
                "Bu tun hech kim yo‘q qilinmadi."
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

        Vote resolution will be connected to the existing
        vote_system in the next integration step.
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

    def cancel_game(
        self,
        game: GameState,
    ) -> None:
        """Cancel all scheduled tasks for a game."""

        game_scheduler.cancel(game.game_id)
        self._games.pop(game.game_id, None)


game_flow = GameFlow()
