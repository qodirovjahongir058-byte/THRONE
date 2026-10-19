import random
from dataclasses import dataclass

from roles import ROLES, Role, Team
from game_engine import Game, GamePhase


@dataclass(frozen=True, slots=True)
class RoleAssignmentResult:
    success: bool
    message: str
    assignments: dict[int, Role]


# O'yinchilar soniga qarab jamoalar taqsimoti:
# KRON, SOYA, ISYON, MUSTAQIL
TEAM_DISTRIBUTION: dict[int, dict[str, int]] = {
    7:  {"KRON": 3, "SOYA": 2, "ISYON": 1, "MUSTAQIL": 1},
    8:  {"KRON": 3, "SOYA": 2, "ISYON": 2, "MUSTAQIL": 1},
    9:  {"KRON": 4, "SOYA": 2, "ISYON": 2, "MUSTAQIL": 1},
    10: {"KRON": 4, "SOYA": 3, "ISYON": 2, "MUSTAQIL": 1},
    11: {"KRON": 4, "SOYA": 3, "ISYON": 3, "MUSTAQIL": 1},
    12: {"KRON": 5, "SOYA": 3, "ISYON": 3, "MUSTAQIL": 1},
    13: {"KRON": 5, "SOYA": 3, "ISYON": 3, "MUSTAQIL": 2},
    14: {"KRON": 5, "SOYA": 4, "ISYON": 3, "MUSTAQIL": 2},
    15: {"KRON": 6, "SOYA": 4, "ISYON": 3, "MUSTAQIL": 2},
    16: {"KRON": 6, "SOYA": 4, "ISYON": 4, "MUSTAQIL": 2},
    17: {"KRON": 6, "SOYA": 5, "ISYON": 4, "MUSTAQIL": 2},
    18: {"KRON": 7, "SOYA": 5, "ISYON": 4, "MUSTAQIL": 2},
    19: {"KRON": 7, "SOYA": 5, "ISYON": 5, "MUSTAQIL": 2},
    20: {"KRON": 7, "SOYA": 6, "ISYON": 5, "MUSTAQIL": 2},
    21: {"KRON": 7, "SOYA": 6, "ISYON": 5, "MUSTAQIL": 3},
    22: {"KRON": 8, "SOYA": 6, "ISYON": 5, "MUSTAQIL": 3},
    23: {"KRON": 8, "SOYA": 6, "ISYON": 6, "MUSTAQIL": 3},
    24: {"KRON": 8, "SOYA": 7, "ISYON": 6, "MUSTAQIL": 3},
    25: {"KRON": 8, "SOYA": 7, "ISYON": 7, "MUSTAQIL": 3},
    26: {"KRON": 9, "SOYA": 7, "ISYON": 7, "MUSTAQIL": 3},
    27: {"KRON": 9, "SOYA": 8, "ISYON": 7, "MUSTAQIL": 3},
    28: {"KRON": 9, "SOYA": 8, "ISYON": 8, "MUSTAQIL": 3},
    29: {"KRON": 10, "SOYA": 8, "ISYON": 8, "MUSTAQIL": 3},
    30: {"KRON": 10, "SOYA": 9, "ISYON": 8, "MUSTAQIL": 3},
    31: {"KRON": 10, "SOYA": 9, "ISYON": 9, "MUSTAQIL": 3},
    32: {"KRON": 10, "SOYA": 9, "ISYON": 9, "MUSTAQIL": 4},
    33: {"KRON": 11, "SOYA": 9, "ISYON": 9, "MUSTAQIL": 4},
    34: {"KRON": 11, "SOYA": 10, "ISYON": 9, "MUSTAQIL": 4},
    35: {"KRON": 11, "SOYA": 10, "ISYON": 10, "MUSTAQIL": 4},
    36: {"KRON": 12, "SOYA": 10, "ISYON": 10, "MUSTAQIL": 4},
}


class RoleAssignment:
    """THRONE o'yinida rollarni adolatli tasodifiy taqsimlaydi."""

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
                role
                for role in ROLES.values()
                if role.team == team
            ]

            if count > len(team_roles):
                raise ValueError(
                    f"{team_name} uchun {count} ta rol kerak, "
                    f"lekin faqat {len(team_roles)} ta rol mavjud."
                )

            pool.extend(random.sample(team_roles, count))

        if len(pool) != player_count:
            raise ValueError(
                "Taqsimlangan rollar soni o'yinchilar soniga mos emas."
            )

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

        assignments = dict(zip(player_ids, role_pool))

        # Barcha o'yinchilar uchun rol mavjudligini oldindan tekshiramiz.
        if len(assignments) != player_count:
            return RoleAssignmentResult(
                False,
                "Rollarni taqsimlashda xatolik yuz berdi.",
                {},
            )

        # Tekshiruvdan so'ng rollarni o'yinchilarga biriktiramiz.
        for user_id, role in assignments.items():
            if not game.assign_role(user_id, role.id):
                return RoleAssignmentResult(
                    False,
                    "Rolni o'yinchiga biriktirib bo'lmadi.",
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
    """Asosiy o'yin kodidan chaqirish uchun funksiya."""
    return RoleAssignment.assign_roles(game)
