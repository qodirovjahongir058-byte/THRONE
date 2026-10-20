
from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramBadRequest,
)

from game_partners import GamePartners, PartnerError
from game_state import GamePhase, GameState, PlayerStatus


logger = logging.getLogger(__name__)


class PrivateMessageError(Exception):
    """Maxfiy xabar yuborishdagi xato."""


@dataclass(frozen=True, slots=True)
class PrivateMessageResult:
    user_id: int
    success: bool
    message: str
    message_id: int | None = None


class GamePrivateMessages:
    """THRONE maxfiy xabarlarini shaxsiy chat orqali yuboradi."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_role(
        self,
        game: GameState,
        user_id: int,
    ) -> PrivateMessageResult:
        """O'yinchiga faqat o'z rolini yuboradi."""

        player = game.get_player(user_id)

        if player is None:
            raise PrivateMessageError(
                "O'yinchi bu o'yinda topilmadi."
            )

        if player.role is None:
            raise PrivateMessageError(
                "O'yinchiga rol hali tayinlanmagan."
            )

        role = player.role

        text = (
            "👑 THRONE — MAXFIY ROL\n\n"
            f"🎭 Rolingiz: {role.name}\n"
            f"🏰 Jamoangiz: "
            f"{player.team.value if player.team else 'Noma’lum'}\n\n"
            f"📜 Tavsif: {role.description}\n"
            f"⚔️ Qobiliyat: {role.ability}\n\n"
            "🔒 Bu ma’lumot faqat siz uchun. "
            "Uni boshqa o‘yinchilarga yubormang."
        )

        return await self._send(user_id, text)

    async def send_partner_info(
        self,
        game: GameState,
        partners: GamePartners,
        user_id: int,
    ) -> PrivateMessageResult:
        """O'yinchiga faqat o'z sheriklari haqida yozadi."""

        try:
            info = partners.get_private_info(user_id)
        except PartnerError as exc:
            raise PrivateMessageError(str(exc)) from exc

        if info.game_id != game.game_id:
            raise PrivateMessageError(
                "Sheriklik ma'lumoti boshqa o'yinga tegishli."
            )

        partner_lines: list[str] = []

        for partner_id in info.partner_ids:
            partner = game.get_player(partner_id)

            if partner is not None:
                partner_lines.append(
                    f"• {partner.full_name} "
                    f"(ID: {partner.user_id})"
                )

        if partner_lines:
            partner_text = "\n".join(partner_lines)
        else:
            partner_text = (
                "Sizga tayinlangan maxfiy sheriklar mavjud emas."
            )

        text = (
            "🔒 THRONE — MAXFIY SHERIKLAR\n\n"
            f"🎮 O'yin ID: {game.game_id}\n"
            f"🏰 Jamoangiz: {info.team}\n\n"
            f"🤝 Sheriklaringiz:\n{partner_text}\n\n"
            "⚠️ Ushbu ma'lumot maxfiy. "
            "Uni guruhga yubormang."
        )

        return await self._send(user_id, text)

    async def send_night_result(
        self,
        game: GameState,
        user_id: int,
        message: str,
    ) -> PrivateMessageResult:
        """Tungi harakat natijasini shaxsiy yuboradi."""

        player = game.get_player(user_id)

        if player is None:
            raise PrivateMessageError("O'yinchi topilmadi.")

        if player.status != PlayerStatus.ALIVE:
            raise PrivateMessageError(
                "Tungi natija faqat tirik o'yinchiga yuboriladi."
            )

        if game.phase not in {
            GamePhase.NIGHT,
            GamePhase.DAY,
            GamePhase.DISCUSSION,
        }:
            raise PrivateMessageError(
                "Hozir tungi natijani yuborish mumkin emas."
            )

        text = (
            "🌙 THRONE — MAXFIY NATIJA\n\n"
            f"{message}\n\n"
            "🔒 Bu xabar faqat siz uchun."
        )

        return await self._send(user_id, text)

    async def send_private_notice(
        self,
        user_id: int,
        heading: str,
        message: str,
    ) -> PrivateMessageResult:
        """Umumiy maxfiy bildirishnoma yuboradi."""

        text = f"👑 THRONE — {heading}\n\n{message}"
        return await self._send(user_id, text)

    async def _send(
        self,
        user_id: int,
        text: str,
    ) -> PrivateMessageResult:
        try:
            sent = await self.bot.send_message(
                chat_id=user_id,
                text=text,
            )

            return PrivateMessageResult(
                user_id=user_id,
                success=True,
                message="Xabar yuborildi.",
                message_id=sent.message_id,
            )

        except TelegramForbiddenError:
            return PrivateMessageResult(
                user_id=user_id,
                success=False,
                message=(
                    "Bot foydalanuvchiga shaxsiy xabar yubora olmadi. "
                    "O'yinchi botni ochib, /start bosishi kerak."
                ),
            )

        except TelegramBadRequest as exc:
            logger.warning(
                "Shaxsiy xabar yuborilmadi: user_id=%s, error=%s",
                user_id,
                exc,
            )

            return PrivateMessageResult(
                user_id=user_id,
                success=False,
                message="Telegram xabarni qabul qilmadi.",
            )

        except TelegramAPIError:
            logger.exception(
                "Telegram API xatosi: user_id=%s",
                user_id,
            )

            return PrivateMessageResult(
                user_id=user_id,
                success=False,
                message="Telegram xizmatida xatolik yuz berdi.",
            )

    async def send_roles_to_all(
        self,
        game: GameState,
    ) -> list[PrivateMessageResult]:
        """Barcha o'yinchilarga rollarini alohida yuboradi."""

        results: list[PrivateMessageResult] = []

        for player in game.players.values():
            if player.status != PlayerStatus.ALIVE:
                continue

            try:
                result = await self.send_role(
                    game,
                    player.user_id,
                )
            except PrivateMessageError as exc:
                result = PrivateMessageResult(
                    user_id=player.user_id,
                    success=False,
                    message=str(exc),
                )

            results.append(result)

        return results


def create_private_message_service(
    bot: Bot,
) -> GamePrivateMessages:
    return GamePrivateMessages(bot)
