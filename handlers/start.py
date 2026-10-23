
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from config import load_config
from database import (
    claim_daily_bonus,
    ensure_user,
    get_user,
    set_language,
)
from keyboards import language_menu, main_menu
from locales import get_text, LANGUAGES

router = Router()


def database_path() -> str:
    return load_config().database_path


async def get_or_create_user(message: Message) -> dict | None:
    if message.from_user is None:
        return None

    user = message.from_user
    db_path = database_path()

    await ensure_user(
        database_path=db_path,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
    )
    return await get_user(db_path, user.id)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    profile = await get_or_create_user(message)
    if profile is None:
        return

    language = profile["language"] or "uz"

    welcome = (
        "👑 <b>THRONE olamiga xush kelibsiz!</b>\n\n"
        "🏰 Sizni strategiya, sirlar va qirollik uchun kurashlar kutmoqda.\n\n"
        "⚔️ Guruhga botni administrator qilib qo‘shing va "
        "<code>/NewGame</code> buyrug‘i bilan o‘yinni boshlang.\n\n"
        "👇 Kerakli bo‘limni menyudan tanlang."
    )

    await message.answer(
        welcome,
        reply_markup=main_menu(language),
    )


@router.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or not callback.data:
        await callback.answer()
        return

    language = callback.data.split(":", 1)[1]

    if language not in LANGUAGES:
        await callback.answer("Noto‘g‘ri til tanlandi.", show_alert=True)
        return

    db_path = database_path()
    user = callback.from_user

    await ensure_user(
        database_path=db_path,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
    )

    updated = await set_language(db_path, user.id, language)

    if not updated:
        await callback.answer(
            "Tilni saqlab bo‘lmadi. Qayta urinib ko‘ring.",
            show_alert=True,
        )
        return

    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            get_text("language", language),
            reply_markup=main_menu(language),
        )

    await callback.answer("🌍 Til saqlandi!")


@router.message(F.text, ~F.text.startswith("/"))
async def menu_handler(message: Message) -> None:
    if message.from_user is None or not message.text:
        return

    profile = await get_or_create_user(message)
    if profile is None:
        return

    language = profile["language"] or "uz"
    text = message.text.strip()

    if text == get_text("profile", language):
        await message.answer(
            "👑 <b>SHAXSIY KABINET</b>\n\n"
            f"🪙 Oltin: <b>{profile['oltin']}</b>\n"
            f"💎 Almaz: <b>{profile['almaz']}</b>\n"
            f"🪙 Koin: <b>{profile['koin']}</b>\n"
            f"⭐ Daraja: <b>{profile['level']}</b>\n"
            f"✨ Tajriba: <b>{profile['xp']} XP</b>"
        )

    elif text == get_text("language", language):
        await message.answer(
            "🌍 <b>Tilni tanlang:</b>",
            reply_markup=language_menu(),
        )

    elif text == get_text("play", language):
        await message.answer(get_text("how_to_play", language))

    elif text == get_text("shop", language):
        await message.answer(get_text("shop", language))

    elif text == get_text("how_to_play", language):
        await message.answer(get_text("how_to_play", language))

    elif text == get_text("roles", language):
        await message.answer(get_text("roles", language))

    elif text == get_text("clan", language):
        await message.answer(get_text("clan", language))

    elif text == get_text("ratings", language):
        await message.answer(get_text("ratings", language))

    elif text == get_text("help", language):
        await message.answer(get_text("help", language))

    elif text in ("🎁 Kunlik bonus", "🎁 Daily bonus"):
        result = await claim_daily_bonus(
            database_path(),
            message.from_user.id,
        )

        if not result["ok"]:
            if result["reason"] == "already_claimed":
                await message.answer(
                    "🎁 <b>BUGUNGI BONUS OLINGAN!</b>\n\n"
                    "👑 Siz bugungi mukofotingizni olib bo‘lgansiz. "
                    "Ertaga yana keling!"
                )
            else:
                await message.answer(
                    "⚠️ Bonusni olishda xatolik yuz berdi. "
                    "Iltimos, qayta urinib ko‘ring."
                )
            return

        await message.answer(
            "🎁 <b>KUNLIK BONUS OLINDI!</b>\n\n"
            f"🗓️ Ketma-ket kun: <b>{result['day']}/7</b>\n"
            f"🪙 Oltin: <b>+{result['oltin']}</b>\n"
            f"✨ Tajriba: <b>+{result['xp']} XP</b>\n\n"
            "👑 Ertaga yana kelib, keyingi mukofotni oling!"
                          )
        
