from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from game_engine import GameState
from roles import RoleSide, get_role


class VictorySide(StrEnum):
    KRON = "KRON"
    SOYA = "SOYA"
    YAKKA = "YAKKA"
    LEGION = "LEGION"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class VictoryResult:
    """Result of a victory check."""

    finished: bool
    winning_side: VictorySide
    reason: str


def get_alive_side_counts(
    game: GameState,
) -> dict[RoleSide, int]:
    """Count living players by their role side."""

    counts: dict[RoleSide, int] = {
        side: 0
        for side in RoleSide
    }

    for player in game.alive_players():
        if not player.role_key:
            continue

        role = get_role(player.role_key)

        if role is None:
            continue

        counts[role.side] += 1

    return counts


def check_victory(game: GameState) -> VictoryResult:
    """
    Check the current game victory conditions.

    This function handles the core faction-level ending rules.
    Individual role victory conditions are evaluated separately by
    the role-specific victory system.
    """

    alive_players = game.alive_players()

    if not alive_players:
        return VictoryResult(
            finished=True,
            winning_side=VictorySide.NONE,
            reason="no_players_alive",
        )

    side_counts = get_alive_side_counts(game)

    kron_count = side_counts[RoleSide.KRON]
    soya_count = side_counts[RoleSide.SOYA]

    total_alive = len(alive_players)

    # SOYA:
    # Soya controls at least 50% of all living players.
    if soya_count > 0 and (soya_count * 2) >= total_alive:
        return VictoryResult(
            finished=True,
            winning_side=VictorySide.SOYA,
            reason="soya_controls_at_least_half",
        )

    # KRON:
    # If there are no living SOYA players, KRON wins.
    if kron_count > 0 and soya_count == 0:
        return VictoryResult(
            finished=True,
            winning_side=VictorySide.KRON,
            reason="soya_eliminated",
        )

    return VictoryResult(
        finished=False,
        winning_side=VictorySide.NONE,
        reason="game_continues",
    )
