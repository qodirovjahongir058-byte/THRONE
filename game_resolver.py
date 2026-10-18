
from dataclasses import dataclass, field

from game_engine import Game, GamePhase
from roles import get_role


@dataclass
class NightResolution:
    success: bool
    messages: list[str] = field(default_factory=list)
    eliminated: list[int] = field(default_factory=list)
    blocked: list[int] = field(default_factory=list)
    healed: list[int] = field(default_factory=list)
    investigated: dict[int, str] = field(default_factory=dict)


class GameResolver:
    """THRONE tungi harakatlarining natijalarini hisoblaydi."""

    ATTACK_ACTIONS = {
        "attack",
        "team_attack",
        "hidden_attack",
        "attack_bypass",
        "contract_attack",
    }

    BYPASS_PROTECTION_ACTIONS = {
        "hidden_attack",
        "attack_bypass",
    }

    BLOCK_ACTIONS = {
        "block",
        "sabotage",
    }

    PROTECT_ACTIONS = {
        "protect",
        "guard",
    }

    HEAL_ACTIONS = {"heal"}

    INVESTIGATE_ACTIONS = {
        "investigate",
        "memory_check",
    }

    OBSERVE_ACTIONS = {"observe"}

    @classmethod
    def resolve_night(cls, game: Game) -> NightResolution:
        if game.phase != GamePhase.NIGHT:
            return NightResolution(
                success=False,
                messages=[
                    "Tungi harakatlarni faqat tun bosqichida "
                    "yechish mumkin."
                ],
            )

        result = NightResolution(success=True)
        actions = list(game.night_actions)

        blocked: set[int] = set()
        protected: set[int] = set()
        healed: set[int] = set()
        attacked: dict[int, list[dict]] = {}
        investigation_results: dict[int, str] = {}

        # 1. Bloklash va sabotaj.
        for action in actions:
            if action.get("action_type") not in cls.BLOCK_ACTIONS:
                continue

            target_id = action.get("target_id")
            actor = game.players.get(action.get("actor_id"))
            target = game.players.get(target_id)

            if target_id is None:
                continue

            if actor is None or not actor.alive:
                continue

            if target is None or not target.alive:
                continue

            blocked.add(target_id)

        result.blocked = sorted(blocked)

        # Bloklangan o'yinchilarning harakatlari bajarilmaydi.
        active_actions = [
            action
            for action in actions
            if action.get("actor_id") not in blocked
        ]

        # 2. Himoya va davolash.
        for action in active_actions:
            action_type = action.get("action_type")
            target_id = action.get("target_id")

            if target_id is None:
                continue

            actor = game.players.get(action.get("actor_id"))
            target = game.players.get(target_id)

            if actor is None or not actor.alive:
                continue

            if target is None or not target.alive:
                continue

            if action_type in cls.PROTECT_ACTIONS:
                protected.add(target_id)

            elif action_type in cls.HEAL_ACTIONS:
                healed.add(target_id)

        result.healed = sorted(healed)

        # 3. Tekshiruv va kuzatuv.
        for action in active_actions:
            action_type = action.get("action_type")
            target_id = action.get("target_id")
            actor_id = action.get("actor_id")

            if target_id is None:
                continue

            actor = game.players.get(actor_id)
            target = game.players.get(target_id)

            if actor is None or not actor.alive:
                continue

            if target is None or not target.alive:
                continue

            if action_type in cls.INVESTIGATE_ACTIONS:
                target_role = get_role(target.role_id or "")

                if target_role is not None:
                    investigation_results[actor_id] = (
                        f"{target.name} jamoasi: "
                        f"{target_role.team.value}"
                    )

            elif action_type in cls.OBSERVE_ACTIONS:
                target_actions = [
                    item
                    for item in active_actions
                    if item.get("target_id") == target_id
                    and item.get("actor_id") != actor_id
                ]

                investigation_results[actor_id] = (
                    f"{target.name}ga yo'naltirilgan "
                    f"harakatlar soni: {len(target_actions)}"
                )

        result.investigated = investigation_results

        # 4. Hujumlarni nishonlar bo'yicha yig'ish.
        for action in active_actions:
            if action.get("action_type") not in cls.ATTACK_ACTIONS:
                continue

            target_id = action.get("target_id")

            if target_id is None:
                continue

            actor = game.players.get(action.get("actor_id"))
            target = game.players.get(target_id)

            if actor is None or not actor.alive:
                continue

            if target is None or not target.alive:
                continue

            attacked.setdefault(target_id, []).append(action)

        # 5. Hujum natijalarini hisoblash.
        for target_id, target_attacks in attacked.items():
            target = game.players.get(target_id)

            if target is None or not target.alive:
                continue

            bypass_attack = any(
                action.get("action_type")
                in cls.BYPASS_PROTECTION_ACTIONS
                for action in target_attacks
            )

            # Himoyani chetlab o'tuvchi hujumlar davolashni
            # avtomatik ravishda chetlab o'tmaydi.
            if target_id in healed:
                result.messages.append(
                    f"{target.name} tabib yordami bilan omon qoldi."
                )
                continue

            if target_id in protected and not bypass_attack:
                result.messages.append(
                    f"{target.name} qo'riqchi tomonidan himoyalandi."
                )
                continue

            success, _message = game.eliminate_player(
                target_id,
                reason="Tungi hujum natijasida",
            )

            if success:
                result.eliminated.append(target_id)
                result.messages.append(
                    f"{target.name} tungi hujum natijasida "
                    "o'yindan chiqdi."
                )

        # 6. Hozircha alohida mexanizmi yo'q maxsus amallar
        # faqat qayd etiladi. Bu ularning to'liq ishlashini anglatmaydi.
        recorded_actions = {
            "trade",
            "feed",
            "steal_gold",
            "influence",
            "succession",
            "inspect_treasury",
            "claim_throne",
            "visit",
            "survive",
            "mislead",
            "judge",
        }

        for action in active_actions:
            action_type = action.get("action_type")

            if action_type in recorded_actions:
                actor = game.players.get(action.get("actor_id"))

                if actor is not None and actor.alive:
                    result.messages.append(
                        f"{actor.name} maxsus harakatni bajardi: "
                        f"{action_type}."
                    )

        # 7. Tun yakuni.
        game.night_actions.clear()

        for player in game.players.values():
            player.night_action = None

        game.history.append(
            f"{game.round_number}-tun yakunlandi. "
            f"Chiqarilgan o'yinchilar: {len(result.eliminated)}."
        )

        return result


def resolve_night(game: Game) -> NightResolution:
    """Tungi natijalarni hisoblash uchun tashqi funksiya."""
    return GameResolver.resolve_night(game)
                    
