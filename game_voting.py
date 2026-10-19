
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game_state import GamePhase, GameState


class VotingError(Exception):
    """Ovoz berish bilan bog'liq xato."""


@dataclass(slots=True)
class VotingResult:
    completed: bool
    eliminated_player_id: int | None = None
    tied_player_ids: list[int] = field(default_factory=list)
    vote_counts: dict[int, int] = field(default_factory=dict)
    total_votes: int = 0
    message: str = ""


class GameVoting:
    """THRONE o'yinida ovoz berishni boshqaradi."""

    def __init__(self, game: GameState) -> None:
        self.game = game
        self._revote_candidates: set[int] | None = None

    def cast_vote(
        self,
        voter_id: int,
        target_id: int | None,
    ) -> dict[str, Any]:
        """Ovoz beradi. target_id=None bo'lsa, ovoz bermaslikni bildiradi."""

        if self.game.phase != GamePhase.VOTING:
            raise VotingError("Hozir ovoz berish bosqichi emas.")

        voter = self.game.get_player(voter_id)

        if voter is None or not voter.is_alive:
            raise VotingError("Faqat tirik o'yinchi ovoz bera oladi.")

        if target_id is not None:
            target = self.game.get_player(target_id)

            if target is None or not target.is_alive:
                raise VotingError("Tanlangan o'yinchi tirik emas.")

            if voter_id == target_id:
                raise VotingError("O'zingizga ovoz bera olmaysiz.")

            if (
                self._revote_candidates is not None
                and target_id not in self._revote_candidates
            ):
                raise VotingError(
                    "Qayta ovoz berishda faqat durangdagi "
                    "o'yinchilarga ovoz berish mumkin."
                )

        # Bitta o'yinchining oxirgi ovozi hisobga olinadi.
        voter.voted_for = target_id

        if target_id is None:
            self.game.votes.pop(voter_id, None)
        else:
            self.game.votes[voter_id] = target_id

        return {
            "success": True,
            "voter_id": voter_id,
            "target_id": target_id,
            "vote_count": len(self.game.votes),
        }

    def remove_vote(self, voter_id: int) -> bool:
        """O'yinchining ovozini bekor qiladi."""

        if self.game.phase != GamePhase.VOTING:
            raise VotingError("Hozir ovoz berish bosqichi emas.")

        voter = self.game.get_player(voter_id)

        if voter is None or not voter.is_alive:
            raise VotingError("Ovoz beruvchi tirik o'yinchi emas.")

        self.game.votes.pop(voter_id, None)
        voter.voted_for = None

        return True

    def get_vote_counts(self) -> dict[int, int]:
        """Har bir o'yinchi olgan ovozlar sonini qaytaradi."""

        counts: dict[int, int] = {}

        for voter_id, target_id in self.game.votes.items():
            voter = self.game.get_player(voter_id)
            target = self.game.get_player(target_id)

            if voter is None or not voter.is_alive:
                continue

            if target is None or not target.is_alive:
                continue

            counts[target_id] = counts.get(target_id, 0) + 1

        return counts

    def resolve_voting(self) -> VotingResult:
        """Ovoz berishni yakunlaydi va natijani hisoblaydi."""

        if self.game.phase != GamePhase.VOTING:
            raise VotingError("Ovoz berish bosqichi tugamagan.")

        counts = self.get_vote_counts()
        total_votes = sum(counts.values())

        if not counts:
            self._revote_candidates = None
            return VotingResult(
                completed=True,
                vote_counts={},
                total_votes=0,
                message="no_votes",
            )

        highest = max(counts.values())
        leaders = sorted(
            player_id
            for player_id, count in counts.items()
            if count == highest
        )

        if len(leaders) > 1:
            # Durang: faqat teng ovoz olganlar orasida qayta ovoz berish.
            self._revote_candidates = set(leaders)
            self.game.revote_count += 1

            return VotingResult(
                completed=False,
                tied_player_ids=leaders,
                vote_counts=counts,
                total_votes=total_votes,
                message="tie_revote_required",
            )

        eliminated_id = leaders[0]
        self._revote_candidates = None

        return VotingResult(
            completed=True,
            eliminated_player_id=eliminated_id,
            vote_counts=counts,
            total_votes=total_votes,
            message="voting_winner_decided",
        )

    def eliminate_voted_player(self) -> VotingResult:
        """Ovoz natijasiga ko'ra o'yinchini o'yindan chiqaradi."""

        result = self.resolve_voting()

        if not result.completed:
            return result

        if result.eliminated_player_id is None:
            return result

        player = self.game.get_player(result.eliminated_player_id)

        if player is None or not player.is_alive:
            raise VotingError(
                "Ovoz natijasidagi o'yinchi endi tirik emas."
            )

        player.eliminate(reason="voted_out")

        return result

    def start_revote(self) -> None:
        """Durangdan keyingi qayta ovoz berishni tayyorlaydi."""

        if self._revote_candidates is None:
            raise VotingError("Qayta ovoz berish uchun durang yo'q.")

        if self.game.phase != GamePhase.VOTING:
            raise VotingError("Qayta ovoz berish VOTING bosqichida bo'lishi kerak.")

        self.game.votes.clear()

        for player in self.game.players.values():
            player.reset_vote()

    def clear(self) -> None:
        """Ovoz berish ma'lumotlarini tozalaydi."""

        self.game.votes.clear()
        self._revote_candidates = None

        for player in self.game.players.values():
            player.reset_vote()


def create_voting(game: GameState) -> GameVoting:
    """Ovoz berish boshqaruv obyektini yaratadi."""

    return GameVoting(game)
    
