
from __future__ import annotations

import secrets
from collections import Counter

from game_state import GamePhase, GameState
from roles import ROLES, Team, Role, validate_role_catalog


MIN_PLAYERS = 7
MAX_PLAYERS = 50


class RoleAssignmentError(Exception):
    """Rol taqsimlashdagi xato."""


def get_team_distribution(player_count: int) -> dict[Team, int]:
    """O'yinchilar soniga mos jamoa tarkibini hisoblaydi."""
    if not MIN_PLAYERS <= player_count <= MAX_PLAYERS:
        raise RoleAssignmentError(
            f"O'yinchilar soni {MIN_PLAYERS}–{MAX_PLAYERS} oralig'ida bo'lishi kerak."
        )

    independent_count = min(4, max(1, player_count // 8))
    soya_count = max(2, round(player_count * 0.22))
    isyon_count = max(2, round(player_count * 0.20))
    kron_count = player_count - independent_count - soya_count - isyon_count

    if kron_count < 1:
        raise RoleAssignmentError("Jamoalar tarkibini hisoblab bo'lmadi.")

    return {
        Team.KRON: kron_count,
        Team.SOYA: soya_count,
        Team.ISYON: isyon_count,
        Team.MUSTAQIL: independent_count,
    }


def _choose_team_roles(team: Team, count: int) -> list[Role]:
    """Jamoaga mos, takrorlanmaydigan rollarni tanlaydi."""
    pool = [role for role in ROLES.values() if role.team == team]

    if count > len(pool):
        raise RoleAssignmentError(
            f"{team.value} jamoasiga {count} ta rol kerak, "
            f"ammo katalogda {len(pool)} ta rol mavjud."
        )

    rng = secrets.SystemRandom()
    rng.shuffle(pool)

    leader_ids = {
        Team.KRON: "shoh",
        Team.SOYA: "soya_hukmdori",
        Team.ISYON: "isyon_boshligi",
        Team.MUSTAQIL: None,
    }
    leader_id = leader_ids[team]

    selected: list[Role] = []

    if leader_id and count > 0:
        leader = ROLES[leader_id]
        selected.append(leader)
        pool.remove(leader)

    remaining = count - len(selected)
    selected.extend(pool[:remaining])
    rng.shuffle(selected)

    return selected


def assign_roles(game: GameState) -> dict[int, Role]:
    """
    Har bir o'yinchiga o'z jamoasiga tegishli rol beradi.

    Faqat LOBBY bosqichida ishlaydi.
    Barcha tekshiruvlar muvaffaqiyatli o'tgach, rollar biriktiriladi.
    """
    validate_role_catalog()

    if game.phase != GamePhase.LOBBY:
        raise RoleAssignmentError(
            "Rollar faqat LOBBY bosqichida taqsimlanadi."
        )

    player_count = game.player_count
    if not MIN_PLAYERS <= player_count <= MAX_PLAYERS:
        raise RoleAssignmentError(
            f"O'yinni boshlash uchun {MIN_PLAYERS}–{MAX_PLAYERS} "
            "nafar o'yinchi kerak."
        )

    distribution = get_team_distribution(player_count)
    players = list(game.players.values())
    rng = secrets.SystemRandom()
    rng.shuffle(players)

    # Avval barcha rollarni jamoalar kesimida tayyorlaymiz.
    roles_by_team: dict[Team, list[Role]] = {
        team: _choose_team_roles(team, count)
        for team, count in distribution.items()
    }

    # Har bir jamoaga alohida o'yinchilar va rollar ajratiladi.
    assignments: list[tuple[int, str]] = []
    player_index = 0

    for team, count in distribution.items():
        team_players = players[player_index:player_index + count]
        player_index += count

        team_roles = roles_by_team[team]
        rng.shuffle(team_roles)

        if len(team_players) != len(team_roles):
            raise RoleAssignmentError(
                f"{team.value} jamoasida o'yinchi va rol soni mos emas."
            )

        for player, role in zip(team_players, team_roles):
            if role.team != team:
                raise RoleAssignmentError(
                    f"{role.id} roli noto'g'ri jamoaga ajratilmoqda."
                )
            assignments.append((player.user_id, role.id))

    if len(assignments) != player_count:
        raise RoleAssignmentError("Barcha o'yinchilarga rol ajratilmadi.")

    assigned_ids = [user_id for user_id, _ in assignments]
    if len(assigned_ids) != len(set(assigned_ids)):
        raise RoleAssignmentError("Bir o'yinchiga bir nechta rol ajratildi.")

    # Tekshiruvlardan keyingina haqiqiy o'yinchi holatini o'zgartiramiz.
    for user_id, role_id in assignments:
        game.players[user_id].assign_role(role_id)

    actual_teams = Counter(
        player.team for player in game.players.values()
    )

    for team, expected_count in distribution.items():
        if actual_teams[team] != expected_count:
            raise RoleAssignmentError(
                f"{team.value}: kutilgan {expected_count}, "
                f"amalda {actual_teams[team]}."
            )

    game.metadata["role_distribution"] = {
        team.value: count for team, count in distribution.items()
    }
    game.metadata["roles_assigned"] = True

    return {
        player.user_id: player.role
        for player in game.players.values()
        if player.role is not None
    }


def get_role_distribution(game: GameState) -> dict[str, int]:
    """Taqsimlangan jamoalar sonini qaytaradi."""
    counts: Counter[str] = Counter()

    for player in game.players.values():
        if player.team is not None:
            counts[player.team.value] += 1

    return dict(counts)


def clear_roles(game: GameState) -> None:
    """Lobbyda rollarni qayta taqsimlash uchun tozalaydi."""
    if game.phase != GamePhase.LOBBY:
        raise RoleAssignmentError(
            "Rollarni faqat LOBBY bosqichida tozalash mumkin."
        )

    for player in game.players.values():
        player.role_id = None
        player.team = None
        player.ability_uses.clear()
        player.ability_data.clear()

    game.metadata.pop("role_distribution", None)
    game.metadata.pop("roles_assigned", None)
    
