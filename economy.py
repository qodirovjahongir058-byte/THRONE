
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from player_profiles import (
    PlayerProfileManager,
    ProfileError,
)


class EconomyError(Exception):
    """Iqtisodiyot tizimidagi xato."""


@dataclass(frozen=True, slots=True)
class EconomyResult:
    success: bool
    user_id: int
    currency: str
    amount: int
    balance: int | None
    message: str
    data: dict[str, Any]


class Economy:
    """THRONE valyutalari, bonuslari va xaridlari."""

    CURRENCIES = {"gold", "coin", "diamond"}

    DAILY_REWARDS = {
        "gold": 100,
        "coin": 5,
        "diamond": 0,
    }

    def __init__(
        self,
        profiles: PlayerProfileManager,
        creator_id: int,
    ) -> None:
        self.profiles = profiles
        self.creator_id = creator_id

    def get_balance(
        self,
        user_id: int,
        currency: str,
    ) -> int | None:
        currency = self._validate_currency(currency)

        if user_id == self.creator_id:
            return None  # None — cheklanmagan balans.

        profile = self.profiles.get_profile(user_id)
        return int(getattr(profile, currency))

    def add(
        self,
        user_id: int,
        currency: str,
        amount: int,
        reason: str = "reward",
    ) -> EconomyResult:
        """Valyuta beradi. Manfiy miqdor qabul qilinmaydi."""

        currency = self._validate_currency(currency)
        self._validate_amount(amount)

        profile = self.profiles.change_currency(
            user_id=user_id,
            currency=currency,
            amount=amount,
        )

        balance = (
            None
            if user_id == self.creator_id
            else int(getattr(profile, currency))
        )

        return EconomyResult(
            success=True,
            user_id=user_id,
            currency=currency,
            amount=amount,
            balance=balance,
            message="Valyuta qo'shildi.",
            data={"reason": reason},
        )

    def spend(
        self,
        user_id: int,
        currency: str,
        amount: int,
        reason: str = "purchase",
    ) -> EconomyResult:
        """Xarid uchun valyuta sarflaydi."""

        currency = self._validate_currency(currency)
        self._validate_amount(amount)

        if user_id != self.creator_id:
            balance = self.get_balance(user_id, currency)

            if balance is None or balance < amount:
                raise EconomyError(
                    f"{currency} yetarli emas. "
                    f"Mavjud balans: {balance}."
                )

        profile = self.profiles.change_currency(
            user_id=user_id,
            currency=currency,
            amount=-amount,
        )

        new_balance = (
            None
            if user_id == self.creator_id
            else int(getattr(profile, currency))
        )

        return EconomyResult(
            success=True,
            user_id=user_id,
            currency=currency,
            amount=amount,
            balance=new_balance,
            message="To'lov bajarildi.",
            data={"reason": reason},
        )

    def transfer(
        self,
        sender_id: int,
        receiver_id: int,
        currency: str,
        amount: int,
    ) -> tuple[EconomyResult, EconomyResult]:
        """Bir o'yinchidan boshqasiga valyuta o'tkazadi."""

        currency = self._validate_currency(currency)
        self._validate_amount(amount)

        if sender_id == receiver_id:
            raise EconomyError(
                "O'zingizga valyuta o'tkaza olmaysiz."
            )

        if sender_id == self.creator_id:
            raise EconomyError(
                "Creator hisobidan transfer alohida boshqarilishi kerak."
            )

        balance = self.get_balance(sender_id, currency)

        if balance is None or balance < amount:
            raise EconomyError(
                f"{currency} transfer uchun yetarli emas."
            )

        # Avval oluvchiga qo'shamiz, keyin jo'natuvchidan ayiramiz.
        # Jo'natuvchining mablag'i ayirilmasa, oluvchiga berilgan
        # mablag'ni qaytarishga harakat qilamiz.
        receiver_result = self.add(
            receiver_id,
            currency,
            amount,
            reason="transfer_received",
        )

        try:
            sender_result = self.spend(
                sender_id,
                currency,
                amount,
                reason="transfer_sent",
            )
        except Exception:
            self.spend(
                receiver_id,
                currency,
                amount,
                reason="transfer_rollback",
            )
            raise

        return sender_result, receiver_result

    def claim_daily(
        self,
        user_id: int,
    ) -> EconomyResult:
        """Kunlik bonusni bir marta olishga ruxsat beradi."""

        today = datetime.now(timezone.utc).date().isoformat()

        profile = self.profiles.get_profile(user_id)
        last_claim = profile.__dict__.get("last_daily_claim")

        if last_claim == today:
            raise EconomyError(
                "Bugungi bonusni allaqachon olgansiz."
            )

        reward = self.DAILY_REWARDS["gold"]

        result = self.add(
            user_id=user_id,
            currency="gold",
            amount=reward,
            reason="daily_reward",
        )

        # Profil modelida bu maydon hali mavjud emas.
        # Bonus sanasini profilning qo'shimcha ma'lumotlarida
        # saqlash uchun keyingi bosqichda DB sxemasi kengaytiriladi.
        profile.ability_data = {"last_daily_claim": today} if hasattr(
            profile, "ability_data"
        ) else {}

        return EconomyResult(
            success=result.success,
            user_id=user_id,
            currency="gold",
            amount=reward,
            balance=result.balance,
            message="Kunlik bonus berildi.",
            data={
                "claim_date": today,
                "note": (
                    "Kunlik bonus sanasini bazada saqlash "
                    "uchun qo'shimcha DB ustuni kerak."
                ),
            },
        )

    def purchase(
        self,
        user_id: int,
        item_name: str,
        currency: str,
        price: int,
    ) -> EconomyResult:
        """Buyum xarid qilish uchun to'lovni amalga oshiradi."""

        if not item_name.strip():
            raise EconomyError("Buyum nomi bo'sh bo'lmasligi kerak.")

        result = self.spend(
            user_id=user_id,
            currency=currency,
            amount=price,
            reason=f"item:{item_name}",
        )

        return EconomyResult(
            success=True,
            user_id=user_id,
            currency=result.currency,
            amount=result.amount,
            balance=result.balance,
            message=f"{item_name} uchun to'lov bajarildi.",
            data={"item_name": item_name},
        )

    @classmethod
    def _validate_currency(cls, currency: str) -> str:
        currency = currency.lower().strip()

        if currency not in cls.CURRENCIES:
            raise EconomyError(
                "Valyuta gold, coin yoki diamond bo'lishi kerak."
            )

        return currency

    @staticmethod
    def _validate_amount(amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise EconomyError("Miqdor butun son bo'lishi kerak.")

        if amount <= 0:
            raise EconomyError("Miqdor noldan katta bo'lishi kerak.")


def create_economy(
    profiles: PlayerProfileManager,
    creator_id: int,
) -> Economy:
    return Economy(
        profiles=profiles,
        creator_id=creator_id,
      )
      
