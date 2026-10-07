from __future__ import annotations

from dataclasses import dataclass

from game_actions import ActionType
from game_engine import GameState, PlayerState
from roles import RoleAbilityType, RoleDefinition, RoleSide, get_role


@dataclass(frozen=True, slots=True)
class RoleActionRule:
    """Defines what a role can do during the night."""

    action_type: ActionType
    requires_target: bool = True
    uses_per_game: int | None = None


@dataclass(frozen=True, slots=True)
class RoleRuntimeInfo:
    """Runtime information about one player's role."""

    role: RoleDefinition
    action_rules: tuple[RoleActionRule, ...]


def get_player_role(
    player: PlayerState,
) -> RoleDefinition | None:
    """Return the role definition assigned to a player."""

    if not player.role_key:
        return None

    return get_role(player.role_key)


def get_role_side(
    player: PlayerState,
) -> RoleSide | None:
    """Return the faction of a player's role."""

    role = get_player_role(player)

    if role is None:
        return None

    return role.side


def build_role_runtime_info(
    player: PlayerState,
) -> RoleRuntimeInfo | None:
    """Build runtime information for a player's current role."""

    role = get_player_role(player)

    if role is None:
        return None

    rules = _build_action_rules(role)

    return RoleRuntimeInfo(
        role=role,
        action_rules=rules,
    )


def can_use_action(
    game: GameState,
    actor_id: int,
    action_type: ActionType,
) -> bool:
    """Check whether a player can currently use an action."""

    player = game.get_player(actor_id)

    if player is None:
        return False

    if not player.alive:
        return False

    if player.blocked:
        return False

    runtime_info = build_role_runtime_info(player)

    if runtime_info is None:
        return False

    return any(
        rule.action_type == action_type
        for rule in runtime_info.action_rules
    )


def action_requires_target(
    game: GameState,
    actor_id: int,
    action_type: ActionType,
) -> bool:
    """Check whether the selected action requires a target."""

    player = game.get_player(actor_id)

    if player is None:
        return False

    runtime_info = build_role_runtime_info(player)

    if runtime_info is None:
        return False

    for rule in runtime_info.action_rules:
        if rule.action_type == action_type:
            return rule.requires_target

    return False


def _build_action_rules(
    role: RoleDefinition,
) -> tuple[RoleActionRule, ...]:
    """Create the basic action rules for a role."""

    ability_type = role.ability_type

    if ability_type == RoleAbilityType.INFORMATION:
        return (
            RoleActionRule(
                action_type=ActionType.OBSERVE,
                requires_target=True,
            ),
        )

    if ability_type == RoleAbilityType.PROTECTION:
        return (
            RoleActionRule(
                action_type=ActionType.PROTECT,
                requires_target=True,
            ),
        )

    if ability_type == RoleAbilityType.CONTROL:
        return (
            RoleActionRule(
                action_type=ActionType.BLOCK,
                requires_target=True,
            ),
        )

    if ability_type == RoleAbilityType.ATTACK:
        return (
            RoleActionRule(
                action_type=ActionType.ATTACK,
                requires_target=True,
            ),
        )

    if ability_type == RoleAbilityType.ECONOMY:
        return (
            RoleActionRule(
                action_type=ActionType.SPECIAL,
                requires_target=False,
            ),
        )

    if ability_type == RoleAbilityType.SPECIAL:
        return (
            RoleActionRule(
                action_type=ActionType.SPECIAL,
                requires_target=True,
            ),
        )

    if ability_type == RoleAbilityType.PASSIVE:
        return ()

    return ()
