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


def sort_actions(
    actions: list[GameAction],
) -> list[GameAction]:
    """Return actions in the defined resolution order."""

    return sorted(
        actions,
        key=lambda action: ACTION_PRIORITY[action.action_type],
    )


def resolve_night(
    game: GameState,
    actions: list[GameAction],
) -> ResolutionResult:
    """
    Resolve all submitted actions for one night.

    Actions are processed in the defined order so that
    blocking can affect actions that have not yet been resolved.
    """

    context = ResolutionContext()

    valid_actions = _get_valid_actions(
        game=game,
        actions=actions,
    )

    for action in sort_actions(valid_actions):
        actor = game.get_player(action.actor_id)

        if actor is None or not actor.alive:
            continue

        if action.actor_id in context.blocked_players:
            context.results.append(
                f"action_blocked:{action.actor_id}"
            )
            continue

        _apply_action(
            game=game,
            action=action,
            context=context,
        )

    eliminated = _resolve_attacks(
        game=game,
        context=context,
    )

    return ResolutionResult(
        success=True,
        context=context,
        eliminated_player_ids=tuple(eliminated),
    )


def _get_valid_actions(
    game: GameState,
    actions: list[GameAction],
) -> list[GameAction]:
    """Filter actions submitted by valid living players."""

    valid_actions: list[GameAction] = []

    for action in actions:
        actor = game.get_player(action.actor_id)

        if actor is None:
            continue

        if not actor.alive:
            continue

        if action.target_id is not None:
            target = game.get_player(action.target_id)

            if target is None or not target.alive:
                continue

        if action.secondary_target_id is not None:
            secondary_target = game.get_player(
                action.secondary_target_id
            )

            if (
                secondary_target is None
                or not secondary_target.alive
            ):
                continue

        valid_actions.append(action)

    return valid_actions


def _apply_action(
    game: GameState,
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Apply one action to the night resolution context."""

    if action.action_type == ActionType.OBSERVE:
        _apply_observe(
            game=game,
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.PROTECT:
        _apply_protect(
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.BLOCK:
        _apply_block(
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.POISON:
        _apply_poison(
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.WEAKEN:
        _apply_weaken(
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.ATTACK:
        _apply_attack(
            action=action,
            context=context,
        )

    elif action.action_type == ActionType.SPECIAL:
        context.results.append(
            f"special_action:{action.actor_id}"
        )


def _apply_observe(
    game: GameState,
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Record an observation target."""

    if action.target_id is None:
        return

    target = game.get_player(action.target_id)

    if target is None or not target.alive:
        return

    context.observations.setdefault(
        action.actor_id,
        [],
    ).append(target.user_id)

    context.results.append(
        f"observed:{action.actor_id}:{target.user_id}"
    )


def _apply_protect(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Protect a player from ordinary attacks."""

    if action.target_id is None:
        return

    context.protected_players.add(
        action.target_id
    )

    context.results.append(
        f"protected:{action.target_id}"
    )


def _apply_block(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Block the target player's remaining night action."""

    if action.target_id is None:
        return

    context.blocked_players.add(
        action.target_id
    )

    context.results.append(
        f"blocked:{action.target_id}"
    )


def _apply_poison(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Mark a player as poisoned."""

    if action.target_id is None:
        return

    context.poisoned_players.add(
        action.target_id
    )

    context.results.append(
        f"poisoned:{action.target_id}"
    )


def _apply_weaken(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Mark a player as weakened."""

    if action.target_id is None:
        return

    context.weakened_players.add(
        action.target_id
    )

    context.results.append(
        f"weakened:{action.target_id}"
    )


def _apply_attack(
    action: GameAction,
    context: ResolutionContext,
) -> None:
    """Register an ordinary attack."""

    if action.target_id is None:
        return

    context.attacked_players.add(
        action.target_id
    )

    context.results.append(
        f"attack:{action.actor_id}:{action.target_id}"
    )


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
