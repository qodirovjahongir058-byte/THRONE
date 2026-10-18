from dataclasses import dataclass

from game_engine import Game, GamePhase
from roles import Team, get_role


@dataclass(frozen=True, slots=True)
class VictoryResult:
    finished: bool
    winner: str | None
    message: str


class GameVictory:
    """THRONE o'yinidagi g'alaba shartlarini tekshiradi."""

    @staticmethod
    def check_victory(game: Game) -> VictoryResult:
        if game.phase in (GamePhase.FINISHED, GamePhase.STOPPED):
            return VictoryResult(
                True,
                game.winner,
                "O'yin allaqachon yakunlangan.",
            )

        alive_players = game.alive_players

        if not alive_players:
            return GameVictory._finish(
                game,
                "DURANG",
                "Barcha o'yinchilar o'yindan chiqdi. Natija — durang.",
            )

        team_counts = {
            team: 0
            for team in Team
        }

        for player in alive_players:
            role = get_role(player.role_id or "")
            if role is not None:
                team_counts[role.team] += 1

        kron = team_counts[Team.KRON]
        soya = team_counts[Team.SOYA]
        yakka = team_counts[Team.YAKKA]
        legion = team_counts[Team.LEGION]

        # Mustaqil g'alaba shartlari keyingi maxsus maqsadlar
        # tizimi orqali yanada aniqlashtiriladi.
        if soya == 0 and legion == 0 and yakka == 0:
            if kron > 0:
                return GameVictory._finish(
                    game,
                    Team.KRON.value,
                    "KRON jamoasi g'alaba qozondi!",
                )

        if kron == 0 and legion == 0 and yakka == 0 and soya > 0:
            return GameVictory._finish(
                game,
                Team.SOYA.value,
                "SOYA jamoasi g'alaba qozondi!",
            )

        # Soya tirik qolgan raqiblar soniga teng yoki ko'p bo'lsa,
        # boshqa jamoalar uni to'xtata olmasligi mumkin.
        if soya > 0 and soya >= kron + legion + yakka:
            return GameVictory._finish(
                game,
                Team.SOYA.value,
                "SOYA jamoasi ustunlikni qo'lga kiritdi!",
            )

        # KRON qolmagan va SOYA yo'q bo'lsa, LEGION yakuniy
        # g'alabaga erishadi.
        if kron == 0 and soya == 0 and yakka == 0 and legion > 0:
            return GameVictory._finish(
                game,
                Team.LEGION.value,
                "LEGION jamoasi g'alaba qozondi!",
            )

        return VictoryResult(
            False,
            None,
            "O'yin davom etmoqda.",
        )

    @staticmethod
    def _finish(
        game: Game,
        winner: str,
        message: str,
    ) -> VictoryResult:
        game.finish(winner)
        return VictoryResult(
            True,
            winner,
            message,
        )


def check_victory(game: Game) -> VictoryResult:
    """G'alaba shartlarini tekshiruvchi tashqi funksiya."""
    return GameVictory.check_victory(game)
