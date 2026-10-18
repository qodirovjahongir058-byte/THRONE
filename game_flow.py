from dataclasses import dataclass

from game_engine import Game, GamePhase
from game_resolver import GameResolver, NightResolution
from game_voting import GameVoting, VotingResult
from game_victory import GameVictory, VictoryResult


@dataclass(frozen=True, slots=True)
class FlowResult:
    success: bool
    message: str
    phase: GamePhase
    night_result: NightResolution | None = None
    voting_result: VotingResult | None = None
    victory_result: VictoryResult | None = None


class GameFlow:
    """THRONE o'yinining bosqichlarini boshqaradi."""

    LAST_WORDS_DURATION = 30

    def __init__(self, game: Game) -> None:
        self.game = game
        self.voting = GameVoting()
        self.pending_last_words_player_id: int | None = None

    def start(self, requester_is_admin: bool) -> FlowResult:
        success, message = self.game.start(requester_is_admin)

        return FlowResult(
            success=success,
            message=message,
            phase=self.game.phase,
        )

    def assign_roles_and_begin_night(self) -> FlowResult:
        if self.game.phase != GamePhase.ROLE_REVEAL:
            return self._result(False, "Rollarni taqsimlash bosqichi emas.")

        if not self.game.all_roles_assigned():
            return self._result(False, "Hali barcha rollar biriktirilmagan.")

        success, message = self.game.begin_night()
        return self._result(success, message)

    def resolve_night(self) -> FlowResult:
        result = GameResolver.resolve_night(self.game)

        if not result.success:
            return self._result(False, "; ".join(result.messages))

        victory = GameVictory.check_victory(self.game)

        if victory.finished:
            return FlowResult(
                True,
                victory.message,
                self.game.phase,
                night_result=result,
                victory_result=victory,
            )

        success, message = self.game.begin_day()

        return FlowResult(
            success,
            message,
            self.game.phase,
            night_result=result,
        )

    def begin_discussion(self) -> FlowResult:
        success, message = self.game.begin_discussion()
        return self._result(success, message)

    def begin_voting(self) -> FlowResult:
        success, message = self.voting.start_voting(self.game)
        return self._result(success, message)

    def cast_vote(
        self,
        voter_id: int,
        target_id: int,
    ) -> FlowResult:
        success, message = self.voting.cast_vote(
            self.game,
            voter_id,
            target_id,
        )
        return self._result(success, message)

    def resolve_voting(self) -> FlowResult:
        result = self.voting.resolve_voting(self.game)

        if not result.success:
            return FlowResult(
                False,
                result.message,
                self.game.phase,
                voting_result=result,
            )

        if result.revote_required:
            return FlowResult(
                True,
                result.message,
                self.game.phase,
                voting_result=result,
            )

        if result.eliminated_id is not None:
            self.pending_last_words_player_id = result.eliminated_id
            self.game.phase = GamePhase.LAST_WORDS
            self.game.phase_started_at = __import__("time").time()

            return FlowResult(
                True,
                result.message + " Oxirgi so'z bosqichi boshlandi.",
                self.game.phase,
                voting_result=result,
            )

        victory = GameVictory.check_victory(self.game)

        if victory.finished:
            return FlowResult(
                True,
                victory.message,
                self.game.phase,
                voting_result=result,
                victory_result=victory,
            )

        success, message = self.game.begin_night()

        return FlowResult(
            success,
            message,
            self.game.phase,
            voting_result=result,
        )

    def save_last_words(
        self,
        player_id: int,
        message: str,
    ) -> FlowResult:
        if player_id != self.pending_last_words_player_id:
            return self._result(
                False,
                "Hozir oxirgi so'z navbati sizda emas.",
            )

        success, response = self.game.save_last_words(player_id, message)

        if success:
            self.pending_last_words_player_id = None

        return self._result(success, response)

    def finish_last_words(self) -> FlowResult:
        if self.game.phase != GamePhase.LAST_WORDS:
            return self._result(False, "Oxirgi so'z bosqichi faol emas.")

        if self.pending_last_words_player_id is not None:
            player = self.game.players.get(
                self.pending_last_words_player_id
            )
            if player is not None and player.last_words is None:
                player.last_words = "Oxirgi so'z aytilmadi."

        self.pending_last_words_player_id = None

        victory = GameVictory.check_victory(self.game)

        if victory.finished:
            return FlowResult(
                True,
                victory.message,
                self.game.phase,
                victory_result=victory,
            )

        success, message = self.game.begin_night()
        return self._result(success, message)

    def stop(self, requester_is_admin: bool) -> FlowResult:
        success, message = self.game.stop(requester_is_admin)
        return self._result(success, message)

    def _result(self, success: bool, message: str) -> FlowResult:
        return FlowResult(
            success=success,
            message=message,
            phase=self.game.phase,
        )


def create_game_flow(game: Game) -> GameFlow:
    return GameFlow(game)
