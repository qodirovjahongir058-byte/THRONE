from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game_state import GamePhase, GameStatus


@dataclass(slots=True)
class PlayerState:
    """Runtime state of a player inside a game."""

    user_id: int
    username: str | None = None
    display_name: str = ""
    role_key: str | None = None

    alive: bool = True
    connected: bool = True
    has_acted: bool = False
    protected: bool = False
    blocked: bool = False
    poisoned: bool = False
    weakened: bool = False

    votes_received: int = 0
    voted_for: int | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GameState:
    """Complete runtime state of one THRONE game."""

    game_id: int
    chat_id: int

    status: GameStatus = GameStatus.WAITING
    phase: GamePhase = GamePhase.LOBBY

    round_number: int = 0
    night_number: int = 0

    players: dict[int, PlayerState] = field(default_factory=dict)

    current_target: int | None = None
    last_words_player_id: int | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def add_player(self, player: PlayerState) -> bool:
        """Add a player if they are not already in the game."""
        if player.user_id in self.players:
            return False

        self.players[player.user_id] = player
        return True

    def remove_player(self, user_id: int) -> bool:
        """Remove a player from the current lobby."""
        if user_id not in self.players:
            return False

        del self.players[user_id]
        return True

    def get_player(self, user_id: int) -> PlayerState | None:
        """Return a player by Telegram user ID."""
        return self.players.get(user_id)

    def alive_players(self) -> list[PlayerState]:
        """Return all currently alive players."""
        return [
            player
            for player in self.players.values()
            if player.alive
        ]

    def alive_count(self) -> int:
        """Return the number of living players."""
        return sum(
            1
            for player in self.players.values()
            if player.alive
        )

    def player_count(self) -> int:
        """Return the total number of players."""
        return len(self.players)

    def reset_night_actions(self) -> None:
        """Reset temporary action flags at the start of a new night."""
        for player in self.players.values():
            player.has_acted = False
            player.protected = False
            player.blocked = False
            player.poisoned = False
            player.weakened = False
            player.metadata.pop("night_target", None)
            player.metadata.pop("night_action", None)

    def reset_votes(self) -> None:
        """Reset voting information for a new voting round."""
        for player in self.players.values():
            player.votes_received = 0
            player.voted_for = None
