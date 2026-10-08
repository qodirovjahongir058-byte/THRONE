from __future__ import annotations

from dataclasses import dataclass

from game_engine import GameState
from game_state import GamePhase, LAST_WORDS_DURATION


@dataclass(frozen=True, slots=True)
class LastWordsResult:
    """Result of a last-words operation."""

    success: bool
    message: str
    player_id: int | None = None


class LastWordsSystem:
    """Manage the 30-second last-words phase."""

    def start(
        self,
        game: GameState,
        player_id: int,
    ) -> LastWordsResult:
        """Start last words for an eliminated player."""

        player = game.get_player(player_id)

        if player is None:
            return LastWordsResult(
                success=False,
                message="player_not_found",
            )

        if player.alive:
            return LastWordsResult(
                success=False,
                message="player_is_alive",
            )

        if game.status.value != "ACTIVE":
            return LastWordsResult(
                success=False,
                message="game_not_active",
            )

        game.phase = GamePhase.LAST_WORDS
        game.last_words_player_id = player_id

        game.metadata["last_words_active"] = True
        game.metadata["last_words_duration"] = LAST_WORDS_DURATION
        game.metadata["last_words_text"] = None

        return LastWordsResult(
            success=True,
            message="last_words_started",
            player_id=player_id,
        )

    def submit(
        self,
        game: GameState,
        player_id: int,
        text: str,
    ) -> LastWordsResult:
        """Save the eliminated player's last words."""

        if game.phase != GamePhase.LAST_WORDS:
            return LastWordsResult(
                success=False,
                message="last_words_not_active",
            )

        if not game.metadata.get("last_words_active"):
            return LastWordsResult(
                success=False,
                message="last_words_not_active",
            )

        if game.last_words_player_id != player_id:
            return LastWordsResult(
                success=False,
                message="not_last_words_player",
            )

        cleaned_text = text.strip()

        if not cleaned_text:
            return LastWordsResult(
                success=False,
                message="empty_last_words",
            )

        game.metadata["last_words_text"] = cleaned_text

        return LastWordsResult(
            success=True,
            message="last_words_saved",
            player_id=player_id,
        )

    def finish(
        self,
        game: GameState,
    ) -> LastWordsResult:
        """Finish the last-words phase."""

        if game.phase != GamePhase.LAST_WORDS:
            return LastWordsResult(
                success=False,
                message="last_words_not_active",
            )

        player_id = game.last_words_player_id

        game.metadata["last_words_active"] = False
        game.metadata.pop("last_words_duration", None)

        game.last_words_player_id = None

        return LastWordsResult(
            success=True,
            message="last_words_finished",
            player_id=player_id,
        )


last_words_system = LastWordsSystem()
