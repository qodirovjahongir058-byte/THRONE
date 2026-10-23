
import random

import pytest

from roles import (
    KRON,
    SOYA,
    YAKKA,
    MAX_PLAYERS,
    MIN_PLAYERS,
    ROLES,
    assign_roles,
    get_role,
    get_roles_by_faction,
    role_summary,
)


def test_role_catalog_contains_20_roles():
    assert len(ROLES) == 20
    assert len({role.id for role in ROLES}) == 20


def test_all_three_factions_exist():
    assert get_roles_by_faction(KRON)
    assert get_roles_by_faction(SOYA)
    assert get_roles_by_faction(YAKKA)

    summary = role_summary()
    assert sum(summary.values()) == 20


def test_known_roles_exist():
    assert get_role("king") is not None
    assert get_role("prince") is not None
    assert get_role("king_guard") is not None
    assert get_role("sauron") is not None
    assert get_role("unknown_role") is None


@pytest.mark.parametrize(
    "player_count",
    [MIN_PLAYERS, 5, 10, 20, MAX_PLAYERS],
)
def test_assign_roles_gives_one_role_per_player(player_count):
    player_ids = list(range(1000, 1000 + player_count))

    assignments = assign_roles(
        player_ids,
        rng=random.Random(42),
    )

    assert len(assignments) == player_count
    assert set(assignments.keys()) == set(player_ids)

    for role in assignments.values():
        assert role in ROLES


def test_duplicate_player_ids_are_rejected():
    with pytest.raises(ValueError):
        assign_roles([1, 2, 3, 3])


@pytest.mark.parametrize("player_count", [0, 1, 2, 3, 31, 40])
def test_invalid_player_counts_are_rejected(player_count):
    player_ids = list(range(player_count))

    with pytest.raises(ValueError):
        assign_roles(player_ids)


def test_unique_roles_are_not_assigned_twice():
    player_ids = list(range(1, 31))

    assignments = assign_roles(
        player_ids,
        rng=random.Random(42),
    )

    unique_role_ids = [
        role.id
        for role in assignments.values()
        if role.unique
    ]

    assert len(unique_role_ids) == len(set(unique_role_ids))
  
