
from __future__ import annotations

from dataclasses import dataclass

from game_state import GameEndReason, GamePhase, GameState
from roles import Team


@dataclass(frozen=True, slots=True)
class VictoryResult:
    finished: bool
    winner: Team | str | None
    reason: str


def check_victory(game: GameState) -> VictoryResult:
    """O'yin holatiga qarab g'olibni aniqlaydi."""

    if game.phase in {GamePhase.FINISHED, GamePhase.STOPPED}:
        return VictoryResult(
            finished=True,
            winner=game.winner,
            reason="game_already_finished",
        )

    alive_players = game.alive_players

    if not alive_players:
        game.finish(
            winner=None,
            reason=GameEndReason.VICTORY,
        )
        return VictoryResult(
            finished=True,
            winner=None,
            reason="no_survivors",
        )

    alive_teams = {
        player.team
        for player in alive_players
        if player.team is not None
    }

    # Mustaqil rollarning alohida g'alaba shartlari.
    for player in alive_players:
        if player.team != Team.MUSTAQIL:
            continue

        if player.role_id == "omon_qoluvchi":
            # Omon qoluvchi tirik qolishi kerak.
            # Boshqa jamoalar to'liq yo'qolmaguncha bu rol
            # avtomatik g'olib deb belgilanmaydi.
            continue

        if player.role_id == "yollanma_qotil":
            # Qotilning maxsus maqsadi keyinchalik kengaytiriladi.
            continue

        if player.role_id == "qasoskor":
            # Qasoskor uchun nishon va qasos sharti alohida
            # mexanizmda belgilanadi.
            continue

        if player.role_id == "soya_sayyohi":
            # Yashirin sayyohning shaxsiy g'alabasi keyin
            # alohida maqsad tizimi orqali tekshiriladi.
            continue

    # Jamoalar orasida faqat bitta jamoa qolgan bo'lsa,
    # shu jamoa g'olib bo'ladi.
    if len(alive_teams) == 1:
        winner = next(iter(alive_teams))

        game.finish(
            winner=winner,
            reason=GameEndReason.VICTORY,
        )

        return VictoryResult(
            finished=True,
            winner=winner,
            reason="last_team_standing",
        )

    # Hech bir jamoa qolmagan, lekin tirik o'yinchilar
    # jamoaga biriktirilmagan bo'lsa, o'yin davom etadi.
    return VictoryResult(
        finished=False,
        winner=None,
        reason="no_victory_yet",
    )


def finish_game(
    game: GameState,
    winner: Team | str | None,
    reason: GameEndReason = GameEndReason.VICTORY,
) -> VictoryResult:
    """O'yinni yakunlash uchun umumiy funksiya."""

    if game.phase in {GamePhase.FINISHED, GamePhase.STOPPED}:
        return VictoryResult(
            finished=True,
            winner=game.winner,
            reason="game_already_finished",
        )

    game.finish(
        winner=winner,
        reason=reason,
    )

    return VictoryResult(
        finished=True,
        winner=winner,
        reason=reason.value,
    )
    
