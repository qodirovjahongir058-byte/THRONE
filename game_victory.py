from dataclasses import dataclass, field

from game_engine import Game, GamePhase


@dataclass
class VotingResult:
    success: bool
    message: str
    eliminated_id: int | None = None
    vote_counts: dict[int, int] = field(default_factory=dict)
    tied_ids: list[int] = field(default_factory=list)
    revote_required: bool = False


class GameVoting:
    """THRONE o'yinidagi ovoz berish jarayonini boshqaradi."""

    def __init__(self) -> None:
        self.revote_used = False
        self.revote_candidates: set[int] = set()

    def start_voting(self, game: Game) -> tuple[bool, str]:
        if game.phase != GamePhase.DISCUSSION:
            return False, "Avval muhokama bosqichi yakunlanishi kerak."

        success, message = game.begin_voting()

        if success:
            self.revote_used = False
            self.revote_candidates.clear()

        return success, message

    def cast_vote(
        self,
        game: Game,
        voter_id: int,
        target_id: int,
    ) -> tuple[bool, str]:
        if game.phase != GamePhase.VOTING:
            return False, "Hozir ovoz berish bosqichi emas."

        if voter_id not in game.players:
            return False, "Ovoz beruvchi o'yinchi topilmadi."

        voter = game.players[voter_id]
        target = game.players.get(target_id)

        if not voter.alive:
            return False, "O'yindan chiqqan o'yinchi ovoz bera olmaydi."

        if target is None or not target.alive:
            return False, "Tanlangan nishon tirik emas yoki topilmadi."

        if voter_id == target_id:
            return False, "O'zingizga ovoz bera olmaysiz."

        if self.revote_used and target_id not in self.revote_candidates:
            return False, "Qayta ovozda faqat durangdagi nomzodlar tanlanadi."

        return game.cast_vote(voter_id, target_id)

    def resolve_voting(self, game: Game) -> VotingResult:
        if game.phase != GamePhase.VOTING:
            return VotingResult(
                False,
                "Hozir ovoz berish bosqichi emas.",
            )

        vote_counts = game.get_vote_results()

        if not vote_counts:
            return VotingResult(
                True,
                "Hech kim ovoz olmadi. Hech kim chiqarilmadi.",
            )

        highest = max(vote_counts.values())
        tied_ids = sorted(
            player_id
            for player_id, count in vote_counts.items()
            if count == highest
        )

        if len(tied_ids) > 1:
            if not self.revote_used:
                self.revote_used = True
                self.revote_candidates = set(tied_ids)
                game.votes.clear()

                for player in game.players.values():
                    player.vote_target = None

                return VotingResult(
                    True,
                    "Ovozlar teng. Durangdagi nomzodlar o'rtasida "
                    "qayta ovoz beriladi.",
                    vote_counts=vote_counts,
                    tied_ids=tied_ids,
                    revote_required=True,
                )

            return VotingResult(
                True,
                "Qayta ovozda ham durang. Hech kim chiqarilmadi.",
                vote_counts=vote_counts,
                tied_ids=tied_ids,
            )

        eliminated_id = tied_ids[0]
        player = game.players.get(eliminated_id)

        if player is None or not player.alive:
            return VotingResult(
                False,
                "Ovoz natijasidagi o'yinchi topilmadi yoki tirik emas.",
                vote_counts=vote_counts,
            )

        success, message = game.eliminate_player(
            eliminated_id,
            reason="Ovoz berish natijasida",
        )

        if not success:
            return VotingResult(
                False,
                message,
                vote_counts=vote_counts,
            )

        return VotingResult(
            True,
            f"{player.name} ovoz berish natijasida chiqarildi.",
            eliminated_id=eliminated_id,
            vote_counts=vote_counts,
        )


def resolve_voting(game: Game) -> VotingResult:
    """Ovoz natijasini bir marta hisoblash uchun yordamchi funksiya."""
    voting = GameVoting()
    return voting.resolve_voting(game)
