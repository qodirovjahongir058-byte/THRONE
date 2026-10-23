
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from locales import LANGUAGES, get_text


DAILY_BONUS_LABELS = {
    "uz": "🎁 Kunlik bonus",
    "ru": "🎁 Ежедневный бонус",
    "en": "🎁 Daily bonus",
    "tr": "🎁 Günlük bonus",
    "ar": "🎁 المكافأة اليومية",
    "ky": "🎁 Күнүмдүк бонус",
    "kk": "🎁 Күнделікті бонус",
    "tg": "🎁 Бонуси ҳаррӯза",
    "fr": "🎁 Bonus quotidien",
    "de": "🎁 Tagesbonus",
    "es": "🎁 Bono diario",
    "az": "🎁 Gündəlik bonus",
    "pt": "🎁 Bônus diário",
    "it": "🎁 Bonus giornaliero",
    "zh": "🎁 每日奖励",
    "ja": "🎁 デイリーボーナス",
    "ko": "🎁 일일 보너스",
    "hi": "🎁 दैनिक बोनस",
    "id": "🎁 Bonus harian",
    "uk": "🎁 Щоденний бонус",
}


def main_menu(language: str = "uz") -> ReplyKeyboardMarkup:
    """Create the main menu, including the daily bonus button."""
    daily_bonus = DAILY_BONUS_LABELS.get(
        language,
        DAILY_BONUS_LABELS["uz"],
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("play", language)),
                KeyboardButton(text=get_text("profile", language)),
            ],
            [
                KeyboardButton(text=get_text("shop", language)),
                KeyboardButton(text=daily_bonus),
            ],
            [
                KeyboardButton(text=get_text("language", language)),
                KeyboardButton(text=get_text("how_to_play", language)),
            ],
            [
                KeyboardButton(text=get_text("roles", language)),
                KeyboardButton(text=get_text("clan", language)),
            ],
            [
                KeyboardButton(text=get_text("ratings", language)),
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
        raise ValueError(
            "action bo‘sh bo‘lmasligi yoki ':' saqlamasligi kerak"
        )

    yes_text = {
        "uz": "✅ Ha",
        "ru": "✅ Да",
        "en": "✅ Yes",
    }.get(language, "✅ Ha")

    no_text = {
        "uz": "❌ Yo‘q",
        "ru": "❌ Нет",
        "en": "❌ No",
    }.get(language, "❌ Yo‘q")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=yes_text,
                    callback_data=f"confirm:{action}",
                ),
                InlineKeyboardButton(
                    text=no_text,
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
        raise ValueError(
            "Klan egasining ID raqami musbat bo‘lishi kerak"
        )

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
    
