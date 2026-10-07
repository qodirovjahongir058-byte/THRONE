from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ActionType(StrEnum):
    """Types of actions that can occur during a game."""

    OBSERVE = "OBSERVE"
    PROTECT = "PROTECT"
    BLOCK = "BLOCK"
    POISON = "POISON"
    WEAKEN = "WEAKEN"
    ATTACK = "ATTACK"
    SPECIAL = "SPECIAL"


@dataclass(frozen=True, slots=True)
class GameAction:
    """A single secret action selected by a player."""

    actor_id: int
    action_type: ActionType
    target_id: int | None = None
    secondary_target_id: int | None = None


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Result produced after resolving a game action."""

    action: GameAction
    success: bool
    message_key: str
    data: dict[str, object] | None = None


def create_action(
    actor_id: int,
    action_type: ActionType,
    target_id: int | None = None,
    secondary_target_id: int | None = None,
) -> GameAction:
    """Create a validated game action."""
    if actor_id <= 0:
        raise ValueError("actor_id must be a positive integer")

    if target_id is not None and target_id <= 0:
        raise ValueError("target_id must be a positive integer")

    if secondary_target_id is not None and secondary_target_id <= 0:
        raise ValueError(
            "secondary_target_id must be a positive integer"
        )

    return GameAction(
        actor_id=actor_id,
        action_type=action_type,
        target_id=target_id,
        secondary_target_id=secondary_target_id,
    )
