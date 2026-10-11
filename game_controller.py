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
    GameStatus,
)
from game_victory import check_victory
from keyboards import voting_keyboard
from last_words import last_words_system
from phase_manager import phase_manager
from vote_system import VoteResolution, VoteResult, vote_system


logger = logging.getLogger("throne.game_flow")

SendMessage = Callable[..., Awaitable[object]]


@dataclass(frozen=True, slots=True)
class FlowResult:
    success: bool
    message: str


class GameFlow:
    """Control the automatic phases of a THRONE group game."""

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

        # Har bir o‘yinchining oxirgi tanlangan harakati saqlanadi.
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
        return list(game.metadata.get("night_actions", []))

    def clear_night_actions(self, game: GameState) -> None:
        game.metadata["night_actions"] = []

    @staticmethod
    def _reset_player_night_flags(game: GameState) -> None:
        for player in game.players.values():
            player.has_acted = False
            player.metadata.pop("night_action", None)
            player.metadata.pop("night_target", None)

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

        self._schedule_night(game, send_message)

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

            # Xatoli tungi natijani qo‘llamaymiz.
            # O‘yin NIGHT bosqichida abadiy qolib ketmasligi uchun
            # ushbu tun bekor qilinadi va kunduzgi bosqich boshlanadi.
            self.clear_night_actions(game)
            self._reset_player_night_flags(game)

            await send_message(
                "⚠️ <b>Tungi harakatlarni hisoblashda xatolik yuz berdi.</b>\n"
                "Bu tun natijasi bekor qilindi. O‘yin davom etadi."
            )

            day_result = phase_manager.start_day(game)

            if not day_result.success:
                logger.error(
                    "Could not start day after night error for game_id=%s",
                    game.game_id,
                )
                return

            await send_message(
                day_started_message(game.night_number)
            )

            await self.start_discussion(
                game=game,
                send_message=send_message,
            )
            return

        game.metadata["last_night_results"] = list(
            resolution.context.results
        )

        game.metadata["last_night_eliminated"] = list(
            resolution.eliminated_player_ids
        )

        self.clear_night_actions(game)
        self._reset_player_night_flags(game)

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
            logger.error(
                "Could not start day for game_id=%s: %s",
                game.game_id,
                result.message,
            )
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
                        player.display_name or str(player.user_id)
                    )

            if names:
                await send_message(
                    "🌅 <b>Tun yakuni</b>\n\n"
                    "⚔️ Bu tun yo‘q qilinganlar:\n"
                    + "\n".join(
                        f"• {name}"
                        for name in names
                    )
                )

                # Hozirgi mexanizm bo‘yicha tungi o‘limlardan
                # faqat birinchi o‘yinchiga so‘nggi so‘z beriladi.
                await self._start_last_words(
                    game=game,
                    player_id=eliminated[0],
                    send_message=send_message,
                    next_phase=GamePhase.DISCUSSION,
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
        *,
        next_phase: GamePhase,
    ) -> None:
        result = last_words_system.start(
            game=game,
            player_id=player_id,
        )

        if not result.success:
            game.metadata.pop("last_words_next_phase", None)

            if next_phase == GamePhase.NIGHT:
                await self._start_next_night(game, send_message)
            else:
                await self.start_discussion(
                    game=game,
                    send_message=send_message,
                )
            return

        player = game.get_player(player_id)

        if player is None:
            last_words_system.finish(game)
            game.metadata.pop("last_words_next_phase", None)

            if next_phase == GamePhase.NIGHT:
                await self._start_next_night(game, send_message)
            else:
                await self.start_discussion(
                    game=game,
                    send_message=send_message,
                )
            return

        game.metadata["last_words_next_phase"] = next_phase.value

        await send_message(
            "🕯️ <b>So‘nggi so‘z</b>\n\n"
            f"👤 <b>{player.display_name}</b>\n\n"
            "30 soniya ichida so‘nggi so‘zini botga "
            "shaxsiy xabarda yuborishi mumkin."
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
                        f"👤 {player.display_name} so‘z qoldirmadi."
                    )

        victory = check_victory(game)

        if victory.finished:
            game.metadata.pop("last_words_next_phase", None)

            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return

        next_phase_value = game.metadata.pop(
            "last_words_next_phase",
            GamePhase.DISCUSSION.value,
        )

        if next_phase_value == GamePhase.NIGHT.value:
            # Kunduzgi ovoz berishdan keyingi so‘nggi so‘z tugadi.
            await self._start_next_night(game, send_message)
        else:
            # Tungi o‘limdan keyingi so‘nggi so‘z tugadi.
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

        await self.start_voting(game, send_message)

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
            # Teng ovoz olgan nomzodlarni saqlaymiz va ovozlarni
            # qayta boshlash uchun tozalaymiz.
            vote_system.start_revote(
                game,
                resolution.tied_player_ids,
            )

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
        resolution: VoteResolution,
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

            await self._start_next_night(game, send_message)
            return

        if resolution.eliminated_player_id is None:
            await self._start_next_night(game, send_message)
            return

        player = game.get_player(
            resolution.eliminated_player_id
        )

        if player is None:
            await self._start_next_night(game, send_message)
            return

        await send_message(
            "⚖️ <b>Ovoz natijasi</b>\n\n"
            f"❌ <b>{player.display_name}</b> "
            "o‘yindan chiqarildi."
        )

        await self._start_last_words(
            game=game,
            player_id=player.user_id,
            send_message=send_message,
            next_phase=GamePhase.NIGHT,
        )

    async def _start_next_night(
        self,
        game: GameState,
        send_message: SendMessage,
    ) -> None:
        result = phase_manager.start_next_night(game)

        if not result.success:
            logger.error(
                "Could not start next night for game_id=%s: %s",
                game.game_id,
                result.message,
            )
            return

        self.clear_night_actions(game)

        await send_message(
            night_started_message(game.night_number)
        )

        self._schedule_night(game, send_message)

    async def _finish_game(
        self,
        game: GameState,
        winning_side: str,
        reason: str,
        send_message: SendMessage,
    ) -> None:
        game_scheduler.cancel(game.game_id)

        game.status = GameStatus.FINISHED
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
