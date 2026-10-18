
import logging

from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from game_engine import GamePhase
from game_flow import GameFlow
from game_handlers import (
    active_games,
    database,
    is_group_admin,
)
from night_action_handlers import send_night_action_prompts


logger = logging.getLogger("THRONE.day_phase")
router = Router(name="throne_day_phase")


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


async def require_group(message: Message) -> bool:
    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.answer(
            "Bu buyruqni THRONE o'yin guruhida ishlating."
        )
        return False

    return True


async def require_admin(message: Message, bot: Bot) -> bool:
    if not message.from_user:
        return False

    if not await is_group_admin(
        bot,
        message.chat.id,
        message.from_user.id,
    ):
        await message.answer(
            "🔒 Bu buyruq faqat guruh administratori uchun."
        )
        return False

    return True


def voting_keyboard(
    game,
    voter_id: int,
    candidate_ids: set[int] | None = None,
) -> InlineKeyboardMarkup:
    rows = []

    for player in game.alive_players:
        if player.user_id == voter_id:
            continue

        if (
            candidate_ids is not None
            and player.user_id not in candidate_ids
        ):
            continue

        rows.append([
            InlineKeyboardButton(
                text=f"⚔️ {player.name}",
                callback_data=(
                    f"throne_vote:{game.chat_id}:"
                    f"{game.game_id}:{player.user_id}"
                ),
            )
        ])

    if not rows:
        rows.append([
            InlineKeyboardButton(
                text="Nomzodlar mavjud emas",
                callback_data="throne_vote_unavailable",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def publish_voting(
    bot: Bot,
    chat_id: int,
    game,
    revote: bool = False,
) -> None:
    if revote:
        title = (
            "⚖️ <b>THRONE — QAYTA OVOZ BERISH</b>\n\n"
            "Ovozlar teng keldi. Durangdagi nomzodlardan birini tanlang:"
        )

        flow = active_games[chat_id]["flow"]
        candidate_ids = set(flow.voting.revote_candidates)
    else:
        title = (
            "⚖️ <b>THRONE — OVOZ BERISH</b>\n\n"
            "Kimni ovoz bilan chiqarishni tanlang:"
        )
        candidate_ids = None

    delivered = 0

    for voter in game.alive_players:
        keyboard = voting_keyboard(
            game,
            voter.user_id,
            candidate_ids=candidate_ids,
        )

        try:
            await bot.send_message(
                voter.user_id,
                title,
                reply_markup=keyboard,
            )
            delivered += 1
        except Exception:
            logger.info(
                "Ovoz berish xabarini yuborib bo'lmadi: %s",
                voter.user_id,
            )

    if revote:
        await bot.send_message(
            chat_id,
            "⚖️ Qayta ovoz berish boshlandi. "
            f"Shaxsiy xabar yuborilgan o'yinchilar: {delivered}.",
        )
    else:
        await bot.send_message(
            chat_id,
            "⚖️ Ovoz berish boshlandi. "
            "Ovoz berish tugmalari o'yinchilarga shaxsiy xabarda yuborildi.\n"
            "Natijani hisoblash uchun administrator /endvote buyrug'ini ishlatadi.",
        )


@router.message(Command("discussion"))
async def start_discussion(message: Message, bot: Bot) -> None:
    if not await require_group(message):
        return

    if not await require_admin(message, bot):
        return

    session = get_session(message.chat.id)

    if session is None:
        await message.answer("❌ Bu guruhda faol o'yin topilmadi.")
        return

    game = session["game"]

    if game.phase != GamePhase.DAY:
        await message.answer(
            "Muhokamani boshlash uchun avval tong bosqichi bo'lishi kerak."
        )
        return

    flow = session["flow"]
    result = flow.begin_discussion()

    if not result.success:
        await message.answer(f"❌ {result.message}")
        return

    session["phase"] = game.phase.value

    try:
        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
        )
        await database.add_history(
            game.game_id,
            "DISCUSSION_STARTED",
            "Muhokama boshlandi.",
        )
    except Exception:
        logger.exception("Muhokama holatini bazaga yozishda xatolik")

    await message.answer(
        "💬 <b>THRONE — MUHOKAMA</b>\n\n"
        "O'yinchilar guruhda fikrlarini bildirishi mumkin.\n"
        "Muhokama tugagach, administrator /vote buyrug'ini ishlatadi."
    )


@router.message(Command("vote"))
async def start_vote(message: Message, bot: Bot) -> None:
    if not await require_group(message):
        return

    if not await require_admin(message, bot):
        return

    session = get_session(message.chat.id)

    if session is None:
        await message.answer("❌ Bu guruhda faol o'yin topilmadi.")
        return

    game = session["game"]
    flow = session["flow"]

    result = flow.begin_voting()

    if not result.success:
        await message.answer(f"❌ {result.message}")
        return

    session["phase"] = game.phase.value

    try:
        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
        )
        await database.add_history(
            game.game_id,
            "VOTING_STARTED",
            "Ovoz berish boshlandi.",
        )
    except Exception:
        logger.exception("Ovoz berishni bazaga yozishda xatolik")

    await publish_voting(
        bot=bot,
        chat_id=message.chat.id,
        game=game,
    )


@router.callback_query(
    lambda query: (
        query.data is not None
        and query.data.startswith("throne_vote:")
    )
)
async def cast_vote_callback(query: CallbackQuery) -> None:
    if not query.from_user or not query.data:
        await query.answer(
            "Ovoz ma'lumotlari topilmadi.",
            show_alert=True,
        )
        return

    parts = query.data.split(":")

    if len(parts) != 4:
        await query.answer(
            "Noto'g'ri ovoz tugmasi.",
            show_alert=True,
        )
        return

    _, chat_text, game_id, target_text = parts

    try:
        chat_id = int(chat_text)
        target_id = int(target_text)
    except ValueError:
        await query.answer(
            "O'yinchi identifikatori noto'g'ri.",
            show_alert=True,
        )
        return

    session = get_session(chat_id)

    if session is None:
        await query.answer(
            "Faol o'yin topilmadi.",
            show_alert=True,
        )
        return

    game = session["game"]

    if game.game_id != game_id:
        await query.answer(
            "Bu tugma boshqa o'yinga tegishli.",
            show_alert=True,
        )
        return

    if game.phase != GamePhase.VOTING:
        await query.answer(
            "Hozir ovoz berish faol emas.",
            show_alert=True,
        )
        return

    flow = session["flow"]
    result = flow.cast_vote(
        query.from_user.id,
        target_id,
    )

    if not result.success:
        await query.answer(
            result.message,
            show_alert=True,
        )
        return

    await query.answer("✅ Ovozingiz qabul qilindi.")

    try:
        await database.add_history(
            game.game_id,
            "VOTE_CAST",
            f"{query.from_user.id} ovoz berdi.",
        )
    except Exception:
        logger.exception("Ovoz tarixini saqlashda xatolik")


@router.message(Command("endvote"))
async def end_vote(message: Message, bot: Bot) -> None:
    if not await require_group(message):
        return

    if not await require_admin(message, bot):
        return

    chat_id = message.chat.id
    session = get_session(chat_id)

    if session is None:
        await message.answer("❌ Bu guruhda faol o'yin topilmadi.")
        return

    game = session["game"]
    flow = session["flow"]

    result = flow.resolve_voting()

    if not result.success:
        await message.answer(f"❌ {result.message}")
        return

    session["phase"] = game.phase.value

    if (
        result.voting_result
        and result.voting_result.revote_required
    ):
        try:
            await database.add_history(
                game.game_id,
                "REVOTE_STARTED",
                "Ovozlar teng kelgani uchun qayta ovoz boshlandi.",
            )
        except Exception:
            logger.exception(
                "Qayta ovoz tarixini saqlashda xatolik"
            )

        await message.answer(
            "⚖️ <b>Ovozlar teng keldi!</b>\n\n"
            "Durangdagi nomzodlar o'rtasida qayta ovoz beriladi."
        )

        await publish_voting(
            bot=bot,
            chat_id=chat_id,
            game=game,
            revote=True,
        )
        return

    vote_result = result.voting_result

    if (
        vote_result
        and vote_result.eliminated_id is not None
    ):
        player = game.players.get(
            vote_result.eliminated_id
        )

        try:
            await database.update_game_player(
                game.game_id,
                vote_result.eliminated_id,
                alive=False,
            )
            await database.update_game(
                game.game_id,
                phase=game.phase.value,
                round_number=game.round_number,
            )
            await database.add_history(
                game.game_id,
                "VOTING_RESOLVED",
                result.message,
            )
        except Exception:
            logger.exception(
                "Ovoz natijasini saqlashda xatolik"
            )

        await message.answer(
            "⚖️ <b>THRONE — OVOZ NATIJASI</b>\n\n"
            f"💀 {player.name if player else 'O‘yinchi'} "
            "ovoz natijasida chiqarildi.\n\n"
            "⚠️ Oxirgi so'z bosqichi hali ulanmagan. "
            "Keyingi bosqichda uni qo'shamiz."
        )
        return

    await message.answer(
        "⚖️ <b>THRONE — OVOZ NATIJASI</b>\n\n"
        f"{result.message}"
    )

    if (
        result.victory_result
        and result.victory_result.finished
    ):
        await message.answer(
            "🏆 <b>O'YIN YAKUNLANDI</b>\n\n"
            f"{result.victory_result.message}"
        )
        return

    try:
        await database.update_game(
            game.game_id,
            phase=game.phase.value,
            round_number=game.round_number,
        )
        await database.add_history(
            game.game_id,
            "VOTING_RESOLVED",
            result.message,
        )
    except Exception:
        logger.exception(
            "Ovoz natijasini bazaga yozishda xatolik"
        )

    if game.phase == GamePhase.NIGHT:
        await message.answer(
            f"🌙 <b>{game.round_number}-tun boshlandi.</b>\n"
            "Tungi harakatlar shaxsiy xabarda yuboriladi."
        )

        await send_night_action_prompts(
            bot=bot,
            game_id=game.game_id,
        )
        
