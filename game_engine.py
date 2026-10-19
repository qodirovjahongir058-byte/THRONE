
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game_resolver import GameResolutionError, GameResolver
from game_state import GameEndReason, GamePhase, GameState
from game_victory import VictoryResult, check_victory
from role_engine import RoleAssignmentError, assign_roles
from roles import Team


class GameEngineError(Exception):
    """THRONE o'yinini boshqarishdagi xatolar."""


@dataclass(slots=True)
class EngineResult:
    success: bool
    phase: GamePhase
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class GameEngine:
    """THRONE o'yinining asosiy boshqaruv markazi."""

    def __init__(self, game: GameState) -> None:
        self.game = game
        self.resolver = GameResolver()

    def start_game(self) -> EngineResult:
        """O'yinni boshlaydi va rollarni taqsimlaydi."""

        if self.game.phase != GamePhase.LOBBY:
            raise GameEngineError("O'yin lobby bosqichida emas.")

        if not self.game.can_start:
            raise GameEngineError(
                f"O'yinni boshlash uchun kamida "
                f"{self.game.min_players} nafar o'yinchi kerak."
            )

        try:
            assign_roles(self.game)
            self.game.start()
        except (RoleAssignmentError, ValueError) as exc:
            raise GameEngineError(
                f"O'yinni boshlash amalga oshmadi: {exc}"
            ) from exc

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="game_started",
            data={
                "game_id": self.game.game_id,
                "player_count": self.game.player_count,
                "round_number": self.game.round_number,
            },
        )

    def begin_night(self) -> EngineResult:
        """Tungi bosqichni boshlaydi."""

        self._require_running()

        allowed = {
            GamePhase.ROLE_REVEAL,
            GamePhase.DAY,
            GamePhase.DISCUSSION,
            GamePhase.VOTING,
            GamePhase.LAST_WORDS,
        }

        if self.game.phase not in allowed:
            raise GameEngineError(
                "Hozir tungi bosqichni boshlash mumkin emas."
            )

        self.game.set_phase(
            GamePhase.NIGHT,
            self.game.night_duration_seconds,
        )

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="night_started",
            data={
                "round_number": self.game.round_number,
                "duration_seconds": self.game.night_duration_seconds,
            },
        )

    def resolve_night(self) -> EngineResult:
        """Tungi harakatlarni hisoblaydi va natijani qaytaradi."""

        self._require_running()

        if self.game.phase != GamePhase.NIGHT:
            raise GameEngineError("Hozir tun bosqichi emas.")

        try:
            night_result = self.resolver.resolve_night(self.game)
        except GameResolutionError as exc:
            raise GameEngineError(str(exc)) from exc

        victory = check_victory(self.game)

        if victory.finished:
            return EngineResult(
                success=True,
                phase=self.game.phase,
                message="game_finished",
                data={
                    "winner": self._winner_value(victory.winner),
                    "reason": victory.reason,
                    "eliminated_player_ids": (
                        night_result.eliminated_player_ids
                    ),
                },
            )

        self.game.set_phase(
            GamePhase.DAY,
            self.game.discussion_duration_seconds,
        )

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="night_resolved",
            data={
                "round_number": night_result.round_number,
                "eliminated_player_ids": (
                    night_result.eliminated_player_ids
                ),
                "protected_player_ids": (
                    night_result.protected_player_ids
                ),
                "blocked_player_ids": (
                    night_result.blocked_player_ids
                ),
                "investigation_results": (
                    night_result.investigation_results
                ),
            },
        )

    def begin_discussion(self) -> EngineResult:
        """Muhokama bosqichini boshlaydi."""

        self._require_running()

        if self.game.phase != GamePhase.DAY:
            raise GameEngineError(
                "Muhokama faqat kunduzgi bosqichda boshlanadi."
            )

        self.game.set_phase(
            GamePhase.DISCUSSION,
            self.game.discussion_duration_seconds,
        )

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="discussion_started",
            data={
                "duration_seconds": (
                    self.game.discussion_duration_seconds
                ),
            },
        )

    def begin_voting(self) -> EngineResult:
        """Ovoz berish bosqichini boshlaydi."""

        self._require_running()

        if self.game.phase not in {
            GamePhase.DAY,
            GamePhase.DISCUSSION,
        }:
            raise GameEngineError(
                "Ovoz berish bosqichini hozir boshlash mumkin emas."
            )

        self.game.set_phase(
            GamePhase.VOTING,
            self.game.voting_duration_seconds,
        )

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="voting_started",
            data={
                "duration_seconds": self.game.voting_duration_seconds,
                "alive_players": self.game.alive_count,
            },
        )

    def begin_last_words(self, player_id: int) -> EngineResult:
        """O'yinchiga so'nggi so'zlar vaqtini beradi."""

        self._require_running()

        if self.game.phase != GamePhase.VOTING:
            raise GameEngineError(
                "So'nggi so'zlar ovoz berishdan keyin boshlanadi."
            )

        player = self.game.get_player(player_id)

        if player is None or not player.is_alive:
            raise GameEngineError(
                "Tanlangan o'yinchi mavjud emas yoki tirik emas."
            )

        self.game.last_words_player_id = player_id

        self.game.set_phase(
            GamePhase.LAST_WORDS,
            self.game.last_words_duration_seconds,
        )

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="last_words_started",
            data={
                "player_id": player_id,
                "duration_seconds": (
                    self.game.last_words_duration_seconds
                ),
            },
        )

    def finish_last_words(self) -> EngineResult:
        """So'nggi so'zlardan keyin o'yin holatini tekshiradi."""

        self._require_running()

        if self.game.phase != GamePhase.LAST_WORDS:
            raise GameEngineError(
                "O'yin so'nggi so'zlar bosqichida emas."
            )

        self.game.last_words_player_id = None

        victory = check_victory(self.game)

        if victory.finished:
            return EngineResult(
                success=True,
                phase=self.game.phase,
                message="game_finished",
                data={
                    "winner": self._winner_value(victory.winner),
                    "reason": victory.reason,
                },
            )

        return self.begin_night()

    def stop_game(self) -> EngineResult:
        """Faol o'yinni to'xtatadi."""

        if self.game.phase in {
            GamePhase.FINISHED,
            GamePhase.STOPPED,
        }:
            raise GameEngineError("O'yin allaqachon yakunlangan.")

        self.game.stop()

        return EngineResult(
            success=True,
            phase=self.game.phase,
            message="game_stopped",
        )

    def get_status(self) -> dict[str, Any]:
        """O'yinning joriy holatini qaytaradi."""

        return {
            "game_id": self.game.game_id,
            "chat_id": self.game.chat_id,
            "phase": self.game.phase.value,
            "round_number": self.game.round_number,
            "player_count": self.game.player_count,
            "alive_count": self.game.alive_count,
            "winner": self._winner_value(self.game.winner),
            "phase_deadline": self.game.phase_deadline,
        }

    def _require_running(self) -> None:
        if not self.game.is_running:
            raise GameEngineError("O'yin faol holatda emas.")

    @staticmethod
    def _winner_value(
        winner: Team | str | None,
    ) -> str | None:
        if winner is None:
            return None

        if isinstance(winner, Team):
            return winner.value

        return str(winner)


def create_engine(game: GameState) -> GameEngine:
    """O'yin uchun boshqaruv obyektini yaratadi."""

    return GameEngine(game)
            
