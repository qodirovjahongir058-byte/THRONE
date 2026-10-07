from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def lobby_keyboard() -> InlineKeyboardMarkup:
    """Keyboard displayed while the game is waiting for players."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="⚔️ Qo‘shilish",
            callback_data="throne:join",
        ),
        InlineKeyboardButton(
            text="👥 O‘yinchilar",
            callback_data="throne:players",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="👑 O‘yinni boshlash",
            callback_data="throne:start",
        ),
        InlineKeyboardButton(
            text="🛑 Bekor qilish",
            callback_data="throne:stop",
        ),
    )

    return builder.as_markup()


def night_action_keyboard(
    action_buttons: list[tuple[str, str]],
) -> InlineKeyboardMarkup:
    """Build a keyboard for available night actions."""

    builder = InlineKeyboardBuilder()

    for text, callback_data in action_buttons:
        builder.button(
            text=text,
            callback_data=callback_data,
        )

    builder.adjust(2)

    return builder.as_markup()


def target_keyboard(
    targets: list[tuple[int, str]],
    callback_prefix: str,
) -> InlineKeyboardMarkup:
    """Build a keyboard containing alive player targets."""

    builder = InlineKeyboardBuilder()

    for user_id, display_name in targets:
        builder.button(
            text=display_name,
            callback_data=f"{callback_prefix}:{user_id}",
        )

    builder.adjust(1)

    return builder.as_markup()


def voting_keyboard(
    targets: list[tuple[int, str]],
) -> InlineKeyboardMarkup:
    """Build the daytime voting keyboard."""

    builder = InlineKeyboardBuilder()

    for user_id, display_name in targets:
        builder.button(
            text=f"⚖️ {display_name}",
            callback_data=f"throne:vote:{user_id}",
        )

    builder.adjust(1)

    return builder.as_markup()


def last_words_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown during the last-words phase."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🕯️ So‘nggi so‘zim",
            callback_data="throne:last_words",
        ),
    )

    return builder.as_markup()


def confirm_keyboard(
    confirm_callback: str,
    cancel_callback: str,
) -> InlineKeyboardMarkup:
    """Generic confirmation keyboard."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Tasdiqlash",
            callback_data=confirm_callback,
        ),
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data=cancel_callback,
        ),
    )

    return builder.as_markup()


def empty_keyboard() -> InlineKeyboardMarkup:
    """Return an empty inline keyboard."""

    return InlineKeyboardMarkup(
        inline_keyboard=[],
    )
