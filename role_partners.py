from __future__ import annotations

from game_engine import GameState
from roles import RoleSide, get_role


def get_known_partners(
    game: GameState,
    user_id: int,
) -> list[str]:
    """
    Return the players who should be known as partners.

    Currently, SOYA players know other living SOYA players.
    KRON, YAKKA and LEGION players do not receive a team list
    through this basic system.
    """

    player = game.get_player(user_id)

    if player is None or not player.role_key:
        return []

    role = get_role(player.role_key)

    if role is None:
        return []

    if role.side != RoleSide.SOYA:
        return []

    partners: list[str] = []

    for other_player in game.players.values():
        if other_player.user_id == user_id:
            continue

        if not other_player.alive:
            continue

        if not other_player.role_key:
            continue

        other_role = get_role(other_player.role_key)

        if other_role is None:
            continue

        if other_role.side != RoleSide.SOYA:
            continue

        partners.append(other_player.display_name)

    return partners
