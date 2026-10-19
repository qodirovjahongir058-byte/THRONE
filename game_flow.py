
from datetime import datetime, timezone

from game_engine import Game, GamePhase
from game_resolver import GameResolver
from game_victory import GameVictory


LAST_WORDS_DURATION = 30


class GameFlow:
    """THRONE o'yin bosqichlarini boshqarish."""

    def __init__(self, game: Game):
        self.game = game
        self.last_words_player_id: int | None = None
        self.last_words_deadline: float | None = None

    def _set_phase(self, phase: GamePhase) -> None:
        self.game.phase = phase
        self.game.phase_started_at = datetime.now(timezone.utc)

    def _alive_players(self):
        return [
            player
            for player in self.game.players.values()
            if player.alive
        ]

    def _check_victory(self):
        winner = GameVictory.check_victory(self.game)

        if winner:
            self.game.finish(winner)
            self._set_phase(GamePhase.FINISHED)

        return winner

    def start_night(self) -> bool:
        if self.game.phase not in {
            GamePhase.ROLE_REVEAL,
            GamePhase.DAY,
            GamePhase.DISCUSSION,
        }:
            return False

        if self._check_victory():
            return False

        self.game.votes.clear()
        self._set_phase(GamePhase.NIGHT)
        return True

    def resolve_night(self):
        if self.game.phase != GamePhase.NIGHT:
            return None

        result = GameResolver.resolve_night(self.game)

        if not result.success:
            return result

        winner = self._check_victory()

        if winner:
            return result

        self._set_phase(GamePhase.DAY)
        return result

    def start_discussion(self) -> bool:
        if self.game.phase != GamePhase.DAY:
            return False

        if self._check_victory():
            return False

        self._set_phase(GamePhase.DISCUSSION)
        return True

    def start_voting(self) -> bool:
        if self.game.phase not in {
            GamePhase.DAY,
            GamePhase.DISCUSSION,
        }:
            return False

        if self._check_victory():
            return False

        self.game.votes.clear()

        for player in self.game.players.values():
            player.vote_target = None

        self._set_phase(GamePhase.VOTING)
        return True

    def register_vote(
        self,
        voter_id: int,
        target_id: int | None,
    ) -> tuple[bool, str]:
        if self.game.phase != GamePhase.VOTING:
            return False, "Hozir ovoz berish bosqichi emas."

        voter = self.game.players.get(voter_id)

        if voter is None or not voter.alive:
            return False, "Siz ovoz bera olmaysiz."

        if target_id == voter_id:
            return False, "O'zingizga ovoz bera olmaysiz."

        if target_id is not None:
            target = self.game.players.get(target_id)

            if target is None or not target.alive:
                return False, "Tanlangan o'yinchi faol emas."

        self.game.votes[voter_id] = target_id
        voter.vote_target = target_id

        return True, "Ovozingiz qabul qilindi."

    def resolve_voting(self) -> dict:
        if self.game.phase != GamePhase.VOTING:
            return {
                "success": False,
                "message": "Hozir ovoz berish bosqichi emas.",
                "eliminated": None,
                "tie": False,
            }

        alive_ids = {
            player.user_id
            for player in self._alive_players()
        }

        vote_counts: dict[int, int] = {}

        for voter_id, target_id in self.game.votes.items():
            if voter_id not in alive_ids:
                continue

            if target_id is None or target_id not in alive_ids:
                continue

            vote_counts[target_id] = (
                vote_counts.get(target_id, 0) + 1
            )

        if not vote_counts:
            self.game.history.append(
                f"{self.game.round_number}-raund: "
                "ovoz berish natijasida hech kim chiqarilmadi."
            )
            self._set_phase(GamePhase.NIGHT)

            return {
                "success": True,
                "message": "Ovoz berish yakunlandi. Hech kim chiqarilmadi.",
                "eliminated": None,
                "tie": False,
            }

        highest_votes = max(vote_counts.values())

        leaders = [
            player_id
            for player_id, count in vote_counts.items()
            if count == highest_votes
        ]

        if len(leaders) > 1:
            self.game.history.append(
                f"{self.game.round_number}-raund: "
                "ovozlar teng bo'ldi."
            )

            return {
                "success": True,
                "message": (
                    "Ovozlar teng. Qayta ovoz berish kerak."
                ),
                "eliminated": None,
                "tie": True,
            }

        target_id = leaders[0]
        target = self.game.players.get(target_id)

        if target is None or not target.alive:
            return {
                "success": False,
                "message": "Ovoz natijasi bo'yicha nishon topilmadi.",
                "eliminated": None,
                "tie": False,
            }

        self.last_words_player_id = target_id
        self._set_phase(GamePhase.LAST_WORDS)

        self.game.history.append(
            f"{target.name} ovoz berish orqali "
            "so'nggi so'z bosqichiga o'tdi."
        )

        return {
            "success": True,
            "message": (
                f"{target.name} so'nggi so'zini aytishi mumkin."
            ),
            "eliminated": target_id,
            "tie": False,
            "last_words_seconds": LAST_WORDS_DURATION,
        }

    def finish_last_words(self) -> dict:
        if self.game.phase != GamePhase.LAST_WORDS:
            return {
                "success": False,
                "message": "Hozir so'nggi so'z bosqichi emas.",
                "eliminated": None,
            }

        target_id = self.last_words_player_id
        target = self.game.players.get(target_id) if target_id else None

        eliminated_id = None

        if target is not None and target.alive:
            success, _message = self.game.eliminate_player(
                target.user_id,
                reason="Ovoz berish natijasida",
            )

            if success:
                eliminated_id = target.user_id

        self.last_words_player_id = None
        self.last_words_deadline = None

        winner = self._check_victory()

        if not winner:
            self.game.round_number += 1
            self._set_phase(GamePhase.NIGHT)

        return {
            "success": True,
            "message": (
                "O'yin yakunlandi."
                if winner
                else "So'nggi so'z bosqichi tugadi. Tun boshlandi."
            ),
            "eliminated": eliminated_id,
            "winner": winner,
        }

    def stop_game(self, reason: str = "O'yin to'xtatildi.") -> bool:
        if self.game.phase in {
            GamePhase.FINISHED,
            GamePhase.STOPPED,
        }:
            return False

        self.game.night_actions.clear()
        self.game.votes.clear()
        self.game.winner = None

        self._set_phase(GamePhase.STOPPED)
        self.game.history.append(reason)

        return True
        
