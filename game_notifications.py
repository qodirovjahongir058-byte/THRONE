
from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NotificationResult:
    chat_id: int
    success: bool
    message: str
    message_id: int | None = None


class GameNotifications:
    """THRONE o'yini uchun guruh bildirishnomalari."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def _send(
        self,
        chat_id: int,
        text: str,
    ) -> NotificationResult:
        try:
            sent = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
            )
            return NotificationResult(
                chat_id=chat_id,
                success=True,
                message="Bildirishnoma yuborildi.",
                message_id=sent.message_id,
            )
        except TelegramAPIError as exc:
            logger.warning(
                "Bildirishnoma yuborilmadi: chat_id=%s, error=%s",
                chat_id,
                exc,
            )
            return NotificationResult(
                chat_id=chat_id,
                success=False,
                message="Telegram xabarni yubora olmadi.",
            )

    async def lobby_created(
        self,
        chat_id: int,
        creator_name: str,
        game_id: str,
        min_players: int = 7,
        max_players: int = 50,
        duration_minutes: int = 20,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "👑 THRONE — YANGI O'YIN!\n\n"
                f"🏰 Yaratgan: {creator_name}\n"
                f"👥 O'yinchilar: 1/{max_players}\n"
                f"⚔️ Kerakli o'yinchilar: kamida {min_players}\n"
                f"⏳ Ro'yxatdan o'tish: {duration_minutes} daqiqa\n\n"
                "Qatnashish: /join\n"
                "Chiqish: /leave\n"
                f"🎮 O'yin ID: {game_id}"
            ),
        )

    async def player_joined(
        self,
        chat_id: int,
        player_name: str,
        player_count: int,
        max_players: int = 50,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                f"⚔️ {player_name} o'yinga qo'shildi!\n"
                f"👥 O'yinchilar: {player_count}/{max_players}"
            ),
        )

    async def player_left(
        self,
        chat_id: int,
        player_name: str,
        player_count: int,
        max_players: int = 50,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                f"🚪 {player_name} lobbydan chiqdi.\n"
                f"👥 O'yinchilar: {player_count}/{max_players}"
            ),
        )

    async def game_started(
        self,
        chat_id: int,
        player_count: int,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "👑 THRONE — O'YIN BOSHLANDI!\n\n"
                f"⚔️ O'yinchilar: {player_count}\n"
                "🔒 Rollar shaxsiy xabarda yuboriladi.\n"
                "🌙 Birinchi tun boshlandi!"
            ),
        )

    async def night_started(
        self,
        chat_id: int,
        round_number: int,
        duration_seconds: int = 90,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                f"🌙 {round_number}-TUN\n\n"
                f"⏳ Vaqt: {duration_seconds} soniya.\n"
                "Maxfiy harakatlaringizni bot orqali bajaring."
            ),
        )

    async def day_started(
        self,
        chat_id: int,
        round_number: int,
        duration_seconds: int = 120,
        public_result: str | None = None,
    ) -> NotificationResult:
        text = (
            f"☀️ {round_number}-KUN BOSHLANDI!\n\n"
            f"🗣️ Muhokama vaqti: {duration_seconds} soniya."
        )
        if public_result:
            text += f"\n\n📜 Natija:\n{public_result}"
        return await self._send(chat_id, text)

    async def discussion_started(
        self,
        chat_id: int,
        duration_seconds: int = 120,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "🗣️ MUHOKAMA BOSHLANDI!\n\n"
                f"⏳ Sizda {duration_seconds} soniya bor."
            ),
        )

    async def voting_started(
        self,
        chat_id: int,
        duration_seconds: int = 60,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "⚖️ OVOZ BERISH BOSHLANDI!\n\n"
                f"⏳ Ovoz berish vaqti: {duration_seconds} soniya."
            ),
        )

    async def voting_result(
        self,
        chat_id: int,
        result_text: str,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            f"⚖️ OVOZ BERISH NATIJASI\n\n{result_text}",
        )

    async def last_words_started(
        self,
        chat_id: int,
        player_name: str,
        duration_seconds: int = 30,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "🗣️ OXIRGI SO'Z\n\n"
                f"{player_name}, so'nggi fikringizni ayting.\n"
                f"⏳ Vaqt: {duration_seconds} soniya."
            ),
        )

    async def player_eliminated(
        self,
        chat_id: int,
        player_name: str,
        public_message: str | None = None,
    ) -> NotificationResult:
        text = f"⚔️ {player_name} o'yindan chiqdi."
        if public_message:
            text += f"\n\n{public_message}"
        return await self._send(chat_id, text)

    async def game_finished(
        self,
        chat_id: int,
        winner_name: str,
        reason: str | None = None,
    ) -> NotificationResult:
        text = (
            "🏆 THRONE — O'YIN YAKUNLANDI!\n\n"
            f"👑 G'olib: {winner_name}"
        )
        if reason:
            text += f"\n📜 Sabab: {reason}"
        text += "\n\nYangi o'yinda yana uchrashamiz!"
        return await self._send(chat_id, text)

    async def timer_warning(
        self,
        chat_id: int,
        phase_name: str,
        remaining_seconds: int,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            f"⏳ {phase_name}: {remaining_seconds} soniya qoldi!",
        )

    async def lobby_cancelled(
        self,
        chat_id: int,
        reason: str,
    ) -> NotificationResult:
        return await self._send(
            chat_id,
            (
                "🚫 THRONE LOBBY BEKOR QILINDI.\n\n"
                f"📜 Sabab: {reason}"
            ),
        )


def create_notifications(bot: Bot) -> GameNotifications:
    return GameNotifications(bot)
