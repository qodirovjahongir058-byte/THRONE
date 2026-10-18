from dataclasses import dataclass
from typing import Any

from game_engine import Game, GamePhase
from roles import get_role


@dataclass(frozen=True, slots=True)
class ActionResult:
    success: bool
    message: str
    action: dict[str, Any] | None = None


class GameActionManager:
    """THRONE o'yinidagi tungi harakatlarni boshqaradi."""

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

    NON_TARGET_ACTIONS = {"survive", "succession"}

    @staticmethod
    def _get_player(game: Game, user_id: int):
        return game.players.get(user_id)

    @classmethod
    def submit_action(
        cls,
        game: Game,
        actor_id: int,
        action_type: str,
        target_id: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> ActionResult:
        if game.phase != GamePhase.NIGHT:
            return ActionResult(
                False,
                "Harakatni faqat tun bosqichida bajarish mumkin.",
            )

        actor = cls._get_player(game, actor_id)

        if actor is None or not actor.alive:
            return ActionResult(
                False,
                "Siz tirik o'yinchi sifatida harakat qila olmaysiz.",
            )

        role = get_role(actor.role_id or "")

        if role is None:
            return ActionResult(False, "Sizga rol biriktirilmagan.")

        if action_type not in cls.ALLOWED_ACTIONS:
            return ActionResult(False, "Noma'lum harakat turi.")

        if role.action != action_type:
            return ActionResult(
                False,
                "Bu harakat sizning rolingizga mos kelmaydi.",
            )

        if action_type not in cls.NON_TARGET_ACTIONS:
            if target_id is None:
                return ActionResult(
                    False,
                    "Harakat uchun nishon tanlashingiz kerak.",
                )

            target = cls._get_player(game, target_id)

            if target is None or not target.alive:
                return ActionResult(
                    False,
                    "Nishon topilmadi yoki u tirik emas.",
                )

            if target_id == actor_id and action_type in {
                "attack",
                "team_attack",
                "hidden_attack",
                "contract_attack",
            }:
                return ActionResult(
                    False,
                    "O'zingizga hujum qila olmaysiz.",
                )

        action = {
            "actor_id": actor_id,
            "action_type": action_type,
            "target_id": target_id,
            "data": data or {},
        }

        # Bir o'yinchi tun davomida bitta harakat yuboradi.
        existing = next(
            (
                item for item in game.night_actions
                if item["actor_id"] == actor_id
            ),
            None,
        )

        if existing is not None:
            game.night_actions.remove(existing)

        game.night_actions.append(action)
        actor.night_action = action

        return ActionResult(
            True,
            "Tungi harakatingiz qabul qilindi.",
            action,
        )

    @classmethod
    def get_player_action(
        cls,
        game: Game,
        actor_id: int,
    ) -> dict[str, Any] | None:
        for action in game.night_actions:
            if action["actor_id"] == actor_id:
                return action
        return None

    @classmethod
    def clear_actions(cls, game: Game) -> None:
        game.night_actions.clear()

        for player in game.players.values():
            player.night_action = None

    @classmethod
    def cancel_action(
        cls,
        game: Game,
        actor_id: int,
    ) -> ActionResult:
        if game.phase != GamePhase.NIGHT:
            return ActionResult(
                False,
                "Harakatni faqat tun davomida bekor qilish mumkin.",
            )

        actor = cls._get_player(game, actor_id)

        if actor is None or not actor.alive:
            return ActionResult(False, "O'yinchi topilmadi.")

        existing = cls.get_player_action(game, actor_id)

        if existing is None:
            return ActionResult(
                False,
                "Bekor qilinadigan harakat mavjud emas.",
            )

        game.night_actions.remove(existing)
        actor.night_action = None

        return ActionResult(True, "Tungi harakatingiz bekor qilindi.")
