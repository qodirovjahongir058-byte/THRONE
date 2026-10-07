from __future__ import annotations

from dataclasses import dataclass, field

from game_actions import ActionType, GameAction
from game_engine import GameState


@dataclass(slots=True)
class ResolutionContext:
    """Temporary state used while resolving one night."""

    blocked_players: set[int] = field(default_factory=set)
    protected_players: set[int] = field(default_factory=set)
    attacked_players: set[int] = field(default_factory=set)
    poisoned_players: set[int] = field(default_factory=set)
    weakened_players: set[int] = field(default_factory=set)

    observations: dict[int, list[int]] = field(default_factory=dict)
    results: list[str] = field(default_factory=list)


ACTION_PRIORITY: dict[ActionType, int] = {
    ActionType.OBSERVE: 10,
    ActionType.PROTECT: 20,
    ActionType.BLOCK: 30,
    ActionType.POISON: 40,
    ActionType.WEAKEN: 50,
    ActionType.ATTACK: 60,
    ActionType.SPECIAL: 70,
}


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """Result of resolving all submitted night actions."""

    success: bool
    context: ResolutionContext
    eliminated_player_ids: tuple[int, ...]


def sort_actions(actions: list[GameAction]) -> list[GameAction]:
    """Return actions in their defined resolution order."""
    return sorted(
        actions,
        key=lambda action: ACTION_PRIORITY[action.action_type],
    )


def resolve_night(
    game: GameState,
    actions: list[GameAction],
) -> ResolutionResult:
    """
    Resolve one complete night.

    This function currently provides the core resolution pipeline.
    Role-specific rules are added through dedicated mechanics without
    changing the public result structure.
    """
    context = ResolutionContext()

    valid_actions: list[GameAction] = []

    for action in actions:
        actor = game.get_player(action.actor_id)

        if actor is None:
            continue

        if not actor.alive:
            continue

        if actor.blocked:
            continue

        valid_actions.append(action)

    for action in sort_actions(valid_actions):
        _apply_action(game, action, context)

    eliminated = _resolve_attacks(game, context)

    return ResolutionResult(
        success=True,
        context=context,
        eliminated_player_ids=tuple(eliminated),
    )


def _apply_action(
    game: GameState,
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Apply one action to the temporary night context."""

    if action.target_id is not None:
        target = game.get_player(action.target_id)

        if target is None or not target.alive:
            return

    if action.action_type == ActionType.OBSERVE:
        _apply_observe(game, action, context)

    elif action.action_type == ActionType.PROTECT:
        _apply_protect(action, context)

    elif action.action_type == ActionType.BLOCK:
        _apply_block(action, context)

    elif action.action_type == ActionType.POISON:
        _apply_poison(action, context)

    elif action.action_type == ActionType.WEAKEN:
        _apply_weaken(action, context)

    elif action.action_type == ActionType.ATTACK:
        _apply_attack(action, context)

    elif action.action_type == ActionType.SPECIAL:
        context.results.append(
            f"special_action:{action.actor_id}"
        )


def _apply_observe(
    game: GameState,
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    target = game.get_player(action.target_id)

    if target is None:
        return

    context.observations.setdefault(
        action.actor_id,
        [],
    ).append(target.user_id)


def _apply_protect(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    context.protected_players.add(action.target_id)


def _apply_block(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    context.blocked_players.add(action.target_id)


def _apply_poison(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    context.poisoned_players.add(action.target_id)


def _apply_weaken(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    context.weakened_players.add(action.target_id)


def _apply_attack(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    if action.target_id is None:
        return

    context.attacked_players.add(action.target_id)


def _resolve_attacks(
    game: GameState,
    context: ResolutionContext,
) -> list[int]:
    """Resolve ordinary attacks against protected players."""

    eliminated: list[int] = []

    for player_id in context.attacked_players:
        player = game.get_player(player_id)

        if player is None or not player.alive:
            continue

        if player_id in context.protected_players:
            context.results.append(
                f"attack_blocked:{player_id}"
            )
            continue

        player.alive = False
        eliminated.append(player_id)

        context.results.append(
            f"player_eliminated:{player_id}"
        )

    return eliminated
