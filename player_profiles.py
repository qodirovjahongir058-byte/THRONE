
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from database import Database, DatabaseError


class ProfileError(Exception):
    """O'yinchi profili bilan bog'liq xato."""


@dataclass(slots=True)
class PlayerProfile:
    user_id: int
    full_name: str
    username: str | None = None

    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    rp: int = 0
    gold: int = 0
    coin: int = 0
    diamond: int = 0

    title: str = "NOVICE"
    language: str = "uz"
    is_premium: bool = False

    @property
    def level(self) -> int:
        """RP asosida 1–100 oralig'idagi daraja."""
        return min(100, max(1, (self.rp // 100) + 1))

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return round(self.wins / self.games_played * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "username": self.username,
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "rp": self.rp,
            "level": self.level,
            "gold": self.gold,
            "coin": self.coin,
            "diamond": self.diamond,
            "title": self.title,
            "language": self.language,
            "is_premium": self.is_premium,
            "win_rate": self.win_rate,
        }


class PlayerProfileManager:
    """Profil, statistika va o'yinchi balanslarini boshqaradi."""

    SUPPORTED_LANGUAGES = {"uz", "ru", "en", "tr", "ar", "ky"}

    def __init__(
        self,
        database: Database,
        creator_id: int,
    ) -> None:
        self.database = database
        self.creator_id = creator_id

    def get_profile(
        self,
        user_id: int,
        full_name: str | None = None,
        username: str | None = None,
    ) -> PlayerProfile:
        """Profilni oladi; mavjud bo'lmasa yaratadi."""

        record = self.database.get_profile(user_id)

        if record is not None:
            return self._from_record(record)

        if full_name is None:
            full_name = f"Player {user_id}"

        profile = PlayerProfile(
            user_id=user_id,
            full_name=full_name,
        )
        profile.username = username

        self._save(profile)
        return profile

    def update_identity(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> PlayerProfile:
        profile = self.get_profile(user_id, full_name, username)
        profile.full_name = full_name
        profile.username = username
        self._save(profile)
        return profile

    def record_game(
        self,
        user_id: int,
        result: str,
        rp_change: int = 0,
        full_name: str | None = None,
    ) -> PlayerProfile:
        """O'yin natijasini statistikaga qo'shadi.

        result: win, loss yoki draw.
        """

        result = result.lower()

        if result not in {"win", "loss", "draw"}:
            raise ProfileError(
                "Natija win, loss yoki draw bo'lishi kerak."
            )

        profile = self.get_profile(user_id, full_name)
        profile.games_played += 1

        if result == "win":
            profile.wins += 1
        elif result == "loss":
            profile.losses += 1
        else:
            profile.draws += 1

        profile.rp = max(0, profile.rp + rp_change)
        self._save(profile)
        return profile

    def change_currency(
        self,
        user_id: int,
        currency: str,
        amount: int,
        full_name: str | None = None,
    ) -> PlayerProfile:
        """Gold, Coin yoki Diamond balansini o'zgartiradi.

        Oddiy o'yinchining balansi manfiy bo'la olmaydi.
        Creator uchun balans cheklanmagan.
        """

        currency = currency.lower()

        fields = {
            "gold": "gold",
            "coin": "coin",
            "diamond": "diamond",
        }

        if currency not in fields:
            raise ProfileError(
                "Valyuta gold, coin yoki diamond bo'lishi kerak."
            )

        profile = self.get_profile(user_id, full_name)
        field = fields[currency]
        current = getattr(profile, field)

        # Creator uchun balansni ko'rsatishda ham cheklov yo'q.
        # Juda katta qiymatlar o'rniga creator uchun amalda
        # sarflanmaydigan maxsus balans qo'llanadi.
        if user_id == self.creator_id:
            setattr(profile, field, max(current + amount, current, 0))
        else:
            new_balance = current + amount

            if new_balance < 0:
                raise ProfileError(
                    f"{currency} yetarli emas. Balans: {current}."
                )

            setattr(profile, field, new_balance)

        self._save(profile)
        return profile

    def set_language(
        self,
        user_id: int,
        language: str,
        full_name: str | None = None,
    ) -> PlayerProfile:
        language = language.lower()

        if language not in self.SUPPORTED_LANGUAGES:
            raise ProfileError(
                "Til uz, ru, en, tr, ar yoki ky bo'lishi kerak."
            )

        profile = self.get_profile(user_id, full_name)
        profile.language = language
        self._save(profile)
        return profile

    def set_premium(
        self,
        user_id: int,
        enabled: bool,
        full_name: str | None = None,
    ) -> PlayerProfile:
        """Premium holatini o'zgartiradi.

        Bu metodni faqat ishonchli to'lov tekshiruvidan
        o'tgan bot kodi chaqirishi kerak.
        """

        profile = self.get_profile(user_id, full_name)
        profile.is_premium = bool(enabled)
        self._save(profile)
        return profile

    def add_rp(
        self,
        user_id: int,
        amount: int,
        full_name: str | None = None,
    ) -> PlayerProfile:
        profile = self.get_profile(user_id, full_name)
        profile.rp = max(0, profile.rp + amount)
        self._save(profile)
        return profile

    def _save(self, profile: PlayerProfile) -> None:
        try:
            self.database.save_profile(
                profile.user_id,
                profile.to_dict(),
            )
        except (DatabaseError, TypeError, ValueError) as exc:
            raise ProfileError(
                f"Profilni saqlashda xato: {exc}"
            ) from exc

    @staticmethod
    def _from_record(record: dict[str, Any]) -> PlayerProfile:
        return PlayerProfile(
            user_id=int(record["user_id"]),
            full_name=str(record.get("full_name") or "Player"),
            username=record.get("username"),
            games_played=int(record.get("games_played", 0)),
            wins=int(record.get("wins", 0)),
            losses=int(record.get("losses", 0)),
            draws=int(record.get("draws", 0)),
            rp=int(record.get("rp", 0)),
            gold=int(record.get("gold", 0)),
            coin=int(record.get("coin", 0)),
            diamond=int(record.get("diamond", 0)),
            title=str(record.get("title", "NOVICE")),
            language=str(record.get("language", "uz")),
            is_premium=bool(record.get("is_premium", False)),
        )


def create_profile_manager(
    database: Database,
    creator_id: int,
) -> PlayerProfileManager:
    return PlayerProfileManager(
        database=database,
        creator_id=creator_id,
    )
