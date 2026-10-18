
import asyncio
import logging

from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from game_engine import GamePhase
from game_handlers import active_games, database
from game_flow import GameFlow
from night_action_handlers import send_night_action_prompts


logger = logging.getLogger("THRONE.last_words")
router = Router(name="throne_last_words")

LAST_WORDS_DURATION = 30


def get_session(chat_id: int) -> dict | None:
    session = active_games.get(chat_id)

    if not session or session.get("game") is None:
        return None

    game = session["game"]
    flow = session.get("flow")

    if flow is None or flow.game is not game:
        flow = GameFlow(game)
        session["flow"] = flow

    return session


async def finish_last_words(
    bot: Bot,
    chat_id: int,
    game_id: str,
) -> None:
    await asyncio.sleep(LAST_WORDS_DURATION)

    session = get_session(chat_id)

    if session is None:
        return

    game = session["game"]

    if (
        game.game_id != game_id
        or game.phase != GamePhase.LAST_WORDS
    ):
        return

    flow = session["flow"]
    result = flow.finish_last_words()

    if not result.success:
        logger.warning(
            "Oxirgi so'z bosqichini tugatib bo'lmadi: %s",
            result.message,
        )
        return

    session["phase"] = game.phase.value
    finished = game.phase == GamePhase.FINISHED

    try:
        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
            winner=game.winner if finished else None,
            finished=finished,
        )

        await database.add_history(
            game.game_id,
            "GAME_FINISHED" if finished else "LAST_WORDS_FINISHED",
            result.message,
        )
    except Exception:
        logger.exception(
            "Oxirgi so'z natijasini bazaga yozishda xatolik"
        )

    if finished:
        await bot.send_message(
            chat_id,
            "🏆 <b>THRONE — O'YIN YAKUNLANDI</b>\n\n"
            f"{result.message}",
        )
        return

    await bot.send_message(
        chat_id,
        "🌙 <b>Oxirgi so'z bosqichi tugadi.</b>\n\n"
        f"{game.round_number + 1}-tun boshlanmoqda.",
    )

    await send_night_action_prompts(
        bot=bot,
        game_id=game.game_id,
    )


@router.message(Command("lastwords"))
async def last_words_status(message: Message) -> None:
    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer(
            "Bu buyruqni o'yin guruhida ishlating."
        )
        return

    session = get_session(message.chat.id)

    if session is None:
        await message.answer("❌ Faol o'yin topilmadi.")
        return

    game = session["game"]

    if game.phase != GamePhase.LAST_WORDS:
        await message.answer(
            "Hozir oxirgi so'z bosqichi faol emas."
        )
        return

    player_id = session["flow"].pending_last_words_player_id
    player = game.players.get(player_id) if player_id else None

    if player is None:
        await message.answer(
            "Oxirgi so'z aytadigan o'yinchi topilmadi."
        )
        return

    await message.answer(
        "🗣 <b>THRONE — OXIRGI SO'Z</b>\n\n"
        f"Navbat: {player.name}\n"
        f"Vaqt: {game.last_words_time_left()} soniya\n\n"
        "Chiqarilgan o'yinchi botga shaxsiy xabar orqali "
        "oxirgi so'zini yozishi mumkin."
    )


@router.message()
async def capture_last_words(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE or not message.from_user:
        return

    for chat_id, session in list(active_games.items()):
        game = session.get("game")

        if game is None or game.phase != GamePhase.LAST_WORDS:
            continue

        flow = session.get("flow")

        if flow is None:
            continue

        if flow.pending_last_words_player_id != message.from_user.id:
            continue

        if game.last_words_time_left() <= 0:
            await message.answer(
                "⏰ Oxirgi so'z uchun ajratilgan vaqt tugadi."
            )
            return

        result = flow.save_last_words(
            message.from_user.id,
            message.text or "",
        )

        if not result.success:
            await message.answer(result.message)
            return

        await message.answer(
            "🗣 Oxirgi so'zingiz saqlandi. Rahmat."
        )

        try:
            await bot.send_message(
                chat_id,
                "🗣 <b>Oxirgi so'z</b>\n\n"
                f"{game.players[message.from_user.id].name}:\n"
                f"{message.text or ''}",
            )

            await database.add_history(
                game.game_id,
                "LAST_WORDS_SAVED",
                f"{message.from_user.id} oxirgi so'zini aytdi.",
            )
        except Exception:
            logger.exception(
                "Oxirgi so'zni guruhga yuborishda xatolik"
            )

        return
    
