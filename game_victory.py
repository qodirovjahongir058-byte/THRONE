from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from game_engine import GameState
from roles import RoleSide


class VictorySide(StrEnum):
    THRONE = "THRONE"
    BLACK = "BLACK"
    REBEL = "REBEL"
    INDEPENDENT = "INDEPENDENT"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class VictoryResult:
    finished: bool
    winning_side: VictorySide
    reason: str


def check_victory(game: GameState) -> VictoryResult:
    """
    Check whether the current game has reached a victory condition.

    Detailed role-specific victory rules will be added after
    the final 36-role roster is registered.
    """
    alive_players = game.alive_players()

    if not alive_players:
        return VictoryResult(
            finished=True,
            winning_side=VictorySide.NONE,
            reason="no_players_alive",
        )

    side_counts: dict[RoleSide, int] = {
        side: 0
        for side in RoleSide
    }

    for player in alive_players:
        if not player.role_key:
            continue

        # Role definitions are resolved later when the complete
        # 36-role roster is registered.
        side_counts[RoleSide.INDEPENDENT] += 0

    return VictoryResult(
        finished=False,
        winning_side=VictorySide.NONE,
        reason="game_continues",
    )
