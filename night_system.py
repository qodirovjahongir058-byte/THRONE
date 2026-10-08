from __future__ import annotations

from dataclasses import dataclass

from game_actions import ActionType, GameAction, create_action
from game_engine import GameState
from game_state import GamePhase
from role_engine import build_role_runtime_info, can_use_action


@dataclass(frozen=True, slots=True)
class NightActionResult:
    """Result of submitting a night action."""

    success: bool
    message: str
    action: GameAction | None = None


class NightSystem:
    """Manage player actions during the night."""

    def get_available_actions(
        self,
        game: GameState,
        player_id: int,
    ) -> list[ActionType]:
        """Return actions available to a player during the night."""

        if game.phase != GamePhase.NIGHT:
            return []

        player = game.get_player(player_id)

        if player is None or not player.alive:
            return []

        runtime_info = build_role_runtime_info(player)

        if runtime_info is None:
            return []

        actions: list[ActionType] = []

        for rule in runtime_info.action_rules:
            if rule.action_type not in actions:
                actions.append(rule.action_type)

        return actions

    def can_act(
        self,
        game: GameState,
        player_id: int,
        action_type: ActionType,
    ) -> bool:
        """Check whether a player can use an action now."""

        if game.phase != GamePhase.NIGHT:
            return False

        player = game.get_player(player_id)

        if player is None:
            return False

        if not player.alive:
            return False

        if player.has_acted:
            return False

        return can_use_action(
            game=game,
            actor_id=player_id,
            action_type=action_type,
        )

    def submit_action(
        self,
        game: GameState,
        player_id: int,
        action_type: ActionType,
        target_id: int | None = None,
        secondary_target_id: int | None = None,
    ) -> NightActionResult:
        """Validate and submit one player's night action."""

        if game.phase != GamePhase.NIGHT:
            return NightActionResult(
                success=False,
                message="night_not_active",
            )

        player = game.get_player(player_id)

        if player is None:
            return NightActionResult(
                success=False,
                message="player_not_found",
            )

        if not player.alive:
            return NightActionResult(
                success=False,
                message="player_not_alive",
            )

        if player.has_acted:
            return NightActionResult(
                success=False,
                message="already_acted",
            )

        if not can_use_action(
            game=game,
            actor_id=player_id,
            action_type=action_type,
        ):
            return NightActionResult(
                success=False,
                message="action_not_allowed",
            )

        target_required = self._action_requires_target(
            game=game,
            player_id=player_id,
            action_type=action_type,
        )

        if target_required and target_id is None:
            return NightActionResult(
                success=False,
                message="target_required",
            )

        if target_id is not None:
            target = game.get_player(target_id)

            if target is None:
                return NightActionResult(
                    success=False,
                    message="target_not_found",
                )

            if not target.alive:
                return NightActionResult(
                    success=False,
                    message="target_not_alive",
                )

            if target_id == player_id:
                return NightActionResult(
                    success=False,
                    message="cannot_target_self",
                )

        if secondary_target_id is not None:
            secondary_target = game.get_player(
                secondary_target_id
            )

            if secondary_target is None:
                return NightActionResult(
                    success=False,
                    message="secondary_target_not_found",
                )

            if not secondary_target.alive:
                return NightActionResult(
                    success=False,
                    message="secondary_target_not_alive",
                )

        action = create_action(
            actor_id=player_id,
            action_type=action_type,
            target_id=target_id,
            secondary_target_id=secondary_target_id,
        )

        player.has_acted = True
        player.metadata["night_action"] = action_type.value
        player.metadata["night_target"] = target_id

        return NightActionResult(
            success=True,
            message="action_submitted",
            action=action,
        )

    def _action_requires_target(
        self,
        game: GameState,
        player_id: int,
        action_type: ActionType,
    ) -> bool:
        """Return whether an action requires a target."""

        runtime_info = build_role_runtime_info(
            game.get_player(player_id)
        ) if game.get_player(player_id) else None

        if runtime_info is None:
            return False

        for rule in runtime_info.action_rules:
            if rule.action_type == action_type:
                return rule.requires_target

        return False

    def get_valid_targets(
        self,
        game: GameState,
        player_id: int,
        action_type: ActionType,
    ) -> list[int]:
        """Return valid living targets for an action."""

        if not self.can_act(
            game=game,
            player_id=player_id,
            action_type=action_type,
        ):
            return []

        result: list[int] = []

        for player in game.alive_players():
            if player.user_id == player_id:
                continue

            result.append(player.user_id)

        return result


night_system = NightSystem()
