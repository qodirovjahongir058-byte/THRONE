from dataclasses import dataclass, field

from game_engine import Game, GamePhase
from roles import get_role, Team


@dataclass
class NightResolution:
    success: bool
    messages: list[str] = field(default_factory=list)
    eliminated: list[int] = field(default_factory=list)
    blocked: list[int] = field(default_factory=list)
    healed: list[int] = field(default_factory=list)
    investigated: dict[int, str] = field(default_factory=dict)


class GameResolver:
    """THRONE o'yinidagi tungi harakatlar natijasini hisoblaydi."""

    ATTACK_ACTIONS = {
        "attack",
        "team_attack",
        "hidden_attack",
        "contract_attack",
    }

    BLOCK_ACTIONS = {"block", "sabotage"}
    PROTECT_ACTIONS = {"protect", "guard"}
    HEAL_ACTIONS = {"heal"}
    INVESTIGATE_ACTIONS = {"investigate", "memory_check"}
    OBSERVE_ACTIONS = {"observe"}

    @classmethod
    def resolve_night(cls, game: Game) -> NightResolution:
        if game.phase != GamePhase.NIGHT:
            return NightResolution(
                success=False,
                messages=["Tungi harakatlarni faqat tun bosqichida yechish mumkin."],
            )

        result = NightResolution(success=True)
        actions = list(game.night_actions)

        blocked: set[int] = set()
        protected: set[int] = set()
        healed: set[int] = set()
        attacked: dict[int, list[dict]] = {}
        investigation_results: dict[int, str] = {}

        # 1. Bloklash.
        for action in actions:
            if action["action_type"] not in cls.BLOCK_ACTIONS:
                continue

            target_id = action.get("target_id")
            if target_id is None:
                continue

            actor = game.players.get(action["actor_id"])
            target = game.players.get(target_id)

            if actor is None or not actor.alive:
                continue
            if target is None or not target.alive:
                continue

            blocked.add(target_id)

        result.blocked = sorted(blocked)

        # Bloklangan o'yinchilarning oddiy harakatlari bekor qilinadi.
        active_actions = [
            action for action in actions
            if action["actor_id"] not in blocked
        ]

        # 2. Himoya va davolash.
        for action in active_actions:
            action_type = action["action_type"]
            target_id = action.get("target_id")

            if target_id is None:
                continue

            actor = game.players.get(action["actor_id"])
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
            action_type = action["action_type"]
            target_id = action.get("target_id")
            actor_id = action["actor_id"]

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
                    item for item in active_actions
                    if item.get("target_id") == target_id
                    and item["actor_id"] != actor_id
                ]
                investigation_results[actor_id] = (
                    f"{target.name}ga tashriflar soni: "
                    f"{len(target_actions)}"
                )

        result.investigated = investigation_results

        # 4. Hujumlar.
        for action in active_actions:
            if action["action_type"] not in cls.ATTACK_ACTIONS:
                continue

            target_id = action.get("target_id")
            if target_id is None:
                continue

            actor = game.players.get(action["actor_id"])
            target = game.players.get(target_id)

            if actor is None or not actor.alive:
                continue
            if target is None or not target.alive:
                continue

            attacked.setdefault(target_id, []).append(action)

        # 5. Hujum natijasi.
        for target_id, attacks in attacked.items():
            target = game.players.get(target_id)

            if target is None or not target.alive:
                continue

            bypass_attack = any(
                action["action_type"] == "hidden_attack"
                for action in attacks
            )

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

            success, message = game.eliminate_player(
                target_id,
                reason="Tungi hujum natijasida",
            )

            if success:
                result.eliminated.append(target_id)
                result.messages.append(
                    f"{target.name} tungi hujum natijasida o'yindan chiqdi."
                )

        # 6. Maxsus harakatlar uchun xabarlar.
        for action in active_actions:
            action_type = action["action_type"]

            if action_type in {
                "trade",
                "feed",
                "steal_gold",
                "influence",
                "succession",
                "inspect_treasury",
                "claim_throne",
                "contract_attack",
                "visit",
                "survive",
                "mislead",
            }:
                result.messages.append(
                    f"Maxsus harakat qayd etildi: {action_type}."
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
