
import logging

from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from game_engine import GamePhase
from game_flow import GameFlow
from game_handlers import (
    active_games,
    database,
    is_group_admin,
)


logger = logging.getLogger("THRONE.night_resolution")
router = Router(name="throne_night_resolution")


def get_flow(session: dict) -> GameFlow:
    """Faol o'yin uchun bosqich boshqaruvchisini oladi."""
    game = session["game"]
    flow = session.get("flow")

    if flow is None or flow.game is not game:
        flow = GameFlow(game)
        session["flow"] = flow

    return flow


@router.message(Command("endnight"))
async def end_night(message: Message, bot: Bot) -> None:
    """Tun natijalarini hisoblaydi va g'alabani tekshiradi."""

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
        await message.answer("Hozir tun bosqichi emas.")
        return

    flow = get_flow(session)
    result = flow.resolve_night()

    if not result.success:
        await message.answer(
            f"❌ Tun natijalarini hisoblab bo'lmadi: "
            f"{result.message}"
        )
        return

    session["phase"] = game.phase.value

    night_result = result.night_result
    eliminated = night_result.eliminated if night_result else []

    try:
        for user_id in eliminated:
            await database.update_game_player(
                game.game_id,
                user_id,
                alive=False,
            )

        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
            finished=game.phase == GamePhase.FINISHED,
        )

        await database.add_history(
            game.game_id,
            "NIGHT_RESOLVED",
            f"{game.round_number}-tun yakunlandi.",
        )

        if game.phase == GamePhase.FINISHED:
            await database.add_history(
                game.game_id,
                "GAME_FINISHED",
                result.message,
            )

    except Exception:
        logger.exception(
            "Tun natijasini bazaga saqlashda xatolik."
        )

    if game.phase == GamePhase.FINISHED:
        winner = result.victory_result

        await message.answer(
            "🏆 <b>THRONE — O'YIN YAKUNLANDI</b>\n\n"
            f"{winner.message if winner else result.message}"
        )
        return

    lines = [
        "☀️ <b>THRONE — TONG OТDI</b>",
        "",
        f"🌙 <b>{game.round_number}-tun yakunlandi.</b>",
    ]

    if eliminated:
        lines.extend(["", "⚔️ <b>Tungi natijalar:</b>"])

        for user_id in eliminated:
            player = game.players.get(user_id)

            if player:
                lines.append(
                    f"💀 {player.name} o'yindan chiqdi."
                )
    else:
        lines.extend([
            "",
            "🛡 Bu tunda hech kim o'yindan chiqmadi.",
        ])

    if night_result:
        for item in night_result.messages:
            if "omon qoldi" in item or "himoyalandi" in item:
                lines.append(f"🛡 {item}")

    lines.extend([
        "",
        "💬 Tong boshlandi.",
        "Administrator muhokamani boshlash uchun "
        "/discussion buyrug'ini ishlatadi.",
    ])

    await message.answer("\n".join(lines))
    
