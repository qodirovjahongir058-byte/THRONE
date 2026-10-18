from typing import Final

DEFAULT_LANGUAGE: Final[str] = "uz"

SUPPORTED_LANGUAGES: Final[dict[str, dict[str, str]]] = {
    "uz": {"name": "O‘zbekcha", "flag": "🇺🇿"},
    "ru": {"name": "Русский", "flag": "🇷🇺"},
    "en": {"name": "English", "flag": "🇬🇧"},
    "tr": {"name": "Türkçe", "flag": "🇹🇷"},
    "ar": {"name": "العربية", "flag": "🇸🇦"},
    "ky": {"name": "Кыргызча", "flag": "🇰🇬"},
    "kk": {"name": "Қазақша", "flag": "🇰🇿"},
    "az": {"name": "Azərbaycanca", "flag": "🇦🇿"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "ko": {"name": "한국어", "flag": "🇰🇷"},
    "ja": {"name": "日本語", "flag": "🇯🇵"},
    "zh": {"name": "中文", "flag": "🇨🇳"},
    "hi": {"name": "हिन्दी", "flag": "🇮🇳"},
    "ur": {"name": "اردو", "flag": "🇵🇰"},
    "fa": {"name": "فارسی", "flag": "🇮🇷"},
    "tg": {"name": "Тоҷикӣ", "flag": "🇹🇯"},
    "tk": {"name": "Türkmençe", "flag": "🇹🇲"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "it": {"name": "Italiano", "flag": "🇮🇹"},
}


# Asosiy matnlar barcha tillarda shu lug'at orqali olinadi.
COMMON_TEXTS: Final[dict[str, dict[str, str]]] = {
    "uz": {
        "welcome": "👑 THRONE — Taxtlar olamiga xush kelibsiz!",
        "choose_language": "🌐 O‘zingizga qulay tilni tanlang:",
        "language_saved": "✅ Til muvaffaqiyatli o‘zgartirildi.",
        "main_menu": "🏰 Asosiy menyu",
        "new_game": "⚔️ Yangi o‘yin",
        "join_game": "👥 O‘yinga qo‘shilish",
        "start_game": "👑 O‘yinni boshlash",
        "profile": "👤 Profil",
        "settings": "⚙️ Sozlamalar",
        "language": "🌐 Tilni o‘zgartirish",
        "help": "📜 Yordam",
        "game_not_found": "❌ Faol o‘yin topilmadi.",
        "already_joined": "✅ Siz allaqachon o‘yindasiz.",
        "joined_game": "⚔️ Siz o‘yinga qo‘shildingiz!",
        "game_started": "👑 O‘yin boshlandi!",
        "not_enough_players": "❌ O‘yin uchun kamida 7 o‘yinchi kerak.",
        "night": "🌙 Tun tushdi. Maxfiy harakatlar vaqti.",
        "day": "☀️ Tong otdi. Qirollik uyg‘ondi.",
        "discussion": "💬 Muhokama boshlandi.",
        "voting": "🗳 Ovoz berish boshlandi.",
        "last_words": "📜 So‘nggi so‘zlar vaqti: 30 soniya.",
        "player_eliminated": "⚔️ O‘yinchi o‘yindan chiqarildi.",
        "victory": "🏆 G‘olib aniqlanmoqda...",
        "not_your_turn": "⏳ Hozir sizning navbatingiz emas.",
        "action_success": "✅ Harakatingiz qabul qilindi.",
        "action_failed": "❌ Harakatni bajarib bo‘lmadi.",
        "profile_title": "👤 Sizning profilingiz",
        "gold": "🪙 Oltin",
        "coin": "🟡 Tanga",
        "diamond": "💎 Olmos",
        "unknown_command": "❓ Buyruq tushunilmadi.",
    },
    "ru": {
        "welcome": "👑 Добро пожаловать в THRONE!",
        "choose_language": "🌐 Выберите язык:",
        "language_saved": "✅ Язык изменён.",
        "main_menu": "🏰 Главное меню",
        "new_game": "⚔️ Новая игра",
        "join_game": "👥 Присоединиться",
        "start_game": "👑 Начать игру",
        "profile": "👤 Профиль",
        "settings": "⚙️ Настройки",
        "language": "🌐 Изменить язык",
        "help": "📜 Помощь",
        "game_not_found": "❌ Активная игра не найдена.",
        "already_joined": "✅ Вы уже в игре.",
        "joined_game": "⚔️ Вы присоединились!",
        "game_started": "👑 Игра началась!",
        "not_enough_players": "❌ Нужно минимум 7 игроков.",
        "night": "🌙 Наступила ночь.",
        "day": "☀️ Наступило утро.",
        "discussion": "💬 Началось обсуждение.",
        "voting": "🗳 Началось голосование.",
        "last_words": "📜 Последние слова: 30 секунд.",
        "player_eliminated": "⚔️ Игрок выбыл.",
        "victory": "🏆 Определяем победителя...",
        "not_your_turn": "⏳ Сейчас не ваш ход.",
        "action_success": "✅ Действие принято.",
        "action_failed": "❌ Не удалось выполнить действие.",
        "profile_title": "👤 Ваш профиль",
        "gold": "🪙 Золото",
        "coin": "🟡 Монеты",
        "diamond": "💎 Алмазы",
        "unknown_command": "❓ Неизвестная команда.",
    },
    "en": {
        "welcome": "👑 Welcome to THRONE!",
        "choose_language": "🌐 Choose your language:",
        "language_saved": "✅ Language changed.",
        "main_menu": "🏰 Main menu",
        "new_game": "⚔️ New game",
        "join_game": "👥 Join game",
        "start_game": "👑 Start game",
        "profile": "👤 Profile",
        "settings": "⚙️ Settings",
        "language": "🌐 Change language",
        "help": "📜 Help",
        "game_not_found": "❌ No active game found.",
        "already_joined": "✅ You are already in the game.",
        "joined_game": "⚔️ You joined the game!",
        "game_started": "👑 The game has started!",
        "not_enough_players": "❌ At least 7 players are required.",
        "night": "🌙 Night has fallen.",
        "day": "☀️ Dawn has arrived.",
        "discussion": "💬 Discussion has started.",
        "voting": "🗳 Voting has started.",
        "last_words": "📜 Last words: 30 seconds.",
        "player_eliminated": "⚔️ A player was eliminated.",
        "victory": "🏆 Determining the winner...",
        "not_your_turn": "⏳ It is not your turn.",
        "action_success": "✅ Action accepted.",
        "action_failed": "❌ Action failed.",
        "profile_title": "👤 Your profile",
        "gold": "🪙 Gold",
        "coin": "🟡 Coins",
        "diamond": "💎 Diamonds",
        "unknown_command": "❓ Unknown command.",
    },
}


# Qolgan tillar uchun vaqtinchalik asosiy til matnlari.
# Har bir tarjima keyinchalik o'z tiliga to'ldiriladi.
LANGUAGE_FALLBACKS: Final[dict[str, str]] = {
    "tr": "en",
    "ar": "en",
    "ky": "uz",
    "kk": "uz",
    "az": "tr",
    "de": "en",
    "es": "en",
    "ko": "en",
    "ja": "en",
    "zh": "en",
    "hi": "en",
    "ur": "en",
    "fa": "en",
    "tg": "ru",
    "tk": "tr",
    "fr": "en",
    "it": "en",
}


def get_text(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Matnni tanlangan tilda yoki zaxira tilda qaytaradi."""
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE

    if key in COMMON_TEXTS.get(language, {}):
        return COMMON_TEXTS[language][key]

    fallback = LANGUAGE_FALLBACKS.get(language, DEFAULT_LANGUAGE)

    if key in COMMON_TEXTS.get(fallback, {}):
        return COMMON_TEXTS[fallback][key]

    return COMMON_TEXTS[DEFAULT_LANGUAGE].get(key, key)


def get_language_name(language: str) -> str:
    """Til nomini qaytaradi."""
    return SUPPORTED_LANGUAGES.get(
        language,
        SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE],
    )["name"]


def get_language_keyboard() -> list[list[dict[str, str]]]:
    """Til tanlash uchun tugma ma'lumotlarini qaytaradi."""
    return [
        [
            {
                "text": f'{details["flag"]} {details["name"]}',
                "callback_data": f"set_language:{code}",
            }
        ]
        for code, details in SUPPORTED_LANGUAGES.items()
    ]
