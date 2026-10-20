
from __future__ import annotations

from dataclasses import dataclass, field

from game_state import GamePhase, GameState, PlayerStatus
from roles import ROLES, Team


class PartnerError(Exception):
    """Maxfiy sheriklar tizimidagi xato."""


@dataclass(frozen=True, slots=True)
class PartnerInfo:
    game_id: str
    user_id: int
    partner_ids: tuple[int, ...]
    team: str
    private: bool = True


@dataclass(slots=True)
class PartnerRegistry:
    """Bir o'yindagi sheriklik ma'lumotlarini boshqaradi."""

    game_id: str
    partners: dict[int, set[int]] = field(default_factory=dict)

    def link(self, first_id: int, second_id: int) -> None:
        if first_id == second_id:
            raise PartnerError("O'yinchi o'ziga sherik bo'la olmaydi.")

        self.partners.setdefault(first_id, set()).add(second_id)
        self.partners.setdefault(second_id, set()).add(first_id)

    def unlink(self, first_id: int, second_id: int) -> None:
        self.partners.get(first_id, set()).discard(second_id)
        self.partners.get(second_id, set()).discard(first_id)

    def get_partners(self, user_id: int) -> tuple[int, ...]:
        return tuple(sorted(self.partners.get(user_id, set())))

    def remove_player(self, user_id: int) -> None:
        for partner_id in self.partners.pop(user_id, set()):
            self.partners.get(partner_id, set()).discard(user_id)


class GamePartners:
    """THRONE o'yini uchun maxfiy sheriklar xizmat qatlami."""

    # Bu rollar uchun jamoa a'zolarini ko'rish imkoniyati beriladi.
    # Har bir rolning maxsus qoidalari keyinchalik alohida kengaytiriladi.
    TEAM_VISIBILITY_ROLES = {
        "soya_hukmdori",
        "soya_qotili",
        "soya_josusi",
        "zaharsoz",
        "soya_tabibi",
        "qorongu_vazir",
        "soya_kuzatuvchisi",
        "soxta_maslahatchi",
        "soya_jallodi",
        "soya_qorovuli",
        "isyon_boshligi",
        "isyon_jangchisi",
        "isyon_josusi",
        "fitnachi",
        "isyon_tabibi",
        "isyon_mergan",
        "isyon_qorovuli",
        "isyon_usta",
        "isyon_targibotchisi",
        "yashirin_isyonchi",
    }

    def __init__(self, game: GameState) -> None:
        self.game = game
        self.registry = PartnerRegistry(game_id=game.game_id)

    def build(self) -> dict[int, PartnerInfo]:
        """O'yinchilarning maxfiy sheriklik ma'lumotlarini tayyorlaydi.

        Soya va Isyon jamoalari o'z jamoasidagi boshqa tirik
        o'yinchilarni ko'ra oladi. Mustaqil va Kron o'yinchilari
        avtomatik tarzda jamoa sheriklarini olmaydi.
        """

        if self.game.phase == GamePhase.LOBBY:
            raise PartnerError(
                "Sheriklar o'yin boshlangandan keyin aniqlanadi."
            )

        alive_players = [
            player
            for player in self.game.players.values()
            if player.status == PlayerStatus.ALIVE
        ]

        for player in alive_players:
            role = player.role

            if role is None or player.team is None:
                continue

            if role.id not in self.TEAM_VISIBILITY_ROLES:
                continue

            teammates = [
                other
                for other in alive_players
                if other.user_id != player.user_id
                and other.team == player.team
            ]

            for teammate in teammates:
                self.registry.link(
                    player.user_id,
                    teammate.user_id,
                )

        # O'yinchi obyektlarida ham sheriklik ro'yxatini yangilaymiz.
        for player in self.game.players.values():
            player.partner_ids = set(
                self.registry.get_partners(player.user_id)
            )

        return {
            player.user_id: self._private_info(player.user_id)
            for player in self.game.players.values()
            if player.status == PlayerStatus.ALIVE
        }

    def get_private_info(self, user_id: int) -> PartnerInfo:
        """Faqat so'ralgan o'yinchining shaxsiy ma'lumotini beradi."""

        player = self.game.get_player(user_id)

        if player is None:
            raise PartnerError("O'yinchi bu o'yinda topilmadi.")

        if player.status != PlayerStatus.ALIVE:
            raise PartnerError(
                "Faqat tirik o'yinchining maxfiy ma'lumoti beriladi."
            )

        return self._private_info(user_id)

    def _private_info(self, user_id: int) -> PartnerInfo:
        player = self.game.get_player(user_id)

        if player is None:
            raise PartnerError("O'yinchi topilmadi.")

        team_name = (
            player.team.value
            if player.team is not None
            else "UNKNOWN"
        )

        return PartnerInfo(
            game_id=self.game.game_id,
            user_id=user_id,
            partner_ids=self.registry.get_partners(user_id),
            team=team_name,
        )

    def remove_player(self, user_id: int) -> None:
        """O'yinchi sheriklik ro'yxatidan chiqariladi."""

        self.registry.remove_player(user_id)

        player = self.game.get_player(user_id)
        if player is not None:
            player.partner_ids.clear()

        for other in self.game.players.values():
            other.partner_ids.discard(user_id)


def create_game_partners(game: GameState) -> GamePartners:
    return GamePartners(game)
  
