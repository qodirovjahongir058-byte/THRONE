from __future__ import annotations

from dataclasses import dataclass

from game_engine import GameState, PlayerState
from game_state import (
    GamePhase,
    GameStatus,
    MAX_PLAYERS,
    MIN_PLAYERS,
)
from role_assignment import assign_roles


@dataclass(frozen=True, slots=True)
class ServiceResult:
    """Standard result returned by game service operations."""

    success: bool
    message: str
    game: GameState | None = None


class GameService:
    """Manage active THRONE games in memory."""

    def __init__(self) -> None:
        self._games: dict[int, GameState] = {}
        self._next_game_id: int = 1

    def get_game(self, chat_id: int) -> GameState | None:
        """Return the active game for a chat."""
        return self._games.get(chat_id)

    def create_game(self, chat_id: int) -> ServiceResult:
        """Create a new lobby if the chat has no active game."""

        existing_game = self.get_game(chat_id)

        if existing_game is not None:
            if existing_game.status in {
                GameStatus.WAITING,
                GameStatus.ACTIVE,
            }:
                return ServiceResult(
                    success=False,
                    message="active_game_exists",
                    game=existing_game,
                )

            del self._games[chat_id]

        game = GameState(
            game_id=self._next_game_id,
            chat_id=chat_id,
            status=GameStatus.WAITING,
            phase=GamePhase.LOBBY,
        )

        self._next_game_id += 1
        self._games[chat_id] = game

        return ServiceResult(
            success=True,
            message="game_created",
            game=game,
        )

    def add_player(
        self,
        chat_id: int,
        player: PlayerState,
    ) -> ServiceResult:
        """Add one player to the lobby."""

        game = self.get_game(chat_id)

        if game is None:
            return ServiceResult(
                success=False,
                message="game_not_found",
            )

        if game.status != GameStatus.WAITING:
            return ServiceResult(
                success=False,
                message="game_not_waiting",
                game=game,
            )

        if game.phase != GamePhase.LOBBY:
            return ServiceResult(
                success=False,
                message="lobby_closed",
                game=game,
            )

        if game.player_count() >= MAX_PLAYERS:
            return ServiceResult(
                success=False,
                message="game_full",
                game=game,
            )

        if player.user_id in game.players:
            return ServiceResult(
                success=False,
                message="player_already_joined",
                game=game,
            )

        if not game.add_player(player):
            return ServiceResult(
                success=False,
                message="player_add_failed",
                game=game,
            )

        return ServiceResult(
            success=True,
            message="player_joined",
            game=game,
        )

    def can_start(self, chat_id: int) -> bool:
        """Return whether the game has enough players to start."""

        game = self.get_game(chat_id)

        if game is None:
            return False

        if game.status != GameStatus.WAITING:
            return False

        if game.phase != GamePhase.LOBBY:
            return False

        return MIN_PLAYERS <= game.player_count() <= MAX_PLAYERS

    def start_game(self, chat_id: int) -> ServiceResult:
        """Assign roles and move the lobby into role reveal."""

        game = self.get_game(chat_id)

        if game is None:
            return ServiceResult(
                success=False,
                message="game_not_found",
            )

        if not self.can_start(chat_id):
            return ServiceResult(
                success=False,
                message="not_enough_players",
                game=game,
            )

        try:
            assign_roles(game)
        except ValueError as error:
            return ServiceResult(
                success=False,
                message=str(error),
                game=game,
            )

        game.status = GameStatus.ACTIVE
        game.phase = GamePhase.ROLE_REVEAL

        return ServiceResult(
            success=True,
            message="game_started",
            game=game,
        )

    def stop_game(self, chat_id: int) -> ServiceResult:
        """Stop the current game."""

        game = self.get_game(chat_id)

        if game is None:
            return ServiceResult(
                success=False,
                message="game_not_found",
            )

        if game.status in {
            GameStatus.FINISHED,
            GameStatus.STOPPED,
        }:
            return ServiceResult(
                success=False,
                message="game_already_closed",
                game=game,
            )

        game.status = GameStatus.STOPPED
        game.phase = GamePhase.STOPPED

        return ServiceResult(
            success=True,
            message="game_stopped",
            game=game,
        )

    def finish_game(self, chat_id: int) -> ServiceResult:
        """Mark the current game as finished."""

        game = self.get_game(chat_id)

        if game is None:
            return ServiceResult(
                success=False,
                message="game_not_found",
            )

        game.status = GameStatus.FINISHED
        game.phase = GamePhase.FINISHED

        return ServiceResult(
            success=True,
            message="game_finished",
            game=game,
        )

    def remove_game(self, chat_id: int) -> None:
        """Remove a closed game from the active-game registry."""

        self._games.pop(chat_id, None)


game_service = GameService()
