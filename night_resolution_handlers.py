
import logging

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from game_handlers import (
    active_games,
    database,
    is_group_admin,
)
from game_engine import GamePhase
from game_resolver import GameResolver


logger = logging.getLogger("THRONE.night_resolution")
router = Router(name="throne_night_resolution")


@router.message(Command("endnight"))
async def end_night(message: Message, bot) -> None:
    """Tun natijalarini hisoblab, tongni boshlaydi."""

    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer(
            "Bu buyruqni o'yin guruhida ishlating."
        )
        return

    if not message.from_user:
        return

    if not await is_group_admin(
        bot,
        message.chat.id,
        message.from_user.id,
    ):
        await message.answer(
            "🔒 Bu buyruq faqat guruh administratori uchun."
        )
        return

    session = active_games.get(message.chat.id)

    if not session or session.get("game") is None:
        await message.answer(
            "❌ Bu guruhda faol o'yin topilmadi."
        )
        return

    game = session["game"]

    if game.phase != GamePhase.NIGHT:
        await message.answer(
            "Hozir tun bosqichi emas."
        )
        return

    result = GameResolver.resolve_night(game)

    if not result.success:
        await message.answer(
            "❌ Tungi harakatlarni hisoblab bo'lmadi."
        )
        return

    success, day_message = game.begin_day()

    if not success:
        await message.answer(
            "❌ Tong bosqichini boshlashda xatolik."
        )
        return

    session["phase"] = game.phase.value
    session["game"] = game

    try:
        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
        )

        for user_id in result.eliminated:
            await database.update_game_player(
                game.game_id,
                user_id,
                alive=False,
            )

        await database.add_history(
            game.game_id,
            "NIGHT_RESOLVED",
            f"{game.round_number}-tun yakunlandi.",
        )

    except Exception:
        logger.exception(
            "Tun natijasini bazaga yozishda xatolik."
        )

    lines = [
        "☀️ <b>THRONE — TONG OТDI</b>",
        "",
        f"🌙 <b>{game.round_number}-tun yakunlandi.</b>",
    ]

    if result.eliminated:
        lines.extend(["", "⚔️ <b>Tungi natijalar:</b>"])

        for user_id in result.eliminated:
            player = game.players.get(user_id)
            if player:
                lines.append(f"💀 {player.name} o'yindan chiqdi.")
    else:
        lines.extend([
            "",
            "🛡 Bu tunda hech kim o'yindan chiqmadi.",
        ])

    for item in result.messages:
        if "omon qoldi" in item or "himoyalandi" in item:
            lines.append(f"🛡 {item}")

    lines.extend([
        "",
        "💬 Endi guruhda muhokama boshlanishi mumkin.",
        "Keyingi bosqichlarni ulash hali davom etadi.",
    ])

    await message.answer("\n".join(lines))
