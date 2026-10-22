
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from locales import LANGUAGES, get_text


def main_menu(language: str = "uz") -> ReplyKeyboardMarkup:
    """Create the main menu shown below the message."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("play", language)),
                KeyboardButton(text=get_text("profile", language)),
            ],
            [
                KeyboardButton(text=get_text("shop", language)),
                KeyboardButton(text=get_text("language", language)),
            ],
            [
                KeyboardButton(text=get_text("how_to_play", language)),
                KeyboardButton(text=get_text("roles", language)),
            ],
            [
                KeyboardButton(text=get_text("clan", language)),
                KeyboardButton(text=get_text("ratings", language)),
            ],
            [
                KeyboardButton(text=get_text("help", language)),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("play", language),
    )


def language_menu() -> InlineKeyboardMarkup:
    """Create buttons for all 20 supported languages."""
    buttons = [
        InlineKeyboardButton(
            text=name,
            callback_data=f"lang:{code}",
        )
        for code, name in LANGUAGES.items()
    ]

    rows = [
        buttons[index:index + 2]
        for index in range(0, len(buttons), 2)
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard(
    action: str,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for a supported action."""
    if not action or ":" in action:
        raise ValueError("action bo‘sh bo‘lmasligi yoki ':' saqlamasligi kerak")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data=f"confirm:{action}",
                ),
                InlineKeyboardButton(
                    text="❌ Yo‘q",
                    callback_data=f"cancel:{action}",
                ),
            ]
        ]
    )


def clan_exit_keyboard() -> InlineKeyboardMarkup:
    """Create the button used to leave a clan."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚪 Klandan chiqish",
                    callback_data="clan:leave",
                )
            ]
        ]
    )


def clan_join_keyboard(
    clan_owner_id: int,
) -> InlineKeyboardMarkup:
    """Create a join button for a clan owner's invitation."""
    if clan_owner_id <= 0:
        raise ValueError("Klan egasining ID raqami musbat bo‘lishi kerak")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛡️ Klaniga qo‘shilish",
                    callback_data=f"clan:join:{clan_owner_id}",
                )
            ]
        ]
    )
    
