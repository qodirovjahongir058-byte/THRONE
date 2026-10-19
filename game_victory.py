
from dataclasses import dataclass

from game_engine import Game, GamePhase
from roles import Team, get_role


@dataclass(frozen=True, slots=True)
class VictoryResult:
    finished: bool
    winner: str | None
    message: str


class GameVictory:
    """THRONE o'yinidagi jamoaviy g'alaba shartlari."""

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
            Team.KRON: 0,
            Team.SOYA: 0,
            Team.ISYON: 0,
            Team.MUSTAQIL: 0,
        }

        for player in alive_players:
            role = get_role(player.role_id or "")

            if role is not None and role.team in team_counts:
                team_counts[role.team] += 1

        kron = team_counts[Team.KRON]
        soya = team_counts[Team.SOYA]
        isyon = team_counts[Team.ISYON]
        mustaqil = team_counts[Team.MUSTAQIL]

        # KRON: SOYA va ISYON tahdidlari qolmaganida.
        if kron > 0 and soya == 0 and isyon == 0:
            return GameVictory._finish(
                game,
                Team.KRON.value,
                "KRON jamoasi g'alaba qozondi!",
            )

        # SOYA: qolgan jamoalardan tirik o'yinchilar soni
        # bo'yicha ustunlikka erishganda.
        if soya > 0 and soya >= kron + isyon + mustaqil:
            return GameVictory._finish(
                game,
                Team.SOYA.value,
                "SOYA jamoasi g'alaba qozondi!",
            )

        # ISYON: qolgan jamoalardan tirik o'yinchilar soni
        # bo'yicha ustunlikka erishganda.
        if isyon > 0 and isyon >= kron + soya + mustaqil:
            return GameVictory._finish(
                game,
                Team.ISYON.value,
                "ISYON jamoasi g'alaba qozondi!",
            )

        # MUSTAQIL rollarning shaxsiy maqsadlari alohida
        # tekshirilishi kerak. Ularni faqat tirik qolganiga
        # qarab g'olib deb e'lon qilmaymiz.
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
    
