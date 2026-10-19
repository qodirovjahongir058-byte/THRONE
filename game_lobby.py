
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from database import (
    ActiveGameConflict,
    Database,
    DatabaseError,
)
from game_state import GamePhase, GameState, PlayerState


class LobbyError(Exception):
    """Lobby bilan bog'liq xato."""


@dataclass(slots=True)
class LobbyResult:
    success: bool
    game_id: str
    message: str
    player_count: int
    min_players: int
    max_players: int
    data: dict[str, Any]


class GameLobby:
    """THRONE o'yinining lobby jarayonini boshqaradi."""

    def __init__(
        self,
        database: Database,
        min_players: int = 7,
        max_players: int = 50,
        lobby_duration_seconds: int = 1200,
    ) -> None:
        if min_players < 1:
            raise ValueError("min_players kamida 1 bo'lishi kerak.")

        if max_players < min_players:
            raise ValueError(
                "max_players min_players dan kichik bo'lmasligi kerak."
            )

        if lobby_duration_seconds <= 0:
            raise ValueError("Lobby muddati musbat bo'lishi kerak.")

        self.database = database
        self.min_players = min_players
        self.max_players = max_players
        self.lobby_duration_seconds = lobby_duration_seconds

        # Bir jarayon ichidagi faol lobbylar.
        self.lobbies: dict[int, GameState] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_lobby(
        self,
        chat_id: int,
        creator_id: int,
        creator_name: str,
        creator_username: str | None = None,
    ) -> LobbyResult:
        """Guruh uchun yangi lobby yaratadi."""

        current = self.lobbies.get(chat_id)

        if current is not None and current.phase not in {
            GamePhase.FINISHED,
            GamePhase.STOPPED,
        }:
            raise LobbyError(
                "Bu guruhda allaqachon faol o'yin yoki lobby mavjud."
            )

        game = GameState(
            chat_id=chat_id,
            creator_id=creator_id,
            min_players=self.min_players,
            max_players=self.max_players,
            lobby_duration_seconds=self.lobby_duration_seconds,
        )

        game.phase_started_at = self._now()
        game.phase_deadline = (
            self._now().timestamp() + self.lobby_duration_seconds
        )

        creator = PlayerState(
            user_id=creator_id,
            full_name=creator_name,
            username=creator_username,
        )

        try:
            game.add_player(creator)
            self.database.create_game(game)
            self.database.join_game(game, creator)
        except (DatabaseError, ValueError) as exc:
            raise LobbyError(
                f"Lobby yaratilmadi: {exc}"
            ) from exc

        self.lobbies[chat_id] = game

        return self._result(
            game,
            "lobby_created",
            {"deadline": game.phase_deadline},
        )

    def join_lobby(
        self,
        chat_id: int,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> LobbyResult:
        """O'yinchini lobbyga qo'shadi."""

        game = self._get_lobby(chat_id)
        self._check_deadline(game)

        if game.phase != GamePhase.LOBBY:
            raise LobbyError("Bu lobby yangi o'yinchilarni qabul qilmaydi.")

        if user_id in game.players:
            raise LobbyError("Siz bu o'yinga allaqachon qo'shilgansiz.")

        if game.player_count >= game.max_players:
            raise LobbyError(
                "Lobby to'la. Eng ko'p 50 nafar o'yinchi qatnashishi mumkin."
            )

        player = PlayerState(
            user_id=user_id,
            full_name=full_name,
            username=username,
        )

        # Avval bazada akkaunt uchun qulf olinadi.
        # Keyin xotiradagi o'yin holati yangilanadi.
        try:
            self.database.join_game(game, player)
            game.add_player(player)
        except ActiveGameConflict as exc:
            raise LobbyError(str(exc)) from exc
        except (DatabaseError, ValueError) as exc:
            raise LobbyError(
                f"O'yinga qo'shilib bo'lmadi: {exc}"
            ) from exc

        try:
            self.database.save_game(game)
        except DatabaseError as exc:
            # Xotiradagi o'zgarishni qaytarish va olingan qulfni
            # bo'shatish uchun eng yaxshi urinish.
            game.players.pop(user_id, None)
            self.database.release_game_locks(game.game_id)
            raise LobbyError(
                f"O'yinchi holatini saqlab bo'lmadi: {exc}"
            ) from exc

        return self._result(
            game,
            "player_joined",
            {"joined_user_id": user_id},
        )

    def leave_lobby(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbyResult:
        """O'yinchi hali lobby ochiq bo'lsa chiqishi mumkin."""

        game = self._get_lobby(chat_id)
        self._check_deadline(game)

        if game.phase != GamePhase.LOBBY:
            raise LobbyError(
                "O'yin boshlanganidan keyin lobbydan chiqish mumkin emas."
            )

        if user_id not in game.players:
            raise LobbyError("Siz bu lobbyda qatnashmayapsiz.")

        game.remove_lobby_player(user_id)

        try:
            with self.database.connection:
                self.database.connection.execute(
                    """
                    DELETE FROM game_players
                    WHERE game_id = ? AND user_id = ?
                    """,
                    (game.game_id, user_id),
                )

                self.database.connection.execute(
                    """
                    DELETE FROM active_game_locks
                    WHERE game_id = ? AND user_id = ?
                    """,
                    (game.game_id, user_id),
                )
        except Exception as exc:
            raise LobbyError(
                f"Lobbidan chiqishni saqlab bo'lmadi: {exc}"
            ) from exc

        self.database.save_game(game)

        return self._result(
            game,
            "player_left",
            {"left_user_id": user_id},
        )

    def get_lobby(self, chat_id: int) -> LobbyResult:
        """Lobby haqida ma'lumot beradi."""

        game = self._get_lobby(chat_id)
        self._check_deadline(game)

        remaining = None

        if game.phase_deadline is not None:
            remaining = max(
                0,
                int(game.phase_deadline - self._now().timestamp()),
            )

        return self._result(
            game,
            "lobby_status",
            {
                "remaining_seconds": remaining,
                "player_ids": list(game.players.keys()),
                "ready_to_start": game.can_start,
            },
        )

    def start_lobby(
        self,
        chat_id: int,
        requester_id: int,
        is_group_admin: bool,
    ) -> GameState:
        """Faqat guruh administratori lobbydan o'yinga o'tadi."""

        game = self._get_lobby(chat_id)
        self._check_deadline(game)

        if game.phase != GamePhase.LOBBY:
            raise LobbyError("Lobby allaqachon yopilgan.")

        if not is_group_admin:
            raise LobbyError(
                "O'yinni faqat guruh administratori boshlashi mumkin."
            )

        if game.player_count < game.min_players:
            raise LobbyError(
                f"Kamida {game.min_players} nafar o'yinchi kerak. "
                f"Hozir: {game.player_count}."
            )

        # Faqat lobby holatini saqlash. Rollarni taqsimlash
        # game_engine.GameEngine.start_game() orqali bajariladi.
        game.metadata["lobby_closed"] = True
        game.metadata["started_by"] = requester_id
        game.metadata["lobby_closed_at"] = self._now().isoformat()

        self.database.save_game(game)

        return game

    def expire_lobby(self, chat_id: int) -> LobbyResult:
        """Muddati tugagan lobbyni tekshiradi."""

        game = self._get_lobby(chat_id)

        if game.phase != GamePhase.LOBBY:
            raise LobbyError("Bu lobby allaqachon yopilgan.")

        if game.phase_deadline is None:
            raise LobbyError("Lobby muddati belgilanmagan.")

        if self._now().timestamp() < game.phase_deadline:
            raise LobbyError("Lobby muddati hali tugamagan.")

        if game.player_count < game.min_players:
            game.stop()
            game.end_reason = GameEndReason.INSUFFICIENT_PLAYERS
            self.database.finish_game(game)

            return self._result(
                game,
                "lobby_cancelled_insufficient_players",
            )

        return self._result(
            game,
            "lobby_expired_ready_for_admin",
            {"ready_to_start": True},
        )

    def cancel_lobby(
        self,
        chat_id: int,
        requester_id: int,
        is_group_admin: bool,
    ) -> LobbyResult:
        """Guruh administratori lobbyni bekor qilishi mumkin."""

        game = self._get_lobby(chat_id)

        if not is_group_admin:
            raise LobbyError(
                "Lobby faqat guruh administratori tomonidan bekor qilinadi."
            )

        if game.phase != GamePhase.LOBBY:
            raise LobbyError("Faqat lobby bosqichini bekor qilish mumkin.")

        game.metadata["cancelled_by"] = requester_id
        game.stop()
        game.end_reason = GameEndReason.CANCELLED

        self.database.finish_game(game)

        return self._result(game, "lobby_cancelled")

    def _get_lobby(self, chat_id: int) -> GameState:
        game = self.lobbies.get(chat_id)

        if game is None:
            raise LobbyError("Bu guruhda faol lobby topilmadi.")

        return game

    def _check_deadline(self, game: GameState) -> None:
        if (
            game.phase == GamePhase.LOBBY
            and game.phase_deadline is not None
            and self._now().timestamp() >= game.phase_deadline
        ):
            raise LobbyError(
                "Lobby muddati tugagan. "
                "Avval expire_lobby() orqali yakunlang."
            )

    def _result(
        self,
        game: GameState,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> LobbyResult:
        return LobbyResult(
            success=True,
            game_id=game.game_id,
            message=message,
            player_count=game.player_count,
            min_players=game.min_players,
            max_players=game.max_players,
            data=data or {},
        )


def create_lobby_manager(database: Database) -> GameLobby:
    """Lobby boshqaruv obyektini yaratadi."""

    return GameLobby(database=database)
