import random
from dataclasses import dataclass

from roles import ROLES, Role, Team
from game_engine import Game, GamePhase


@dataclass(frozen=True, slots=True)
class RoleAssignmentResult:
    success: bool
    message: str
    assignments: dict[int, Role]


# O'yinchi soniga qarab jamoalar taqsimoti.
# Har bir o'yinchiga bittadan rol beriladi.
TEAM_DISTRIBUTION = {
    7:  {"KRON": 3, "SOYA": 2, "YAKKA": 1, "LEGION": 1},
    8:  {"KRON": 3, "SOYA": 2, "YAKKA": 1, "LEGION": 2},
    9:  {"KRON": 4, "SOYA": 2, "YAKKA": 1, "LEGION": 2},
    10: {"KRON": 4, "SOYA": 3, "YAKKA": 1, "LEGION": 2},
    11: {"KRON": 4, "SOYA": 3, "YAKKA": 2, "LEGION": 2},
    12: {"KRON": 5, "SOYA": 3, "YAKKA": 2, "LEGION": 2},
    13: {"KRON": 5, "SOYA": 3, "YAKKA": 2, "LEGION": 3},
    14: {"KRON": 5, "SOYA": 4, "YAKKA": 2, "LEGION": 3},
    15: {"KRON": 6, "SOYA": 4, "YAKKA": 2, "LEGION": 3},
    16: {"KRON": 6, "SOYA": 4, "YAKKA": 3, "LEGION": 3},
    17: {"KRON": 6, "SOYA": 5, "YAKKA": 3, "LEGION": 3},
    18: {"KRON": 7, "SOYA": 5, "YAKKA": 3, "LEGION": 3},
    19: {"KRON": 7, "SOYA": 5, "YAKKA": 3, "LEGION": 4},
    20: {"KRON": 7, "SOYA": 6, "YAKKA": 3, "LEGION": 4},
    21: {"KRON": 8, "SOYA": 6, "YAKKA": 3, "LEGION": 4},
    22: {"KRON": 8, "SOYA": 6, "YAKKA": 4, "LEGION": 4},
    23: {"KRON": 8, "SOYA": 7, "YAKKA": 4, "LEGION": 4},
    24: {"KRON": 9, "SOYA": 7, "YAKKA": 4, "LEGION": 4},
    25: {"KRON": 9, "SOYA": 7, "YAKKA": 4, "LEGION": 5},
    26: {"KRON": 9, "SOYA": 8, "YAKKA": 4, "LEGION": 5},
    27: {"KRON": 10, "SOYA": 8, "YAKKA": 4, "LEGION": 5},
    28: {"KRON": 10, "SOYA": 8, "YAKKA": 5, "LEGION": 5},
    29: {"KRON": 10, "SOYA": 9, "YAKKA": 5, "LEGION": 5},
    30: {"KRON": 11, "SOYA": 9, "YAKKA": 5, "LEGION": 5},
    31: {"KRON": 11, "SOYA": 9, "YAKKA": 5, "LEGION": 6},
    32: {"KRON": 11, "SOYA": 10, "YAKKA": 5, "LEGION": 6},
    33: {"KRON": 12, "SOYA": 10, "YAKKA": 5, "LEGION": 6},
    34: {"KRON": 12, "SOYA": 10, "YAKKA": 6, "LEGION": 6},
    35: {"KRON": 12, "SOYA": 10, "YAKKA": 6, "LEGION": 7},
    36: {"KRON": 12, "SOYA": 10, "YAKKA": 7, "LEGION": 7},
}


class RoleAssignment:
    """THRONE o'yini uchun rollarni taqsimlash tizimi."""

    @staticmethod
    def _build_role_pool(player_count: int) -> list[Role]:
        distribution = TEAM_DISTRIBUTION.get(player_count)

        if distribution is None:
            raise ValueError(
                "O'yinchilar soni 7 dan 36 gacha bo'lishi kerak."
            )

        pool: list[Role] = []

        for team_name, count in distribution.items():
            team = Team(team_name)
            team_roles = [
                role for role in ROLES.values()
                if role.team == team
            ]

            if count > len(team_roles):
                raise ValueError(
                    f"{team_name} jamoasida {count} ta rol kerak, "
                    f"ammo faqat {len(team_roles)} ta rol mavjud."
                )

            pool.extend(random.sample(team_roles, count))

        if len(pool) != player_count:
            raise ValueError("Rollar soni o'yinchilar soniga teng emas.")

        return pool

    @classmethod
    def assign_roles(cls, game: Game) -> RoleAssignmentResult:
        if game.phase != GamePhase.ROLE_REVEAL:
            return RoleAssignmentResult(
                False,
                "Avval o'yinni boshlash kerak.",
                {},
            )

        player_count = len(game.players)

        if not Game.MIN_PLAYERS <= player_count <= Game.MAX_PLAYERS:
            return RoleAssignmentResult(
                False,
                "O'yinchilar soni 7 dan 36 gacha bo'lishi kerak.",
                {},
            )

        try:
            role_pool = cls._build_role_pool(player_count)
        except ValueError as error:
            return RoleAssignmentResult(False, str(error), {})

        player_ids = list(game.players.keys())
        random.shuffle(player_ids)
        random.shuffle(role_pool)

        assignments: dict[int, Role] = {}

        # Avval tekshirib, keyin rollarni birgalikda biriktiramiz.
        for user_id, role in zip(player_ids, role_pool):
            assignments[user_id] = role

        for user_id, role in assignments.items():
            if not game.assign_role(user_id, role.id):
                return RoleAssignmentResult(
                    False,
                    "Rolni biriktirishda xatolik yuz berdi.",
                    {},
                )

        game.history.append(
            f"{player_count} nafar o'yinchiga rollar taqsimlandi."
        )

        return RoleAssignmentResult(
            True,
            "Barcha rollar muvaffaqiyatli taqsimlandi.",
            assignments,
        )


def assign_roles(game: Game) -> RoleAssignmentResult:
    """Rollarni taqsimlash uchun qulay tashqi funksiya."""
    return RoleAssignment.assign_roles(game)
