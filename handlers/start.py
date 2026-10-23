
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import ensure_user, get_user
from keyboards import main_menu
from locales import get_text

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    if message.from_user is None:
        return

    user = message.from_user

    await ensure_user(
        database_path="data/throne.db",
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
    )

    profile = await get_user("data/throne.db", user.id)
    language = profile["language"] if profile else "uz"

    welcome = (
        "👑 <b>THRONE olamiga xush kelibsiz!</b>\n\n"
        "🏰 Bu yerda sizni strategiya, sirlar va qirollik uchun "
        "kurashlar kutmoqda.\n\n"
        "⚔️ Guruhga botni administrator qilib qo‘shing va "
        "<code>/NewGame</code> buyrug‘i bilan o‘yinni boshlang.\n\n"
        "👇 Kerakli bo‘limni menyudan tanlang."
    )

    await message.answer(
        welcome,
        reply_markup=main_menu(language),
    )


@router.message()
async def menu_handler(message: Message) -> None:
    if message.from_user is None or not message.text:
        return

    user = message.from_user
    profile = await get_user("data/throne.db", user.id)
    language = profile["language"] if profile else "uz"

    text = message.text.strip()

    if text == get_text("play", language):
        await message.answer(get_text("how_to_play", language))

    elif text == get_text("profile", language):
        if profile is None:
            await ensure_user(
                database_path="data/throne.db",
                user_id=user.id,
                username=user.username,
                first_name=user.first_name or "",
            )
            profile = await get_user("data/throne.db", user.id)

        if profile:
            profile_text = (
                "👤 <b>SHAXSIY KABINET</b>\n\n"
                f"🪙 Oltin: <b>{profile['oltin']}</b>\n"
                f"💎 Almaz: <b>{profile['almaz']}</b>\n"
                f"🪙 Koin: <b>{profile['koin']}</b>\n"
                f"⭐ Daraja: <b>{profile['level']}</b>\n"
                f"✨ Tajriba: <b>{profile['xp']} XP</b>"
            )
            await message.answer(profile_text)

    elif text == get_text("shop", language):
        await message.answer(get_text("shop", language))

    elif text == get_text("language", language):
        from keyboards import language_menu

        await message.answer(
            "🌍 <b>Tilni tanlang:</b>",
            reply_markup=language_menu(),
        )

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
        await message.answer(
            "🎁 <b>KUNLIK BONUS</b>\n\n"
            "Bonus olish tizimi tez orada ishga tushadi. 👑"
        )
        
