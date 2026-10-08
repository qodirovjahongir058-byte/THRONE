from __future__ import annotations

from dataclasses import dataclass

from game_engine import GameState
from game_state import VoteResult


@dataclass(frozen=True, slots=True)
class VoteResolution:
    """Result of one voting round."""

    result: VoteResult
    eliminated_player_id: int | None
    tied_player_ids: tuple[int, ...]
    vote_counts: dict[int, int]


class VoteSystem:
    """Handle THRONE daytime voting."""

    def submit_vote(
        self,
        game: GameState,
        voter_id: int,
        target_id: int,
    ) -> bool:
        """Register one player's vote."""

        voter = game.get_player(voter_id)
        target = game.get_player(target_id)

        if voter is None or target is None:
            return False

        if not voter.alive or not target.alive:
            return False

        if voter_id == target_id:
            return False

        if game.phase.value != "VOTING":
            return False

        voter.voted_for = target_id
        return True

    def resolve_votes(
        self,
        game: GameState,
    ) -> VoteResolution:
        """Calculate the result of the current voting round."""

        vote_counts: dict[int, int] = {}

        for player in game.alive_players():
            target_id = player.voted_for

            if target_id is None:
                continue

            target = game.get_player(target_id)

            if target is None or not target.alive:
                continue

            vote_counts[target_id] = (
                vote_counts.get(target_id, 0) + 1
            )

        if not vote_counts:
            return VoteResolution(
                result=VoteResult.NO_ELIMINATION,
                eliminated_player_id=None,
                tied_player_ids=(),
                vote_counts=vote_counts,
            )

        highest_votes = max(vote_counts.values())

        leaders = tuple(
            player_id
            for player_id, votes in vote_counts.items()
            if votes == highest_votes
        )

        if len(leaders) > 1:
            return VoteResolution(
                result=VoteResult.REVOTE,
                eliminated_player_id=None,
                tied_player_ids=leaders,
                vote_counts=vote_counts,
            )

        eliminated_player_id = leaders[0]

        player = game.get_player(eliminated_player_id)

        if player is None or not player.alive:
            return VoteResolution(
                result=VoteResult.NO_ELIMINATION,
                eliminated_player_id=None,
                tied_player_ids=(),
                vote_counts=vote_counts,
            )

        player.alive = False

        return VoteResolution(
            result=VoteResult.ELIMINATED,
            eliminated_player_id=eliminated_player_id,
            tied_player_ids=(),
            vote_counts=vote_counts,
        )

    def start_revote(
        self,
        game: GameState,
        tied_player_ids: tuple[int, ...],
    ) -> None:
        """Prepare a revote between tied players."""

        game.metadata["revote"] = True
        game.metadata["revote_targets"] = list(
            tied_player_ids
        )

        game.reset_votes()

    def resolve_revote(
        self,
        game: GameState,
    ) -> VoteResolution:
        """
        Resolve the second voting round.

        A second tie means nobody is eliminated.
        """

        tied_targets = set(
            game.metadata.get("revote_targets", [])
        )

        vote_counts: dict[int, int] = {}

        for player in game.alive_players():
            target_id = player.voted_for

            if target_id is None:
                continue

            if target_id not in tied_targets:
                continue

            target = game.get_player(target_id)

            if target is None or not target.alive:
                continue

            vote_counts[target_id] = (
                vote_counts.get(target_id, 0) + 1
            )

        game.metadata.pop("revote", None)
        game.metadata.pop("revote_targets", None)

        if not vote_counts:
            return VoteResolution(
                result=VoteResult.NO_ELIMINATION,
                eliminated_player_id=None,
                tied_player_ids=(),
                vote_counts=vote_counts,
            )

        highest_votes = max(vote_counts.values())

        leaders = tuple(
            player_id
            for player_id, votes in vote_counts.items()
            if votes == highest_votes
        )

        if len(leaders) > 1:
            game.reset_votes()

            return VoteResolution(
                result=VoteResult.NO_ELIMINATION,
                eliminated_player_id=None,
                tied_player_ids=leaders,
                vote_counts=vote_counts,
            )

        eliminated_player_id = leaders[0]

        player = game.get_player(eliminated_player_id)

        if player is None or not player.alive:
            return VoteResolution(
                result=VoteResult.NO_ELIMINATION,
                eliminated_player_id=None,
                tied_player_ids=(),
                vote_counts=vote_counts,
            )

        player.alive = False

        return VoteResolution(
            result=VoteResult.ELIMINATED,
            eliminated_player_id=eliminated_player_id,
            tied_player_ids=(),
            vote_counts=vote_counts,
        )


vote_system = VoteSystem()
