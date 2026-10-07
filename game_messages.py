from __future__ import annotations


GAME_TITLE = "👑 <b>THRONE — Taxtlar O‘yini</b>"


def lobby_message(
    player_count: int,
    min_players: int,
    max_players: int,
) -> str:
    return (
        f"{GAME_TITLE}\n\n"
        "🏰 <b>Yangi qirollik o‘yini ochildi!</b>\n\n"
        f"👥 O‘yinchilar: <b>{player_count}/{max_players}</b>\n"
        f"📌 Boshlash uchun kamida <b>{min_players}</b> nafar "
        "o‘yinchi kerak.\n\n"
        "⚔️ Taxt uchun kurashga qo‘shilish uchun "
        "<b>Qo‘shilish</b> tugmasini bosing."
    )


def player_joined_message(
    display_name: str,
    player_count: int,
    max_players: int,
) -> str:
    return (
        f"👤 <b>{display_name}</b> o‘yinga qo‘shildi.\n\n"
        f"👥 O‘yinchilar: <b>{player_count}/{max_players}</b>"
    )


def player_already_joined_message() -> str:
    return "⚠️ Siz allaqachon bu o‘yinga qo‘shilgansiz."


def game_full_message() -> str:
    return "🚫 O‘yinchilar soni maksimal chegaraga yetdi."


def game_not_started_message() -> str:
    return (
        "⚠️ O‘yin hali boshlanmadi.\n"
        "Avval lobby bosqichida o‘yinga qo‘shiling."
    )


def not_enough_players_message(
    current_count: int,
    min_players: int,
) -> str:
    remaining = min_players - current_count

    return (
        "⚠️ O‘yinni boshlash uchun o‘yinchilar yetarli emas.\n\n"
        f"👥 Hozir: <b>{current_count}</b>\n"
        f"🎯 Kerak: <b>{min_players}</b>\n"
        f"➕ Yana: <b>{remaining}</b> ta o‘yinchi kerak."
    )


def game_started_message() -> str:
    return (
        f"{GAME_TITLE}\n\n"
        "⚔️ <b>O‘yin boshlandi!</b>\n\n"
        "Rollar maxfiy tarzda taqsimlanmoqda...\n"
        "📜 Har bir o‘yinchi o‘z vazifasini shaxsiy xabarda oladi."
    )


def role_reveal_message() -> str:
    return (
        "📜 <b>Rollar taqsimlandi.</b>\n\n"
        "🔐 Sizning rolingiz maxfiy.\n"
        "🤫 Uni boshqa o‘yinchilarga oshkor qilmang."
    )


def private_role_message(
    role_name: str,
    side_name: str,
    ability: str,
    victory_condition: str,
) -> str:
    return (
        f"{GAME_TITLE}\n\n"
        f"🎭 <b>Sizning rolingiz:</b> {role_name}\n"
        f"⚔️ <b>Tomon:</b> {side_name}\n\n"
        f"✨ <b>Qobiliyat:</b>\n{ability}\n\n"
        f"🏆 <b>G‘alaba sharti:</b>\n{victory_condition}"
    )


def partners_message(partners: list[str]) -> str:
    if not partners:
        return (
            "🤝 <b>Sizning sheriklaringiz</b>\n\n"
            "Sizga ma'lum bo‘lgan sherik yo‘q."
        )

    partner_lines = "\n".join(
        f"• {partner}"
        for partner in partners
    )

    return (
        "🤝 <b>Sizning sheriklaringiz</b>\n\n"
        f"{partner_lines}"
    )


def night_started_message(night_number: int) -> str:
    return (
        f"🌙 <b>{night_number}-tun boshlandi.</b>\n\n"
        "Saroy jimjitlikka cho‘mdi.\n"
        "Ammo qorong‘ulik ostida yashirin harakatlar "
        "allaqachon boshlandi..."
    )


def day_started_message(day_number: int) -> str:
    return (
        f"☀️ <b>{day_number}-kun boshlandi.</b>\n\n"
        "Tun sirlari endi asta-sekin yuzaga chiqadi."
    )


def discussion_started_message() -> str:
    return (
        "🗣️ <b>Muhokama boshlandi.</b>\n\n"
        "Dalillarni tahlil qiling.\n"
        "Shubhali harakatlarni muhokama qiling.\n"
        "Ammo ittifoq va xiyonatni ham unutmang."
    )


def voting_started_message() -> str:
    return (
        "⚖️ <b>Ovoz berish boshlandi.</b>\n\n"
        "Kimni taxtga xavf deb bilasiz?\n"
        "Qaroringizni ehtiyotkorlik bilan qabul qiling."
    )


def last_words_message(
    player_name: str,
    duration: int,
) -> str:
    return (
        f"🕯️ <b>{player_name}</b> uchun so‘nggi so‘zlar vaqti.\n\n"
        f"⏳ Sizda <b>{duration} soniya</b> bor.\n"
        "Bu vaqt tugagach, o‘yin avtomatik davom etadi."
    )


def player_eliminated_message(
    player_name: str,
) -> str:
    return (
        f"⚔️ <b>{player_name}</b> o‘yindan chiqarildi.\n\n"
        "🏰 Saroydagi kuchlar muvozanati o‘zgardi."
    )


def attack_blocked_message(
    player_name: str,
) -> str:
    return (
        f"🛡️ <b>{player_name}</b> ga qilingan hujum "
        "himoya tufayli muvaffaqiyatsiz tugadi."
    )


def no_elimination_message() -> str:
    return (
        "⚖️ <b>Bu safar hech kim chiqarilmadi.</b>\n\n"
        "Ovozlar yetarli bo‘lmadi yoki qayta ovoz berish "
        "natijasida qaror qabul qilinmadi."
    )


def game_finished_message(
    winning_side: str,
    reason: str,
) -> str:
    return (
        f"{GAME_TITLE}\n\n"
        "🏆 <b>O‘yin yakunlandi!</b>\n\n"
        f"👑 G‘olib tomon: <b>{winning_side}</b>\n"
        f"📜 Sabab: {reason}"
    )


def game_stopped_message() -> str:
    return (
        f"{GAME_TITLE}\n\n"
        "🛑 <b>O‘yin to‘xtatildi.</b>\n\n"
        "Ushbu o‘yin endi davom ettirilmaydi."
    )


def invalid_action_message() -> str:
    return (
        "⚠️ <b>Bu harakatni hozir amalga oshirib bo‘lmaydi.</b>\n\n"
        "O‘yin bosqichi yoki sizning rolingiz bunga ruxsat bermaydi."
    )


def target_not_found_message() -> str:
    return "⚠️ Tanlangan o‘yinchi topilmadi."


def target_not_alive_message() -> str:
    return "⚠️ Tanlangan o‘yinchi allaqachon o‘yindan chiqqan."


def not_your_turn_message() -> str:
    return "⏳ Hozir sizning harakat vaqtingiz emas."


def permission_denied_message() -> str:
    return (
        "🚫 <b>Ruxsat yo‘q.</b>\n\n"
        "Bu amalni faqat guruh administratori bajarishi mumkin."
)
