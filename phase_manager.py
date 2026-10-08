from __future__ import annotations

from dataclasses import dataclass

from game_engine import GameState
from game_state import GamePhase, GameStatus


@dataclass(frozen=True, slots=True)
class PhaseResult:
    """Result of a phase transition."""

    success: bool
    phase: GamePhase
    message: str


class PhaseManager:
    """Control THRONE game phase transitions."""

    def start_role_reveal(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.phase = GamePhase.ROLE_REVEAL

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="role_reveal_started",
        )

    def start_first_night(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.round_number = 1
        game.night_number = 1
        game.phase = GamePhase.NIGHT

        game.reset_night_actions()

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="first_night_started",
        )

    def start_next_night(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.night_number += 1
        game.round_number += 1
        game.phase = GamePhase.NIGHT

        game.reset_night_actions()

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="next_night_started",
        )

    def start_day(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.phase = GamePhase.DAY

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="day_started",
        )

    def start_discussion(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.phase = GamePhase.DISCUSSION

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="discussion_started",
        )

    def start_voting(
        self,
        game: GameState,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        game.reset_votes()
        game.phase = GamePhase.VOTING

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="voting_started",
        )

    def start_last_words(
        self,
        game: GameState,
        player_id: int,
    ) -> PhaseResult:
        if game.status != GameStatus.ACTIVE:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="game_not_active",
            )

        player = game.get_player(player_id)

        if player is None:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="player_not_found",
            )

        if player.alive:
            return PhaseResult(
                success=False,
                phase=game.phase,
                message="player_is_alive",
            )

        game.last_words_player_id = player_id
        game.phase = GamePhase.LAST_WORDS

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="last_words_started",
        )

    def finish(
        self,
        game: GameState,
    ) -> PhaseResult:
        game.status = GameStatus.FINISHED
        game.phase = GamePhase.FINISHED

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="game_finished",
        )

    def stop(
        self,
        game: GameState,
    ) -> PhaseResult:
        game.status = GameStatus.STOPPED
        game.phase = GamePhase.STOPPED

        return PhaseResult(
            success=True,
            phase=game.phase,
            message="game_stopped",
        )


phase_manager = PhaseManager()
