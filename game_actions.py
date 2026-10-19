
from dataclasses import dataclass, field
from typing import Any

from game_engine import Game, GamePhase
from roles import get_role


ATTACK_ACTIONS = {
    "attack",
    "team_attack",
    "hidden_attack",
    "contract_attack",
    "attack_bypass",
}


ALLOWED_ACTIONS = {
    "attack",
    "team_attack",
    "protect",
    "guard",
    "heal",
    "block",
    "investigate",
    "observe",
    "hidden_attack",
    "attack_bypass",
    "shadow_mask",
    "steal_gold",
    "visit",
    "memory_check",
    "mislead",
    "sabotage",
    "influence",
    "succession",
    "inspect_treasury",
    "contract_attack",
    "claim_throne",
    "feed",
    "trade",
    "survive",
    "judge",
}


NON_TARGET_ACTIONS = {
    "survive",
    "succession",
}


@dataclass
class ActionResult:
    success: bool
    message: str
    action: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


class GameActionManager:
    """Tungi harakatlarni tekshiradi va o'yinga yozadi."""

    @staticmethod
    def submit_action(
        game: Game,
        actor_id: int,
        action_type: str,
        target_id: int | None = None,
        **kwargs: Any,
    ) -> ActionResult:
        if game.phase != GamePhase.NIGHT:
            return ActionResult(
                False,
                "Harakatni faqat tun bosqichida bajarish mumkin.",
            )

        actor = game.players.get(actor_id)

        if actor is None:
            return ActionResult(
                False,
                "Siz ushbu o'yin ishtirokchisi emassiz.",
            )

        if not actor.alive:
            return ActionResult(
                False,
                "O'yindan chiqqan o'yinchi harakat qila olmaydi.",
            )

        if action_type not in ALLOWED_ACTIONS:
            return ActionResult(
                False,
                "Noma'lum harakat turi.",
            )

        role = get_role(actor.role_id or "")

        if role is None:
            return ActionResult(
                False,
                "Rolingiz aniqlanmadi.",
            )

        if role.action != action_type:
            return ActionResult(
                False,
                "Bu harakat sizning rolingizga mos kelmaydi.",
            )

        if action_type not in NON_TARGET_ACTIONS:
            if target_id is None:
                return ActionResult(
                    False,
                    "Nishonni tanlang.",
                )

            target = game.players.get(target_id)

            if target is None:
                return ActionResult(
                    False,
                    "Tanlangan o'yinchi ushbu o'yinda yo'q.",
                )

            if not target.alive:
                return ActionResult(
                    False,
                    "O'yindan chiqqan o'yinchini nishon qilib bo'lmaydi.",
                )

            if action_type in ATTACK_ACTIONS and target_id == actor_id:
                return ActionResult(
                    False,
                    "O'zingizga hujum qila olmaysiz.",
                )

        # action_type — resolver uchun.
        # action — eski modullar bilan moslik uchun saqlanadi.
        action = {
            "actor_id": actor_id,
            "action_type": action_type,
            "action": action_type,
            "target_id": target_id,
            **kwargs,
        }

        # Har bir o'yinchi bir tunda faqat bitta faol
        # harakatga ega bo'ladi. Qayta tanlasa, avvalgisi yangilanadi.
        game.night_actions = [
            old_action
            for old_action in game.night_actions
            if old_action.get("actor_id") != actor_id
        ]

        game.night_actions.append(action)
        actor.night_action = action_type

        return ActionResult(
            True,
            "Harakatingiz qabul qilindi.",
            action=action,
        )

    @staticmethod
    def get_player_action(
        game: Game,
        actor_id: int,
    ) -> dict[str, Any] | None:
        for action in game.night_actions:
            if action.get("actor_id") == actor_id:
                return action

        return None

    @staticmethod
    def clear_actions(game: Game) -> None:
        game.night_actions.clear()

        for player in game.players.values():
            player.night_action = None

    @staticmethod
    def cancel_action(
        game: Game,
        actor_id: int,
    ) -> ActionResult:
        if game.phase != GamePhase.NIGHT:
            return ActionResult(
                False,
                "Harakatni faqat tun bosqichida bekor qilish mumkin.",
            )

        existing = GameActionManager.get_player_action(game, actor_id)

        if existing is None:
            return ActionResult(
                False,
                "Bekor qilinadigan harakat topilmadi.",
            )

        game.night_actions = [
            action
            for action in game.night_actions
            if action.get("actor_id") != actor_id
        ]

        player = game.players.get(actor_id)

        if player is not None:
            player.night_action = None

        return ActionResult(
            True,
            "Harakatingiz bekor qilindi.",
)
        
