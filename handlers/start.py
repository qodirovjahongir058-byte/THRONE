from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    first_name = message.from_user.first_name or "Sarkarda"

    await message.answer(
        f"👑 <b>THRONE</b>\n\n"
        f"Xush kelibsiz, <b>{first_name}</b>!\n\n"
        "Bu yerda qirolliklar, saroylar, ittifoqlar "
        "va yashirin kurashlar boshlanadi.\n\n"
        "⚔️ <i>Taxt uchun kurash boshlanmoqda...</i>"
    )
