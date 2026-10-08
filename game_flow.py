from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

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
from game_victory import check_victory
from keyboards import last_words_keyboard, voting_keyboard
from last_words import last_words_system
from phase_manager import phase_manager
from vote_system import VoteResult, vote_system


logger = logging.getLogger("throne.game_flow")

SendMessage = Callable[..., Awaitable[object]]


@dataclass(frozen=True, slots=True)
class FlowResult:
    success: bool
    message: str


class GameFlow:
    """Control the complete automatic THRONE game flow."""

    def __init__(self) -> None:
        self._games: dict[int, GameState] = {}

    def register_game(self, game: GameState) -> None:
        self._games[game.game_id] = game
        game.metadata.setdefault("night_actions", [])

    def unregister_game(self, game_id: int) -> None:
        game_scheduler.cancel(game_id)
        self._games.pop(game_id, None)

    def get_game(self, game_id: int) -> GameState | None:
        return self._games.get(game_id)

    def submit_night_action(
        self,
        game: GameState,
        action: GameAction,
    ) -> FlowResult:
        if game.phase != GamePhase.NIGHT:
            return FlowResult(False, "night_not_active")

        actor = game.get_player(action.actor_id)

        if actor is None:
            return FlowResult(False, "player_not_found")

        if not actor.alive:
            return FlowResult(False, "player_not_alive")

        night_actions = game.metadata.setdefault(
            "night_actions",
            [],
        )

        night_actions[:] = [
            existing
            for existing in night_actions
            if existing.actor_id != action.actor_id
        ]

        night_actions.append(action)

        actor.has_acted = True
        actor.metadata["night_action"] = action.action_type.value
        actor.metadata["night_target"] = action.target_id

        return FlowResult(True, "night_action_saved")

    def get_night_actions(
        self,
        game: GameState,
    ) -> list[GameAction]:
        return list(
            game.metadata.get("night_actions", [])
        )

    def clear_night_actions(
        self,
        game: GameState,
    ) -> None:
        game.metadata["night_actions"] = []

    async def start_first_night(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> FlowResult:
        result = phase_manager.start_first_night(game)

        if not result.success:
            return FlowResult(False, result.message)

        self.register_game(game)
        self.clear_night_actions(game)

        await send_message(
            night_started_message(game.night_number)
        )

        self._schedule_night(
            game,
            send_message,
        )

        return FlowResult(True, "first_night_started")

    def _schedule_night(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.NIGHT.value,
            duration=DEFAULT_NIGHT_DURATION,
            callback=lambda: self._finish_night(
                game,
                send_message,
            ),
        )

    async def _finish_night(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
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

        game.metadata["last_night_results"] = list(
            resolution.context.results
        )
        game.metadata["last_night_eliminated"] = list(
            resolution.eliminated_player_ids
        )

        self.clear_night_actions(game)

        for player in game.players.values():
            player.has_acted = False
            player.metadata.pop("night_action", None)
            player.metadata.pop("night_target", None)

        victory = check_victory(game)

        if victory.finished:
            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return

        result = phase_manager.start_day(game)

        if not result.success:
            return

        await send_message(
            day_started_message(game.night_number)
        )

        eliminated = resolution.eliminated_player_ids

        if eliminated:
            names = []

            for player_id in eliminated:
                player = game.get_player(player_id)

                if player is not None:
                    names.append(player.display_name)

            if names:
                await send_message(
                    "🌅 <b>Tun yakuni</b>\n\n"
                    "⚔️ Bu tun yo‘q qilinganlar:\n"
                    + "\n".join(
                        f"• {name}"
                        for name in names
                    )
                )

                # Process the first eliminated player through
                # the existing last-words system.
                await self._start_last_words(
                    game=game,
                    player_id=eliminated[0],
                    send_message=send_message,
                )
                return

        await self.start_discussion(
            game=game,
            send_message=send_message,
        )

    async def _start_last_words(
        self,
        game: GameState,
        player_id: int,
        send_message: SendMessage,
    ) -> None:
        result = last_words_system.start(
            game=game,
            player_id=player_id,
        )

        if not result.success:
            await self.start_discussion(
                game=game,
                send_message=send_message,
            )
            return

        player = game.get_player(player_id)

        if player is None:
            await self.start_discussion(
                game=game,
                send_message=send_message,
            )
            return

        await send_message(
            "🕯️ <b>So‘nggi so‘z</b>\n\n"
            f"👤 <b>{player.display_name}</b>\n\n"
            "Sizda 30 soniya bor. "
            "So‘nggi so‘zingizni botga shaxsiy xabarda yuboring."
        )

        await send_message(
            "🕯️ <b>So‘nggi so‘z boshlandi.</b>\n\n"
            f"👤 {player.display_name} so‘nggi so‘zini aytmoqda."
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.LAST_WORDS.value,
            duration=30,
            callback=lambda: self._finish_last_words(
                game,
                send_message,
            ),
        )

    async def _finish_last_words(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        if game.phase != GamePhase.LAST_WORDS:
            return

        player_id = game.last_words_player_id
        saved_text = game.metadata.get("last_words_text")

        last_words_system.finish(game)

        if player_id is not None:
            player = game.get_player(player_id)

            if player is not None:
                if saved_text:
                    await send_message(
                        "🕯️ <b>So‘nggi so‘z</b>\n\n"
                        f"👤 <b>{player.display_name}</b>:\n"
                        f"“{saved_text}”"
                    )
                else:
                    await send_message(
                        "🕯️ <b>So‘nggi so‘z vaqti tugadi.</b>\n\n"
                        f"👤 {player.display_name} "
                        "so‘z qoldirmadi."
                    )

        victory = check_victory(game)

        if victory.finished:
            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return

        await self.start_discussion(
            game=game,
            send_message=send_message,
        )

    async def start_discussion(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> FlowResult:
        result = phase_manager.start_discussion(game)

        if not result.success:
            return FlowResult(False, result.message)

        await send_message(
            discussion_started_message()
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.DISCUSSION.value,
            duration=DEFAULT_DISCUSSION_DURATION,
            callback=lambda: self._finish_discussion(
                game,
                send_message,
            ),
        )

        return FlowResult(True, "discussion_started")

    async def _finish_discussion(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        if game.phase != GamePhase.DISCUSSION:
            return

        await self.start_voting(
            game,
            send_message,
        )

    async def start_voting(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> FlowResult:
        result = phase_manager.start_voting(game)

        if not result.success:
            return FlowResult(False, result.message)

        targets = [
            (
                player.user_id,
                player.display_name or f"User {player.user_id}",
            )
            for player in game.alive_players()
        ]

        await send_message(
            voting_started_message(),
            reply_markup=voting_keyboard(targets),
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.VOTING.value,
            duration=DEFAULT_VOTING_DURATION,
            callback=lambda: self._finish_voting(
                game,
                send_message,
            ),
        )

        return FlowResult(True, "voting_started")

    async def _finish_voting(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        if game.phase != GamePhase.VOTING:
            return

        resolution = vote_system.resolve_votes(game)

        if resolution.result == VoteResult.REVOTE:
            game.metadata["revote"] = True

            targets = []

            for player_id in resolution.tied_player_ids:
                player = game.get_player(player_id)

                if player is not None and player.alive:
                    targets.append(
                        (
                            player.user_id,
                            player.display_name
                            or f"User {player.user_id}",
                        )
                    )

            game.reset_votes()

            await send_message(
                "⚖️ <b>Ovozlar teng keldi.</b>\n\n"
                "Qayta ovoz berish boshlanadi.",
                reply_markup=voting_keyboard(targets),
            )

            game_scheduler.schedule(
                game_id=game.game_id,
                phase_name="REVOTE",
                duration=DEFAULT_VOTING_DURATION,
                callback=lambda: self._finish_revote(
                    game,
                    send_message,
                ),
            )
            return

        await self._process_vote_result(
            game,
            resolution,
            send_message,
        )

    async def _finish_revote(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        if game.phase != GamePhase.VOTING:
            return

        resolution = vote_system.resolve_revote(game)

        await self._process_vote_result(
            game,
            resolution,
            send_message,
        )

    async def _process_vote_result(
        self,
        game: GameState,
        resolution,
        send_message: SendMessage,
    ) -> None:
        if resolution.result == VoteResult.NO_ELIMINATION:
            await send_message(
                "⚖️ <b>Ovoz natijasi</b>\n\n"
                "Hech kim chiqarilmadi."
            )

            victory = check_victory(game)

            if victory.finished:
                await self._finish_game(
                    game,
                    victory.winning_side.value,
                    victory.reason,
                    send_message,
                )
                return

            await self._start_next_night(
                game,
                send_message,
            )
            return

        if resolution.eliminated_player_id is None:
            await self._start_next_night(
                game,
                send_message,
            )
            return

        player = game.get_player(
            resolution.eliminated_player_id
        )

        if player is None:
            await self._start_next_night(
                game,
                send_message,
            )
            return

        await send_message(
            "⚖️ <b>Ovoz natijasi</b>\n\n"
            f"❌ <b>{player.display_name}</b> "
            "o‘yindan chiqarildi."
        )

        last_words_result = last_words_system.start(
            game=game,
            player_id=player.user_id,
        )

        if last_words_result.success:
            await send_message(
                "🕯️ <b>So‘nggi so‘z</b>\n\n"
                f"👤 {player.display_name}\n"
                "30 soniya ichida so‘nggi so‘zini aytishi mumkin."
            )

            game_scheduler.schedule(
                game_id=game.game_id,
                phase_name=GamePhase.LAST_WORDS.value,
                duration=30,
                callback=lambda: self._finish_last_words(
                    game,
                    send_message,
                ),
            )
            return

        victory = check_victory(game)

        if victory.finished:
            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return

        await self._start_next_night(
            game,
            send_message,
        )

    async def _start_next_night(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        result = phase_manager.start_next_night(game)

        if not result.success:
            return

        self.clear_night_actions(game)

        await send_message(
            night_started_message(game.night_number)
        )

        self._schedule_night(
            game,
            send_message,
        )

    async def _finish_game(
        self,
        game: GameState,
        winning_side: str,
        reason: str,
        send_message: SendMessage,
    ) -> None:
        game_scheduler.cancel(game.game_id)

        game.status = game.status.FINISHED
        game.phase = GamePhase.FINISHED

        await send_message(
            "👑 <b>THRONE — O‘YIN YAKUNLANDI</b>\n\n"
            f"🏆 G‘olib tomon: <b>{winning_side}</b>\n\n"
            f"📜 Sabab: {reason}"
        )

        self.unregister_game(game.game_id)

    def cancel_game(self, game: GameState) -> None:
        game_scheduler.cancel(game.game_id)
        self._games.pop(game.game_id, None)


game_flow = GameFlow()
