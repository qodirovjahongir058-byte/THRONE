
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
    """THRONE tungi harakatlarini yagona tartibda hal qiladi."""

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

    @staticmethod
    def _get_actor(game: Game, action: dict):
        actor_id = action.get("actor_id")
        actor = game.players.get(actor_id)

        if actor is None or not actor.alive:
            return None

        return actor

    @staticmethod
    def _get_target(game: Game, action: dict):
        target_id = action.get("target_id")

        if target_id is None:
            return None

        target = game.players.get(target_id)

        if target is None or not target.alive:
            return None

        return target

    @classmethod
    def resolve_night(cls, game: Game) -> NightResolution:
        if game.phase != GamePhase.NIGHT:
            return NightResolution(
                success=False,
                messages=[
                    "Tungi harakatlarni faqat tun bosqichida "
                    "hal qilish mumkin."
                ],
            )

        result = NightResolution(success=True)
        actions = list(game.night_actions)

        blocked: set[int] = set()
        protected: set[int] = set()
        healed: set[int] = set()
        attacked: dict[int, list[dict]] = {}

        # 1. Bloklash.
        # Bloklangan o'yinchining boshqa tungi harakatlari
        # bajarilmaydi.
        for action in actions:
            if action.get("action_type") not in cls.BLOCK_ACTIONS:
                continue

            actor = cls._get_actor(game, action)
            target = cls._get_target(game, action)

            if actor is None or target is None:
                continue

            blocked.add(target.user_id)

        result.blocked = sorted(blocked)

        active_actions = [
            action
            for action in actions
            if action.get("actor_id") not in blocked
        ]

        # 2. Himoya va davolash.
        for action in active_actions:
            action_type = action.get("action_type")

            if action_type not in (
                cls.PROTECT_ACTIONS | cls.HEAL_ACTIONS
            ):
                continue

            actor = cls._get_actor(game, action)
            target = cls._get_target(game, action)

            if actor is None or target is None:
                continue

            if action_type in cls.PROTECT_ACTIONS:
                protected.add(target.user_id)

            elif action_type in cls.HEAL_ACTIONS:
                healed.add(target.user_id)

        result.healed = sorted(healed)

        # 3. Tekshiruv va kuzatuv.
        for action in active_actions:
            action_type = action.get("action_type")

            if action_type not in (
                cls.INVESTIGATE_ACTIONS | cls.OBSERVE_ACTIONS
            ):
                continue

            actor = cls._get_actor(game, action)
            target = cls._get_target(game, action)

            if actor is None or target is None:
                continue

            if action_type in cls.INVESTIGATE_ACTIONS:
                role = get_role(target.role_id or "")

                if role is not None:
                    result.investigated[actor.user_id] = (
                        f"{target.name} o'yinchisining jamoasi: "
                        f"{role.team.value}"
                    )

            elif action_type in cls.OBSERVE_ACTIONS:
                target_actions = [
                    other
                    for other in active_actions
                    if other.get("target_id") == target.user_id
                    and other.get("actor_id") != actor.user_id
                    and other.get("action_type") not in cls.BLOCK_ACTIONS
                ]

                result.investigated[actor.user_id] = (
                    f"{target.name} o'yinchisiga yo'naltirilgan "
                    f"harakatlar soni: {len(target_actions)}"
                )

        # 4. Hujumlarni yig'ish.
        for action in active_actions:
            if action.get("action_type") not in cls.ATTACK_ACTIONS:
                continue

            actor = cls._get_actor(game, action)
            target = cls._get_target(game, action)

            if actor is None or target is None:
                continue

            attacked.setdefault(target.user_id, []).append(action)

        # 5. Hujum natijalari.
        for target_id, target_attacks in attacked.items():
            target = game.players.get(target_id)

            if target is None or not target.alive:
                continue

            bypass_protection = any(
                action.get("action_type")
                in cls.BYPASS_PROTECTION_ACTIONS
                for action in target_attacks
            )

            # Davolash oddiy va himoyani chetlab o'tuvchi
            # hujumdan ham saqlaydi.
            if target_id in healed:
                result.messages.append(
                    f"{target.name} davolash yordamida omon qoldi."
                )
                continue

            if target_id in protected and not bypass_protection:
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
                    f"{target.name} tungi hujum natijasida "
                    "o'yindan chiqdi."
                )
            elif message:
                result.messages.append(message)

        # 6. Tun tarixini saqlash va harakatlarni tozalash.
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
        
