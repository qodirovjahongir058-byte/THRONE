
"""THRONE — rol katalogi va avtomatik rol taqsimlash."""

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Role:
    id: str
    name: str
    faction: str
    description: str
    unique: bool = False


KRON = "KRON"
SOYA = "SOYA"
YAKKA = "YAKKA"

MIN_PLAYERS = 4
MAX_PLAYERS = 30


# Eslatma:
# Faqat Shoh, Shahzoda, Shoh qo'riqchisi va Sauron
# avvalgi kelishuvlardan olingan. Qolgan rollar nomlari
# va tavsiflari hozircha loyiha uchun taklif hisoblanadi.

ROLES: tuple[Role, ...] = (
    # KRON — qirollik tomoni
    Role(
        "king", "Shoh", KRON,
        "Qirollik yetakchisi. Ikki tun ketma-ket harakat qilmasa, "
        "uning o‘rni vorislik qoidasiga ko‘ra ko‘rib chiqiladi.",
        unique=True,
    ),
    Role(
        "prince", "Shahzoda", KRON,
        "Shoh halok bo‘lsa, tirik bo‘lganida uning o‘rnini egallaydi.",
        unique=True,
    ),
    Role(
        "king_guard", "Shoh qo‘riqchisi", KRON,
        "Shohni himoya qiladi. O‘zini himoya qila olmaydi.",
        unique=True,
    ),
    Role(
        "healer", "Tabib", KRON,
        "Tungi himoya qobiliyati taklif qilinayotgan rol.",
    ),
    Role(
        "seer", "Donishmand", KRON,
        "O‘yinchilar haqida ma’lumot olish qobiliyati taklif qilinayotgan rol.",
    ),
    Role(
        "knight", "Ritsar", KRON,
        "Qirollikni himoya qilishga mo‘ljallangan rol.",
    ),
    Role(
        "archer", "Kamondor", KRON,
        "Masofadan hujum qilishga mo‘ljallangan rol.",
    ),
    Role(
        "alchemist", "Alkimyogar", KRON,
        "Maxsus buyumlar bilan ishlashga mo‘ljallangan rol.",
    ),
    Role(
        "diplomat", "Diplomat", KRON,
        "Muzokara va ovoz berish bilan bog‘liq rol.",
    ),
    Role(
        "scout", "Razvedkachi", KRON,
        "Ma’lumot yig‘ishga mo‘ljallangan rol.",
    ),

    # SOYA — qorong‘u tomon
    Role(
        "sauron", "Sauron", SOYA,
        "SOYA jamoasining yetakchisi.",
        unique=True,
    ),
    Role(
        "shadow_assassin", "Soya qotili", SOYA,
        "Tungi hujumga mo‘ljallangan rol.",
    ),
    Role(
        "dark_mage", "Qora sehrgar", SOYA,
        "Maxsus tungi qobiliyatga mo‘ljallangan rol.",
    ),
    Role(
        "spy", "Josus", SOYA,
        "Yashirin ma’lumot yig‘ishga mo‘ljallangan rol.",
    ),
    Role(
        "saboteur", "Buzg‘unchi", SOYA,
        "Boshqa o‘yinchilarning harakatlariga xalaqit berishga mo‘ljallangan rol.",
    ),
    Role(
        "shadow_guard", "Soya himoyachisi", SOYA,
        "SOYA a’zolarini himoya qilishga mo‘ljallangan rol.",
    ),

    # YAKKA — mustaqil tomon
    Role(
        "wanderer", "Darbadar", YAKKA,
        "Mustaqil maqsadli rol.",
    ),
    Role(
        "trickster", "Hiylakor", YAKKA,
        "Aldov va strategiyaga asoslangan mustaqil rol.",
    ),
    Role(
        "survivor", "Omon qoluvchi", YAKKA,
        "O‘yinda omon qolishga yo‘naltirilgan rol.",
    ),
    Role(
        "bounty_hunter", "Mukofot ovchisi", YAKKA,
        "Alohida nishon bilan bog‘liq mustaqil rol.",
    ),
)


ROLES_BY_ID: dict[str, Role] = {
    role.id: role for role in ROLES
}


def get_role(role_id: str) -> Role | None:
    """Rolni ID orqali topish."""
    return ROLES_BY_ID.get(role_id)


def get_roles_by_faction(faction: str) -> tuple[Role, ...]:
    """Jamoa bo‘yicha rollarni qaytarish."""
    if faction not in {KRON, SOYA, YAKKA}:
        return ()

    return tuple(
        role for role in ROLES
        if role.faction == faction
    )


def validate_player_count(player_count: int) -> None:
    """O‘yinchilar sonini tekshirish."""
    if not MIN_PLAYERS <= player_count <= MAX_PLAYERS:
        raise ValueError(
            f"O‘yinchilar soni {MIN_PLAYERS}–{MAX_PLAYERS} "
            "oralig‘ida bo‘lishi kerak."
        )


def assign_roles(
    player_ids: list[int],
    rng: random.Random | None = None,
) -> dict[int, Role]:
    """
    O‘yinchilarga rollarni tasodifiy taqsimlash.

    Takrorlanmaydigan unique rollar bir martadan beriladi.
    Oddiy rollar 20 tadan ko‘p o‘yinchi bo‘lsa takrorlanishi mumkin.

    Bu boshlang‘ich taqsimlash mexanizmi; jamoalar muvozanati
    va har bir o‘yinchi soni uchun maxsus tarkib hali belgilanmagan.
    """
    validate_player_count(len(player_ids))

    if len(set(player_ids)) != len(player_ids):
        raise ValueError("O‘yinchi ID raqamlari takrorlanmasligi kerak.")

    generator = rng or random.SystemRandom()

    unique_roles = [role for role in ROLES if role.unique]
    repeatable_roles = [role for role in ROLES if not role.unique]

    # Har bir noyob rol ko‘pi bilan bir marta beriladi.
    pool = unique_roles + repeatable_roles

    # 30 o‘yinchi uchun takrorlanuvchi rollar kerak bo‘lishi mumkin.
    while len(pool) < len(player_ids):
        pool.append(generator.choice(repeatable_roles))

    generator.shuffle(pool)

    selected_roles = pool[:len(player_ids)]
    generator.shuffle(selected_roles)

    return dict(zip(player_ids, selected_roles))


def role_summary() -> dict[str, int]:
    """Har bir jamoada nechta rol borligini ko‘rsatish."""
    return {
        faction: len(get_roles_by_faction(faction))
        for faction in (KRON, SOYA, YAKKA)
    }
    
