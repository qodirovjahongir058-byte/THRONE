
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game_state import GamePhase, GameState
from roles import Team


# ============================================================
# THRONE — NIGHT ACTION RESOLVER
# ============================================================


@dataclass(slots=True)
class ResolutionEvent:
    event_type: str
    actor_id: int | None = None
    target_id: int | None = None
    message_key: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResolutionResult:
    game_id: str
    round_number: int
    events: list[ResolutionEvent] = field(default_factory=list)
    eliminated_player_ids: list[int] = field(default_factory=list)
    protected_player_ids: list[int] = field(default_factory=list)
    blocked_player_ids: list[int] = field(default_factory=list)
    investigation_results: dict[int, dict[str, Any]] = field(
        default_factory=dict
    )

    @property
    def has_eliminations(self) -> bool:
        return bool(self.eliminated_player_ids)


class GameResolutionError(Exception):
    """Tungi harakatlarni hal qilishdagi xato."""


# Bir-biriga zid yoki xavfli harakatlar uchun ustuvorlik.
ACTION_PRIORITY: dict[str, int] = {
    "block": 10,
    "weaken": 15,
    "protect": 20,
    "protect_ally": 20,
    "guard": 20,
    "self_protect": 20,
    "inspect_defense": 30,
    "investigate": 40,
    "investigate_team": 40,
    "observe": 40,
    "mislead": 35,
    "conceal": 35,
    "poison": 50,
    "revenge": 55,
    "team_attack": 60,
    "rebellion_action": 60,
    "rebellion_attack": 60,
    "solo_attack": 60,
}


class GameResolver:
    """Tungi harakatlarni bosqichma-bosqich hal qiladi."""

    def resolve_night(self, game: GameState) -> ResolutionResult:
        if game.phase != GamePhase.NIGHT:
            raise GameResolutionError(
                "Tungi harakatlarni faqat NIGHT bosqichida hal qilish mumkin."
            )

        result = ResolutionResult(
            game_id=game.game_id,
            round_number=game.round_number,
        )

        actions = [
            dict(action)
            for action in game.pending_actions
        ]

        # Faqat shu o'yinga tegishli va tirik o'yinchilar harakatlari.
        valid_actions: list[dict[str, Any]] = []

        for action in actions:
            if action.get("game_id") != game.game_id:
                continue

            actor = game.get_player(action.get("actor_id"))

            if actor is None or not actor.is_alive:
                continue

            target_id = action.get("target_id")
            if target_id is not None:
                target = game.get_player(target_id)
                if target is None or not target.is_alive:
                    continue

            valid_actions.append(action)

        valid_actions.sort(
            key=lambda action: ACTION_PRIORITY.get(
                action.get("action_type", ""),
                100,
            )
        )

        # Harakatlarning joriy tun uchun holati.
        blocked: set[int] = set()
        protected: set[int] = set()
        concealed: set[int] = set()
        weakened: set[int] = set()
        poisoned: set[int] = set()

        attacks: dict[int, list[dict[str, Any]]] = {}
        investigation_actions: list[dict[str, Any]] = []
        observation_actions: list[dict[str, Any]] = []

        # 1. To'sish va zaiflashtirish.
        for action in valid_actions:
            action_type = action["action_type"]
            actor_id = action["actor_id"]
            target_id = action.get("target_id")

            if target_id is None:
                continue

            if action_type == "block":
                blocked.add(target_id)
                result.blocked_player_ids.append(target_id)
                result.events.append(
                    ResolutionEvent(
                        event_type="blocked",
                        actor_id=actor_id,
                        target_id=target_id,
                        message_key="night_action_blocked",
                    )
                )

            elif action_type == "weaken":
                weakened.add(target_id)

        # 2. To'silmagan o'yinchilarning himoya harakatlari.
        for action in valid_actions:
            actor_id = action["actor_id"]
            action_type = action["action_type"]
            target_id = action.get("target_id")

            if actor_id in blocked:
                continue

            if action_type in {
                "protect",
                "protect_ally",
                "guard",
                "self_protect",
            }:
                actual_target = actor_id if action_type == "self_protect" else target_id

                if actual_target is None:
                    continue

                if action_type == "protect_ally":
                    actor = game.get_player(actor_id)
                    target = game.get_player(actual_target)

                    if (
                        actor is None
                        or target is None
                        or actor.team != target.team
                    ):
                        continue

                protected.add(actual_target)
                result.events.append(
                    ResolutionEvent(
                        event_type="protected",
                        actor_id=actor_id,
                        target_id=actual_target,
                        message_key="night_player_protected",
                    )
                )

        # 3. Yashirinish va zaharlash.
        for action in valid_actions:
            actor_id = action["actor_id"]
            action_type = action["action_type"]
            target_id = action.get("target_id")

            if actor_id in blocked:
                continue

            if action_type == "conceal":
                concealed.add(actor_id)

            elif action_type == "poison" and target_id is not None:
                poisoned.add(target_id)

        # 4. Tekshiruv va kuzatuv harakatlarini yig'ish.
        for action in valid_actions:
            actor_id = action["actor_id"]
            action_type = action["action_type"]

            if actor_id in blocked:
                continue

            if action_type in {
                "investigate",
                "investigate_team",
                "inspect_defense",
                "mislead",
            }:
                investigation_actions.append(action)

            elif action_type == "observe":
                observation_actions.append(action)

        # 5. Hujumlarni yig'ish.
        for action in valid_actions:
            actor_id = action["actor_id"]
            action_type = action["action_type"]
            target_id = action.get("target_id")

            if actor_id in blocked or target_id is None:
                continue

            if action_type not in {
                "team_attack",
                "rebellion_attack",
                "rebellion_action",
                "solo_attack",
                "revenge",
            }:
                continue

            actor = game.get_player(actor_id)
            target = game.get_player(target_id)

            if actor is None or target is None:
                continue

            if actor.team is None:
                continue

            # Jamoaviy hujumlar faqat o'z jamoasidan bo'ladi.
            if (
                action_type == "team_attack"
                and actor.team != Team.SOYA
            ):
                continue

            if (
                action_type in {"rebellion_attack", "rebellion_action"}
                and actor.team != Team.ISYON
            ):
                continue

            if (
                action_type == "solo_attack"
                and actor.team != Team.MUSTAQIL
            ):
                continue

            # Jamoa o'z a'zosiga hujum qilmaydi.
            if (
                action_type in {"team_attack", "rebellion_attack"}
                and actor.team == target.team
            ):
                continue

            attacks.setdefault(target_id, []).append(action)

        # 6. Hujum natijalari. Himoya mavjud bo'lsa, hujum to'xtaydi.
        eliminated_this_night: set[int] = set()

        for target_id, target_attacks in attacks.items():
            target = game.get_player(target_id)

            if target is None or not target.is_alive:
                continue

            if target_id in protected:
                result.events.append(
                    ResolutionEvent(
                        event_type="attack_blocked",
                        target_id=target_id,
                        message_key="night_attack_prevented",
                    )
                )
                continue

            # Shahzodaning bir martalik omon qolish qobiliyati.
            if target.role_id == "shahzoda":
                if not target.ability_data.get("survival_used", False):
                    target.ability_data["survival_used"] = True
                    result.events.append(
                        ResolutionEvent(
                            event_type="survived",
                            target_id=target_id,
                            message_key="player_survived_attack",
                        )
                    )
                    continue

            reasons = [
                action["action_type"]
                for action in target_attacks
            ]

            if target.eliminate(
                reason="night_attack:" + ",".join(reasons)
            ):
                eliminated_this_night.add(target_id)
                result.eliminated_player_ids.append(target_id)
                result.events.append(
                    ResolutionEvent(
                        event_type="eliminated",
                        target_id=target_id,
                        message_key="player_eliminated_at_night",
                        data={"reasons": reasons},
                    )
                )

        # 7. Zahar ta'siri. Himoya zaharni avtomatik bekor qilmaydi.
        for target_id in poisoned:
            target = game.get_player(target_id)

            if target is None or not target.is_alive:
                continue

            # Ushbu versiyada zahar o'yinchini shu tunning o'zida
            # o'ldirmaydi; keyingi tizimda davomiy ta'sir qo'shiladi.
            target.poisoned = True
            result.events.append(
                ResolutionEvent(
                    event_type="poisoned",
                    target_id=target_id,
                    message_key="player_poisoned",
                )
            )

        # 8. Tekshiruv natijalari. Natijalar faqat so'rovchiga
        # yuborilishi kerak; ommaviy guruhga chiqarilmaydi.
        for action in investigation_actions:
            actor_id = action["actor_id"]
            target_id = action.get("target_id")
            action_type = action["action_type"]

            if target_id is None:
                continue

            target = game.get_player(target_id)
            if target is None:
                continue

            if action_type == "inspect_defense":
                value: Any = target_id in protected
                result_key = "is_protected"

            elif action_type == "investigate_team":
                if target_id in concealed:
                    value = "UNKNOWN"
                else:
                    value = (
                        target.team.value
                        if target.team is not None
                        else "UNKNOWN"
                    )
                result_key = "team"

            else:
                if target_id in concealed:
                    value = "UNKNOWN"
                else:
                    value = target.role_id or "UNKNOWN"
                result_key = "role"

            if action_type == "mislead":
                # Chalg'ituvchi rolning aniq natijasi alohida
                # rol mexanizmi bilan keyin kengaytiriladi.
                value = "UNKNOWN"

            result.investigation_results.setdefault(
                actor_id, {}
            )[str(target_id)] = {
                result_key: value,
                "action_type": action_type,
            }

        # 9. Kuzatuv natijalari.
        for action in observation_actions:
            actor_id = action["actor_id"]
            target_id = action.get("target_id")

            if target_id is None:
                continue

            observed_actions = [
                item
                for item in valid_actions
                if item.get("actor_id") == target_id
                and target_id not in blocked
            ]

            result.investigation_results.setdefault(
                actor_id, {}
            )[str(target_id)] = {
                "observed_actions": [
                    item.get("action_type")
                    for item in observed_actions
                ]
            }

        result.protected_player_ids = sorted(protected)
        result.blocked_player_ids = sorted(blocked)

        # Tungi harakatlar bir marta hal qilinadi.
        game.pending_actions.clear()

        return result


def resolve_night(game: GameState) -> ResolutionResult:
    """Tungi harakatlarni hal qilish uchun qulay funksiya."""
    return GameResolver().resolve_night(game)
            
