from __future__ import annotations

from enum import StrEnum


class GamePhase(StrEnum):
    """All possible phases of a THRONE group game."""

    LOBBY = "LOBBY"
    ROLE_REVEAL = "ROLE_REVEAL"
    NIGHT = "NIGHT"
    DAY = "DAY"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    LAST_WORDS = "LAST_WORDS"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


class GameStatus(StrEnum):
    """Persistent game status values."""

    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


class NightPhase(StrEnum):
    """Order of night action processing."""

    OBSERVE = "OBSERVE"
    PROTECT = "PROTECT"
    BLOCK = "BLOCK"
    POISON = "POISON"
    WEAKEN = "WEAKEN"
    ATTACK = "ATTACK"
    SPECIAL = "SPECIAL"
    RESOLVE = "RESOLVE"
    MORNING = "MORNING"


class VoteResult(StrEnum):
    """Possible outcomes of a voting round."""

    PENDING = "PENDING"
    ELIMINATED = "ELIMINATED"
    REVOTE = "REVOTE"
    NO_ELIMINATION = "NO_ELIMINATION"


MIN_PLAYERS = 7
MAX_PLAYERS = 36

LAST_WORDS_DURATION = 30

DEFAULT_DISCUSSION_DURATION = 120
DEFAULT_VOTING_DURATION = 60
DEFAULT_NIGHT_DURATION = 90


def is_valid_player_count(player_count: int) -> bool:
    """Return True when the player count is within THRONE limits."""
    return MIN_PLAYERS <= player_count <= MAX_PLAYERS


def is_active_phase(phase: GamePhase) -> bool:
    """Return True when a game is currently in an active phase."""
    return phase not in {
        GamePhase.FINISHED,
        GamePhase.STOPPED,
    }


def is_night_phase(phase: GamePhase) -> bool:
    """Return True when the game is in a night-related phase."""
    return phase == GamePhase.NIGHT
