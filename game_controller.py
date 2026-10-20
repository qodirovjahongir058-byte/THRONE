
from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from typing import Any

from aiogram import Bot

from database import Database
from game_actions import GameActionManager
from game_engine import GameEngine, GameEngineError
from game_lobby import GameLobby, LobbyError
from game_notifications import GameNotifications
from game_partners import GamePartners
from game_private_messages import GamePrivateMessages
from game_state import GamePhase, GameState
from game_timer import GameTimer, TimerPhase
from game_voting import GameVoting, VotingError
from role_engine import assign_roles
from game_victory import check_victory


logger = logging.getLogger(__name__)


class GameControllerError(Exception):
    """O'yin boshqaruvi xatosi."""


@dataclass(frozen=True, slots=True)
class ControllerResult:
    success: bool
    message: str
    game_id: str | None = None
    phase: str | None = None
    data: dict[str, Any] | None = None


class GameController:
    """THRONE o'yin tizimlarini boshqaradi."""

    def __init__(
        self,
        bot: Bot,
        database: Database,
        lobby: GameLobby,
        engine: GameEngine,
        timer: GameTimer,
        voting: GameVoting,
        actions: GameActionManager,
        partners: GamePartners,
    ) -> None:
        self.bot = bot
        self.database = database
        self.lobby = lobby
        self.engine = engine
        self.timer = timer
        self.voting = voting
        self.actions = actions
        self.partners = partners

        self.notifications = GameNotifications(bot)
        self.private_messages = GamePrivateMessages(bot, partners)

        self._games: dict[int, GameState] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._closed = False

    def register_game(self, game: GameState) -> None:
        """O'yinni controller xotirasiga qo'shadi."""
        if self._closed:
            raise GameControllerError(
                "Controller yopilgan."
            )

        self._games[game.chat_id] = game
        self._locks.setdefault(
            game.chat_id,
            asyncio.Lock(),
        )

    def get_game(
        self,
        chat_id: int,
    ) -> GameState | None:
        return self._games.get(chat_id)

    def get_active_games(self) -> list[GameState]:
        return [
            game
            for game in self._games.values()
            if game.phase not in (
                GamePhase.FINISHED,
                GamePhase.STOPPED,
            )
        ]

    async def create_game(
        self,
        chat_id: int,
        creator_id: int,
        creator_name: str,
        username: str | None = None,
    ) -> ControllerResult:
        self._ensure_open()

        try:
            game = await self.lobby.create_lobby(
                chat_id=chat_id,
                creator_id=creator_id,
                creator_name=creator_name,
                username=username,
            )

            self.register_game(game)

            await self.notifications.lobby_created(
                chat_id=chat_id,
                creator_name=creator_name,
                game_id=game.game_id,
                min_players=game.min_players,
                max_players=game.max_players,
                duration_minutes=(
                    game.lobby_duration_seconds // 60
                ),
            )

            return self._result(
                True,
                "Yangi lobby yaratildi.",
                game,
            )

        except (LobbyError, GameControllerError) as exc:
            return ControllerResult(
                success=False,
                message=str(exc),
            )

    async def join_game(
        self,
        chat_id: int,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "Bu guruhda faol lobby yo'q.",
                )

            try:
                player = await self.lobby.join_lobby(
                    game=game,
                    user_id=user_id,
                    full_name=full_name,
                    username=username,
                )

                await self.notifications.player_joined(
                    chat_id=chat_id,
                    player_name=player.full_name,
                    player_count=game.player_count,
                    max_players=game.max_players,
                )

                return self._result(
                    True,
                    "O'yinga qo'shildingiz.",
                    game,
                )

            except LobbyError as exc:
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def leave_game(
        self,
        chat_id: int,
        user_id: int,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "Faol o'yin topilmadi.",
                )

            player = game.get_player(user_id)

            if player is None:
                return self._result(
                    False,
                    "Siz bu o'yinda qatnashmayapsiz.",
                    game,
                )

            if game.phase != GamePhase.LOBBY:
                return self._result(
                    False,
                    "Boshlangan o'yinni bu buyruq bilan "
                    "tark eta olmaysiz.",
                    game,
                )

            player_name = player.full_name

            try:
                await self.lobby.leave_lobby(
                    game=game,
                    user_id=user_id,
                )

                await self.notifications.player_left(
                    chat_id=chat_id,
                    player_name=player_name,
                    player_count=game.player_count,
                    max_players=game.max_players,
                )

                return self._result(
                    True,
                    "Lobbyni tark etdingiz.",
                    game,
                )

            except LobbyError as exc:
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def start_game(
        self,
        chat_id: int,
        requester_id: int,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "Boshlash uchun lobby topilmadi.",
                )

            if requester_id != game.creator_id:
                return self._result(
                    False,
                    "O'yinni faqat uni yaratgan admin "
                    "boshlashi mumkin.",
                    game,
                )

            if not game.can_start:
                return self._result(
                    False,
                    f"O'yin boshlanishi uchun kamida "
                    f"{game.min_players} o'yinchi kerak.",
                    game,
                )

            try:
                await self.timer.cancel_game(
                    game.game_id
                )

                engine_result = self.engine.start_game(
                    game
                )

                if not engine_result.success:
                    return self._result(
                        False,
                        engine_result.message,
                        game,
                    )

                self.database.save_game(game)

                await self.notifications.game_started(
                    chat_id=chat_id,
                    player_count=game.player_count,
                )

                role_results = (
                    await self.private_messages.send_roles_to_all(
                        game
                    )
                )

                partner_result = None

                try:
                    partner_result = self.partners.build(
                        game
                    )
                except Exception:
                    logger.exception(
                        "Sheriklar ma'lumotini yaratishda xato."
                    )

                if partner_result is not None:
                    for user_id in partner_result:
                        try:
                            await self.private_messages.send_partner_info(
                                game,
                                user_id,
                            )
                        except Exception:
                            logger.exception(
                                "Sherik haqida xabar yuborilmadi: %s",
                                user_id,
                            )

                return self._result(
                    True,
                    "O'yin boshlandi. Rollar shaxsiy "
                    "xabarlarga yuborildi.",
                    game,
                    {
                        "role_messages": role_results,
                    },
                )

            except (
                GameEngineError,
                LobbyError,
            ) as exc:
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def begin_night(
        self,
        chat_id: int,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "O'yin topilmadi.",
                )

            try:
                result = self.engine.begin_night(game)

                if not result.success:
                    return self._result(
                        False,
                        result.message,
                        game,
                    )

                self.database.save_game(game)

                await self.notifications.night_started(
                    chat_id=chat_id,
                    round_number=game.round_number,
                    duration_seconds=game.night_duration_seconds,
                )

                return self._result(
                    True,
                    "Tun boshlandi.",
                    game,
                )

            except GameEngineError as exc:
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def resolve_night(
        self,
        chat_id: int,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "O'yin topilmadi.",
                )

            try:
                result = self.engine.resolve_night(game)

                if not result.success:
                    return self._result(
                        False,
                        result.message,
                        game,
                    )

                if game.phase == GamePhase.FINISHED:
                    await self._finish_notifications(game)
                else:
                    await self.notifications.day_started(
                        chat_id=chat_id,
                        round_number=game.round_number,
                        duration_seconds=(
                            game.discussion_duration_seconds
                        ),
                    )

                self.database.save_game(game)

                return self._result(
                    True,
                    result.message,
                    game,
                    result.data,
                )

            except GameEngineError as exc:
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def begin_discussion(
        self,
        chat_id: int,
    ) -> ControllerResult:
        game = self._games.get(chat_id)

        if game is None:
            return ControllerResult(
                False,
                "O'yin topilmadi.",
            )

        try:
            result = self.engine.begin_discussion(game)

            if not result.success:
                return self._result(
                    False,
                    result.message,
                    game,
                )

            self.database.save_game(game)

            await self.notifications.discussion_started(
                chat_id,
                game.discussion_duration_seconds,
            )

            return self._result(
                True,
                "Muhokama boshlandi.",
                game,
            )

        except GameEngineError as exc:
            return self._result(
                False,
                str(exc),
                game,
            )

    async def begin_voting(
        self,
        chat_id: int,
    ) -> ControllerResult:
        game = self._games.get(chat_id)

        if game is None:
            return ControllerResult(
                False,
                "O'yin topilmadi.",
            )

        try:
            result = self.engine.begin_voting(game)

            if not result.success:
                return self._result(
                    False,
                    result.message,
                    game,
                )

            self.database.save_game(game)

            await self.notifications.voting_started(
                chat_id,
                game.voting_duration_seconds,
            )

            return self._result(
                True,
                "Ovoz berish boshlandi.",
                game,
            )

        except GameEngineError as exc:
            return self._result(
                False,
                str(exc),
                game,
            )

    async def cast_vote(
        self,
        chat_id: int,
        voter_id: int,
        target_id: int,
    ) -> ControllerResult:
        game = self._games.get(chat_id)

        if game is None:
            return ControllerResult(
                False,
                "O'yin topilmadi.",
            )

        try:
            result = self.voting.cast_vote(
                game=game,
                voter_id=voter_id,
                target_id=target_id,
            )

            self.database.save_game(game)

            return self._result(
                True,
                getattr(
                    result,
                    "message",
                    "Ovozingiz qabul qilindi.",
                ),
                game,
            )

        except (VotingError, AttributeError, TypeError) as exc:
            return self._result(
                False,
                str(exc),
                game,
            )

    async def stop_game(
        self,
        chat_id: int,
        requester_id: int,
    ) -> ControllerResult:
        self._ensure_open()

        lock = self._get_lock(chat_id)

        async with lock:
            game = self._games.get(chat_id)

            if game is None:
                return ControllerResult(
                    False,
                    "O'yin topilmadi.",
                )

            if requester_id != game.creator_id:
                return self._result(
                    False,
                    "O'yinni faqat yaratuvchi to'xtata oladi.",
                    game,
                )

            try:
                result = self.engine.stop_game(game)

                await self.timer.cancel_game(
                    game.game_id
                )

                if game.phase == GamePhase.STOPPED:
                    self.database.finish_game(game)

                await self.notifications.lobby_cancelled(
                    chat_id,
                    "O'yin yaratuvchi tomonidan to'xtatildi.",
                )

                return self._result(
                    result.success,
                    result.message,
                    game,
                )

            except (GameEngineError, Exception) as exc:
                logger.exception("O'yinni to'xtatishda xato.")
                return self._result(
                    False,
                    str(exc),
                    game,
                )

    async def _finish_notifications(
        self,
        game: GameState,
    ) -> None:
        winner = game.winner

        if winner is None:
            winner_name = "Durang"
        else:
            winner_name = str(
                getattr(winner, "value", winner)
            )

        await self.notifications.game_finished(
            chat_id=game.chat_id,
            winner_name=winner_name,
            reason=(
                str(getattr(game.end_reason, "value", game.end_reason))
                if game.end_reason is not None
                else None
            ),
        )

    def _get_lock(
        self,
        chat_id: int,
    ) -> asyncio.Lock:
        return self._locks.setdefault(
            chat_id,
            asyncio.Lock(),
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise GameControllerError(
                "GameController yopilgan."
            )

    @staticmethod
    def _result(
        success: bool,
        message: str,
        game: GameState,
        data: dict[str, Any] | None = None,
    ) -> ControllerResult:
        return ControllerResult(
            success=success,
            message=message,
            game_id=game.game_id,
            phase=str(game.phase.value),
            data=data,
        )

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        try:
            await self.timer.close()
        except Exception:
            logger.exception("Taymerni yopishda xato.")

    async def __aenter__(self) -> GameController:
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc: Any,
        traceback: Any,
    ) -> None:
        await self.close()


def create_game_controller(
    bot: Bot,
    database: Database,
    lobby: GameLobby,
    engine: GameEngine,
    timer: GameTimer,
    voting: GameVoting,
    actions: GameActionManager,
    partners: GamePartners,
) -> GameController:
    return GameController(
        bot=bot,
        database=database,
        lobby=lobby,
        engine=engine,
        timer=timer,
        voting=voting,
        actions=actions,
        partners=partners,
            )
        
