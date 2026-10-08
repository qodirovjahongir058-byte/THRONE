from __future__ import annotations

import random

from game_engine import GameState
from roles import get_all_roles


def assign_roles(game: GameState) -> None:
    """
    Randomly assign one unique role to every player.

    The current THRONE roster contains exactly 36 unique roles.
    The number of players must therefore be between 7 and 36.
    """
    players = list(game.players.values())
    roles = get_all_roles()

    if not players:
        raise ValueError("Cannot assign roles to an empty game.")

    if len(players) > len(roles):
        raise ValueError(
            "There are not enough unique roles for all players."
        )

    shuffled_roles = list(roles)
    random.shuffle(shuffled_roles)

    for player, role in zip(players, shuffled_roles):
        player.role_key = role.key

    game.metadata["roles_assigned"] = True


def roles_are_assigned(game: GameState) -> bool:
    """Return True when every player has a role."""

    if not game.players:
        return False

    return all(
        player.role_key is not None
        for player in game.players.values()
    )


def get_player_role_key(
    game: GameState,
    user_id: int,
) -> str | None:
    """Return the assigned role key of a player."""

    player = game.get_player(user_id)

    if player is None:
        return None

    return player.role_key
