
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from game_state import GamePhase, GameState, PlayerState
from roles import Team


# ============================================================
# THRONE — GAME ACTIONS
# ============================================================


class GameActionError(Exception):
    """O'yin harakatlari bilan bog'liq xato."""


@dataclass(frozen=True, slots=True)
class GameAction:
    game_id: str
    actor_id: int
    action_type: str
    target_id: int | None = None
    data: dict[str, Any] | None = None


# Har bir rol uchun ruxsat etilgan harakatlar.
ROLE_ACTIONS: dict[str, frozenset[str]] = {
    "shoh": frozenset({"block"}),
    "malika": frozenset({"inspect_defense"}),
    "shahzoda": frozenset(),
    "vazir": frozenset({"investigate"}),
    "bosh_qomondon": frozenset({"protect"}),
    "qirol_qoriqchisi": frozenset({"guard"}),
    "qozi": frozenset({"investigate"}),
    "xazinachi": frozenset(),
    "ritsar": frozenset({"protect"}),
    "xizmatkor": frozenset({"observe"}),
    "tinch_aholi": frozenset(),
    "aygoqchi": frozenset({"investigate_team"}),

    "soya_hukmdori": frozenset({"team_attack"}),
    "soya_qotili": frozenset({"team_attack"}),
    "soya_josusi": frozenset({"investigate_team"}),
    "zaharsoz": frozenset({"poison"}),
    "soya_tabibi": frozenset({"protect_ally"}),
    "qorongu_vazir": frozenset({"block"}),
    "soya_ayg oqchisi": frozenset({"observe"}),
    "soxta_maslahatchi": frozenset({"mislead"}),
    "soya_jallodi": frozenset({"team_attack"}),
    "soya_qorovuli": frozenset({"protect_ally"}),

    "isyon_boshligi": frozenset({"rebellion_action"}),
    "isyon_jangchisi": frozenset({"rebellion_attack"}),
    "isyon josusi": frozenset({"investigate_team"}),
    "fitnachi": frozenset({"block"}),
    "isyon_tabibi": frozenset({"protect"}),
    "isyon_mergan": frozenset({"rebellion_attack"}),
    "isyon_qorovuli": frozenset({"protect_ally"}),
    "isyon_usta": frozenset({"weaken"}),
    "isyon_targibotchisi": frozenset(),
    "yashirin_isyonchi": frozenset({"conceal"}),

    "yollanma_qotil": frozenset({"solo_attack"}),
    "soya_sayyohi": frozenset({"conceal"}),
    "qasoskor": frozenset({"revenge"}),
    "omon_qoluvchi": frozenset({"self_protect"}),
}


TEAM_ACTIONS: dict[str, frozenset[Team]] = {
    "team_attack": frozenset({Team.SOYA}),
    "rebellion_attack": frozenset({Team.ISYON}),
    "rebellion_action": frozenset({Team.ISYON}),
    "solo_attack": frozenset({Team.MUSTAQIL}),
}


SELF_TARGET_ACTIONS = frozenset({
    "self_protect",
    "conceal",
})


class GameActionManager:
    """O'yin harakatlarini tekshirish va navbatga qo'yish."""

    def submit_action(
        self,
        game: GameState,
        actor_id: int,
        action_type: str,
        target_id: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> GameAction:
        """Harakatni tekshiradi va o'yin holatiga qo'shadi."""

        if game.phase != GamePhase.NIGHT:
            raise GameActionError(
                "Harakatlarni faqat tungi bosqichda yuborish mumkin."
            )

        actor = game.get_player(actor_id)

        if actor is None:
            raise GameActionError("O'yinchi bu o'yinda qatnashmaydi.")

        if not actor.is_alive:
            raise GameActionError("O'lgan o'yinchi harakat qila olmaydi.")

        if actor.role_id is None or actor.team is None:
            raise GameActionError("O'yinchining roli hali belgilanmagan.")

        allowed_actions = ROLE_ACTIONS.get(actor.role_id)

        if allowed_actions is None:
            raise GameActionError(
                f"{actor.role_id} roli uchun harakatlar belgilanmagan."
            )

        if action_type not in allowed_actions:
            raise GameActionError(
                "Bu rol tanlangan harakatdan foydalana olmaydi."
            )

        if target_id is None and action_type not in SELF_TARGET_ACTIONS:
            raise GameActionError("Nishonni tanlash kerak.")

        if target_id is not None:
            target = game.get_player(target_id)

            if target is None:
                raise GameActionError("Tanlangan nishon bu o'yinda yo'q.")

            if not target.is_alive:
                raise GameActionError("O'lgan o'yinchini nishon qilib bo'lmaydi.")

            if target_id == actor_id and action_type not in SELF_TARGET_ACTIONS:
                raise GameActionError("Bu harakatda o'zingizni nishon qila olmaysiz.")

        required_team = TEAM_ACTIONS.get(action_type)

        if required_team is not None and actor.team not in required_team:
            raise GameActionError(
                "Bu jamoaviy harakatdan foydalanishga ruxsat yo'q."
            )

        # Har bir rol bir tunda shu turdagi harakatni bir marta yuboradi.
        for existing in game.pending_actions:
            if (
                existing.get("actor_id") == actor_id
                and existing.get("action_type") == action_type
            ):
                raise GameActionError(
                    "Bu harakatni ushbu tunda allaqachon yuborgansiz."
                )

        action = GameAction(
            game_id=game.game_id,
            actor_id=actor_id,
            action_type=action_type,
            target_id=target_id,
            data=dict(data or {}),
        )

        game.pending_actions.append({
            "game_id": action.game_id,
            "actor_id": action.actor_id,
            "action_type": action.action_type,
            "target_id": action.target_id,
            "data": action.data,
        })

        return action

    def get_player_actions(
        self,
        game: GameState,
        actor_id: int,
    ) -> list[dict[str, Any]]:
        """O'yinchining joriy tunda yuborgan harakatlarini qaytaradi."""
        return [
            action
            for action in game.pending_actions
            if action.get("actor_id") == actor_id
        ]

    def cancel_action(
        self,
        game: GameState,
        actor_id: int,
        action_type: str | None = None,
    ) -> bool:
        """O'yinchi harakatini tunda bekor qilishga imkon beradi."""
        if game.phase != GamePhase.NIGHT:
            raise GameActionError(
                "Harakatni faqat tungi bosqichda bekor qilish mumkin."
            )

        for index, action in enumerate(game.pending_actions):
            if action.get("actor_id") != actor_id:
                continue

            if action_type is not None and action.get("action_type") != action_type:
                continue

            game.pending_actions.pop(index)
            return True

        return False

    def clear_actions(self, game: GameState) -> None:
        """Barcha tungi harakatlarni tozalaydi."""
        game.pending_actions.clear()


def submit_action(
    game: GameState,
    actor_id: int,
    action_type: str,
    target_id: int | None = None,
    data: dict[str, Any] | None = None,
) -> GameAction:
    """Qulay funksional interfeys."""
    return GameActionManager().submit_action(
        game=game,
        actor_id=actor_id,
        action_type=action_type,
        target_id=target_id,
        data=data,
)
            
