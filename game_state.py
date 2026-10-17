from __future__ import annotations

from enum import Enum


# Game settings
MIN_PLAYERS = 7
MAX_PLAYERS = 36

LAST_WORDS_DURATION = 30
DEFAULT_DISCUSSION_DURATION = 120
DEFAULT_VOTING_DURATION = 60
DEFAULT_NIGHT_DURATION = 90


# Game phases
class GamePhase(str, Enum):
    LOBBY = "LOBBY"
    ROLE_REVEAL = "ROLE_REVEAL"
    NIGHT = "NIGHT"
    DAY = "DAY"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    REVOTE = "REVOTE"
    LAST_WORDS = "LAST_WORDS"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


# Game status
class GameStatus(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


# Voting results
class VoteResult(str, Enum):
    ELIMINATED = "ELIMINATED"
    NO_ELIMINATION = "NO_ELIMINATION"
    REVOTE = "REVOTE"
