from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RoleSide(StrEnum):
    """Main faction of a role."""

    KRON = "KRON"
    SOYA = "SOYA"
    YAKKA = "YAKKA"
    LEGION = "LEGION"


class RoleAbilityType(StrEnum):
    """General category of a role ability."""

    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"
    INFORMATION = "INFORMATION"
    PROTECTION = "PROTECTION"
    CONTROL = "CONTROL"
    ATTACK = "ATTACK"
    ECONOMY = "ECONOMY"
    SPECIAL = "SPECIAL"


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    """Complete static definition of one THRONE role."""

    key: str
    name: str
    side: RoleSide
    ability_type: RoleAbilityType
    ability: str
    victory_condition: str


ROLE_DEFINITIONS: dict[str, RoleDefinition] = {
    # ============================================================
    # KRON — 12
    # ============================================================

    "shoh": RoleDefinition(
        key="shoh",
        name="Shoh",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.CONTROL,
        ability=(
            "Har tun 1 o‘yinchining tungi qobiliyatini bloklaydi. "
            "Bir marta kuchli himoyalanish imkoniga ega."
        ),
        victory_condition=(
            "Soya asosiy tahdidlarini yo‘qotib, tirik qolish."
        ),
    ),

    "malika": RoleDefinition(
        key="malika",
        name="Malika",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.PROTECTION,
        ability=(
            "Har tun 1 o‘yinchini oddiy hujumdan himoya qiladi."
        ),
        victory_condition="KRON g‘alaba qilsa.",
    ),

    "shahzoda": RoleDefinition(
        key="shahzoda",
        name="Shahzoda",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "Shoh tirik paytda maxsus himoyaga ega. "
            "Shoh o‘lsa, yangi qobiliyati ochiladi."
        ),
        victory_condition="KRON g‘alaba qilsa.",
    ),

    "vazir": RoleDefinition(
        key="vazir",
        name="Vazir",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Har tun 1 o‘yinchining qaysi tomonga tegishli "
            "ekanini tekshiradi."
        ),
        victory_condition="KRON g‘alaba qilsa.",
    ),

    "bosh_qomondon": RoleDefinition(
        key="bosh_qomondon",
        name="Bosh qo‘mondon",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Har tun 1 o‘yinchiga oddiy hujum qiladi."
        ),
        victory_condition="KRON g‘alaba qilsa.",
    ),

    "qirol_qoriqchisi": RoleDefinition(
        key="qirol_qoriqchisi",
        name="Qirol qo‘riqchisi",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.PROTECTION,
        ability=(
            "Har tun 1 o‘yinchini kuchli himoya qiladi. "
            "Shohni himoya qilsa, qo‘shimcha bonus oladi."
        ),
        victory_condition=(
            "Shohni kamida 2 marta himoya qilib, "
            "KRON g‘alaba qilishi."
        ),
    ),

    "qozi": RoleDefinition(
        key="qozi",
        name="Qozi",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.CONTROL,
        ability=(
            "Bir marta ovoz berishni bekor qilish yoki "
            "qayta ovoz berishni majburlash imkoniga ega."
        ),
        victory_condition=(
            "Kamida 2 ta foydali KRON ovoz natijasida qatnashish."
        ),
    ),

    "xazinachi": RoleDefinition(
        key="xazinachi",
        name="Xazinachi",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.ECONOMY,
        ability=(
            "Qirollik iqtisodiyotiga ta’sir qiladi va ayrim "
            "iqtisodiy hujumlardan himoyalangan."
        ),
        victory_condition=(
            "KRON g‘alaba qilishi va xazina saqlanishi."
        ),
    ),

    "ritsir": RoleDefinition(
        key="ritsir",
        name="Ritsir",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.PROTECTION,
        ability=(
            "Bir martalik zirhga ega. "
            "Oddiy hujumdan omon qoladi."
        ),
        victory_condition=(
            "Kamida 1 ta hujumdan omon qolib, "
            "KRON g‘alaba qilishi."
        ),
    ),

    "xizmatkor": RoleDefinition(
        key="xizmatkor",
        name="Xizmatkor",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Har tun 1 o‘yinchini kuzatib, "
            "uning harakat qilgan-qilmaganini aniqlaydi."
        ),
        victory_condition=(
            "Kamida 2 ta faoliyat izini aniqlab, "
            "KRON g‘alaba qilishi."
        ),
    ),

    "tinch_aholi": RoleDefinition(
        key="tinch_aholi",
        name="Tinch aholi",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.PASSIVE,
        ability=(
            "Tungi qobiliyati yo‘q. Asosiy kuchi — "
            "muhokama va ovoz berish."
        ),
        victory_condition="KRON g‘alaba qilsa.",
    ),

    "aygoqchi": RoleDefinition(
        key="aygoqchi",
        name="Ayg‘oqchi",
        side=RoleSide.KRON,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Har tun 1 o‘yinchining tomonini aniqlaydi."
        ),
        victory_condition=(
            "Kamida 2 ta Soya o‘yinchisini to‘g‘ri aniqlash "
            "va KRON g‘alabasi."
        ),
    ),

    # ============================================================
    # SOYA — 10
    # ============================================================

    "soya_boshligi": RoleDefinition(
        key="soya_boshligi",
        name="Soya boshlig‘i",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Soya hujumlarini boshqaradi. "
            "Bir marta tekshiruvlardan yashirinish imkoniga ega."
        ),
        victory_condition=(
            "KRON kuchini qulatib, tiriklarning kamida "
            "50 foizini Soya nazoratiga olish."
        ),
    ),

    "qotil": RoleDefinition(
        key="qotil",
        name="Qotil",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Har tun 1 o‘yinchiga oddiy hujum qiladi."
        ),
        victory_condition=(
            "2 ta KRON o‘yinchisini yo‘q qilish "
            "va SOYA g‘alabasi."
        ),
    ),

    "josus": RoleDefinition(
        key="josus",
        name="Josus",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "1 o‘yinchini kuzatib, uning tungi faoliyatini aniqlaydi."
        ),
        victory_condition=(
            "3 ta tungi faoliyatni aniqlash "
            "va SOYA g‘alabasi."
        ),
    ),

    "soxta_maslahatchi": RoleDefinition(
        key="soxta_maslahatchi",
        name="Soxta maslahatchi",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Tekshiruvlarni chalg‘itadi va o‘zini "
            "boshqa tomon sifatida ko‘rsatishi mumkin."
        ),
        victory_condition=(
            "2 ta tekshiruvni noto‘g‘ri yo‘naltirish "
            "va SOYA g‘alabasi."
        ),
    ),

    "xoin": RoleDefinition(
        key="xoin",
        name="Xoin",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "KRON ichida yashirin Soya. O‘zini KRON tarafdori "
            "qilib ko‘rsatadi va yashirin ma’lumot uzatadi."
        ),
        victory_condition=(
            "SOYA g‘alabasigacha fosh bo‘lmaslik."
        ),
    ),

    "qora_vazir": RoleDefinition(
        key="qora_vazir",
        name="Qora vazir",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.CONTROL,
        ability=(
            "Ovoz berishga yashirin ta’sir ko‘rsatadi."
        ),
        victory_condition=(
            "2 ta ovoz natijasiga muvaffaqiyatli ta’sir qilish "
            "va SOYA g‘alabasi."
        ),
    ),

    "dushman_qiroli": RoleDefinition(
        key="dushman_qiroli",
        name="Dushman qiroli",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Shoh yoki Shahzodaga qarshi maxsus kuchli "
            "hujumga ega."
        ),
        victory_condition=(
            "Shoh yoki Shahzodani yo‘q qilish "
            "va SOYA g‘alabasi."
        ),
    ),

    "dushman_qomondoni": RoleDefinition(
        key="dushman_qomondoni",
        name="Dushman qo‘mondoni",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Kuchli hujum qiladi va ayrim kuchli "
            "himoyalarni buzishi mumkin."
        ),
        victory_condition=(
            "2 ta muvaffaqiyatli hujumda qatnashish "
            "va SOYA g‘alabasi."
        ),
    ),

    "dushman_josusi": RoleDefinition(
        key="dushman_josusi",
        name="Dushman josusi",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Maxsus rollarni aniqlashga ixtisoslashgan."
        ),
        victory_condition=(
            "2 ta maxsus rolni aniqlash "
            "va SOYA g‘alabasi."
        ),
    ),

    "dushman_suiqasdchisi": RoleDefinition(
        key="dushman_suiqasdchisi",
        name="Dushman suiqasdchisi",
        side=RoleSide.SOYA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Oddiy himoyani chetlab o‘tuvchi suiqasdga ega. "
            "Foydalanish soni cheklangan."
        ),
        victory_condition=(
            "Kamida 1 ta muvaffaqiyatli suiqasd "
            "va SOYA g‘alabasi."
        ),
    ),

    # ============================================================
    # YAKKA — 7
    # ============================================================

    "ovchi": RoleDefinition(
        key="ovchi",
        name="Ovchi",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Shaxsiy nishonlari beriladi. "
            "Ularni yo‘q qilishi kerak."
        ),
        victory_condition=(
            "3 ta belgilangan nishonni yo‘q qilish."
        ),
    ),

    "telba": RoleDefinition(
        key="telba",
        name="Telba",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "Guruh uni xavfli deb o‘ylab, "
            "ovoz bilan chiqarib yuborishi kerak."
        ),
        victory_condition=(
            "Ovoz berishda chiqarib yuborilsa."
        ),
    ),

    "sayyoh": RoleDefinition(
        key="sayyoh",
        name="Sayyoh",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.PASSIVE,
        ability=(
            "Tungi faoliyati qiyin aniqlanadi."
        ),
        victory_condition=(
            "4 tun tirik qolish va 2 ta shaxsiy shartni bajarish."
        ),
    ),

    "yollanma_jangchi": RoleDefinition(
        key="yollanma_jangchi",
        name="Yollanma jangchi",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Yashirin shartnoma asosida nishonlar oladi."
        ),
        victory_condition=(
            "2 ta shartnoma nishonini yo‘q qilish."
        ),
    ),

    "surgun_shahzoda": RoleDefinition(
        key="surgun_shahzoda",
        name="Surgun shahzoda",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "Qaytish qobiliyati orqali ma’lum shartlarda "
            "o‘yinga qaytishi mumkin."
        ),
        victory_condition=(
            "Qaytishdan foydalanib, o‘yin oxirigacha tirik qolish."
        ),
    ),

    "taxt_davogari": RoleDefinition(
        key="taxt_davogari",
        name="Taxt da’vogari",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "Shoh o‘lgach, taxt uchun kurash boshlaydi."
        ),
        victory_condition=(
            "Shoh o‘lgandan keyin 3 ta ovoz olib, "
            "yakuniy bosqichgacha tirik qolish."
        ),
    ),

    "qaroqchi": RoleDefinition(
        key="qaroqchi",
        name="Qaroqchi",
        side=RoleSide.YAKKA,
        ability_type=RoleAbilityType.ECONOMY,
        ability=(
            "Har tun 1 o‘yinchidan Gold o‘g‘irlaydi."
        ),
        victory_condition=(
            "1000 Gold o‘g‘irlab, o‘yin oxirigacha tirik qolish."
        ),
    ),

    # ============================================================
    # LEGION — 7
    # ============================================================

    "tabib": RoleDefinition(
        key="tabib",
        name="Tabib",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.PROTECTION,
        ability=(
            "Har tun 1 o‘yinchini oddiy hujumdan davolaydi."
        ),
        victory_condition=(
            "3 marta muvaffaqiyatli davolash va tirik qolish."
        ),
    ),

    "kuzatuvchi": RoleDefinition(
        key="kuzatuvchi",
        name="Kuzatuvchi",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "1 o‘yinchini kuzatib, unga kimlar "
            "tashrif buyurganini ko‘radi."
        ),
        victory_condition=(
            "4 ta tashrifni aniqlash."
        ),
    ),

    "qorovul": RoleDefinition(
        key="qorovul",
        name="Qorovul",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.CONTROL,
        ability=(
            "Ayrim tungi harakatlarni bloklaydi."
        ),
        victory_condition=(
            "2 ta muhim hujumni bloklash va tirik qolish."
        ),
    ),

    "solnomachi": RoleDefinition(
        key="solnomachi",
        name="Solnomachi",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.INFORMATION,
        ability=(
            "Tungi muhim voqealarni qayd qiladi va "
            "ertalab cheklangan ma’lumot oladi."
        ),
        victory_condition=(
            "5 ta muhim voqeani to‘g‘ri qayd qilish."
        ),
    ),

    "savdogar": RoleDefinition(
        key="savdogar",
        name="Savdogar",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.ECONOMY,
        ability=(
            "Gold bilan savdo qiladi va iqtisodiy bonuslar oladi."
        ),
        victory_condition=(
            "1500 Gold savdo aylanmasiga erishish."
        ),
    ),

    "suiqasdchi": RoleDefinition(
        key="suiqasdchi",
        name="Suiqasdchi",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.ATTACK,
        ability=(
            "Belgilangan maxsus nishoniga qarshi "
            "suiqasd imkoniyatiga ega."
        ),
        victory_condition=(
            "Belgilangan nishonni yo‘q qilish."
        ),
    ),

    "oshpaz": RoleDefinition(
        key="oshpaz",
        name="Oshpaz",
        side=RoleSide.LEGION,
        ability_type=RoleAbilityType.SPECIAL,
        ability=(
            "Har tun 1 o‘yinchini tanlab, unga ovqat tayyorlaydi. "
            "Bu himoya emas. Faqat Oshpaz va tanlangan "
            "o‘yinchi buni biladi."
        ),
        victory_condition=(
            "5 xil o‘yinchini mehmon qilib, tirik qolish."
        ),
    ),
}


def get_role(role_key: str) -> RoleDefinition | None:
    """Return a role definition by its unique key."""
    return ROLE_DEFINITIONS.get(role_key)


def get_all_roles() -> tuple[RoleDefinition, ...]:
    """Return all registered roles."""
    return tuple(ROLE_DEFINITIONS.values())


def get_roles_by_side(side: RoleSide) -> tuple[RoleDefinition, ...]:
    """Return all roles belonging to a faction."""
    return tuple(
        role
        for role in ROLE_DEFINITIONS.values()
        if role.side == side
    )


def get_role_count() -> int:
    """Return the total number of registered roles."""
    return len(ROLE_DEFINITIONS)


def validate_role_roster() -> None:
    """Validate the final THRONE role roster."""
    expected_counts = {
        RoleSide.KRON: 12,
        RoleSide.SOYA: 10,
        RoleSide.YAKKA: 7,
        RoleSide.LEGION: 7,
    }

    if get_role_count() != 36:
        raise RuntimeError(
            f"THRONE requires exactly 36 roles, "
            f"found {get_role_count()}."
        )

    for side, expected_count in expected_counts.items():
        actual_count = len(get_roles_by_side(side))

        if actual_count != expected_count:
            raise RuntimeError(
                f"{side} requires {expected_count} roles, "
                f"found {actual_count}."
)
