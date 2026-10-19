
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


# ============================================================
# THRONE — ROLLAR TIZIMI
# Ushbu fayl yangi arxitektura uchun yozilgan.
# Boshqa fayllar shu yerdagi ID va turlardan foydalanadi.
# ============================================================


class Team(StrEnum):
    KRON = "KRON"
    SOYA = "SOYA"
    ISYON = "ISYON"
    MUSTAQIL = "MUSTAQIL"


@dataclass(frozen=True, slots=True)
class Role:
    id: str
    name: str
    team: Team
    description: str
    ability: str
    night_action: str | None = None
    night_priority: int = 0
    unique: bool = False


# ============================================================
# 36 TA ROL
# KRON: 12 | SOYA: 10 | ISYON: 10 | MUSTAQIL: 4
# ============================================================

_ROLE_LIST: tuple[Role, ...] = (

    # --------------------------------------------------------
    # KRON — 12 ROL
    # --------------------------------------------------------

    Role(
        id="shoh",
        name="Shoh",
        team=Team.KRON,
        description="Kron taxtining hukmdori. Kron jamoasi g‘alabasini ta’minlashi kerak.",
        ability="Bir kechada bitta raqib qobiliyatini to‘xtata oladi. Kuchli himoyaga ega.",
        night_action="block",
        night_priority=10,
        unique=True,
    ),
    Role(
        id="malika",
        name="Malika",
        team=Team.KRON,
        description="Kron oilasining muhim a’zosi.",
        ability="Har kecha bir o‘yinchini tanlab, uning himoyalangan yoki himoyasizligini tekshiradi.",
        night_action="inspect_defense",
        night_priority=30,
        unique=True,
    ),
    Role(
        id="shahzoda",
        name="Shahzoda",
        team=Team.KRON,
        description="Taxtning vorisi.",
        ability="Bir marta tungi hujumdan omon qolish imkoniyatiga ega.",
        night_action=None,
        unique=True,
    ),
    Role(
        id="vazir",
        name="Vazir",
        team=Team.KRON,
        description="Shohning siyosiy maslahatchisi.",
        ability="Har kecha bir o‘yinchi haqida ma’lumot to‘playdi.",
        night_action="investigate",
        night_priority=40,
        unique=True,
    ),
    Role(
        id="bosh_qomondon",
        name="Bosh qo‘mondon",
        team=Team.KRON,
        description="Kron qo‘shinining boshlig‘i.",
        ability="Har kecha bir o‘yinchini hujumdan himoya qiladi.",
        night_action="protect",
        night_priority=20,
        unique=True,
    ),
    Role(
        id="qirol_qoriqchisi",
        name="Qirol qo‘riqchisi",
        team=Team.KRON,
        description="Taxt va qirollik oilasini himoya qiladi.",
        ability="Tanlangan o‘yinchiga qarshi bitta tungi hujumni qaytarishga urinadi.",
        night_action="guard",
        night_priority=20,
        unique=True,
    ),
    Role(
        id="qozi",
        name="Qozi",
        team=Team.KRON,
        description="Qirollik qonunlarini himoya qiladi.",
        ability="Har kecha bir o‘yinchining harakatini tekshirib, shubhali faoliyat haqida ma’lumot oladi.",
        night_action="investigate",
        night_priority=40,
        unique=True,
    ),
    Role(
        id="xazinachi",
        name="Xazinachi",
        team=Team.KRON,
        description="Qirollik xazinasini boshqaradi.",
        ability="Har bir muvaffaqiyatli o‘yin yakunida qo‘shimcha Gold olish tizimiga ulanadi.",
        night_action=None,
        unique=True,
    ),
    Role(
        id="ritsar",
        name="Ritsar",
        team=Team.KRON,
        description="Kron uchun jang qiladigan sodiq jangchi.",
        ability="Har kecha bir o‘yinchini himoya qiladi.",
        night_action="protect",
        night_priority=20,
    ),
    Role(
        id="xizmatkor",
        name="Xizmatkor",
        team=Team.KRON,
        description="Saroydagi voqealardan xabardor.",
        ability="Har kecha bir o‘yinchini kuzatib, uning kim bilan uchrashganini bilishga urinadi.",
        night_action="observe",
        night_priority=40,
    ),
    Role(
        id="tinch_aholi",
        name="Tinch aholi",
        team=Team.KRON,
        description="Qirollikning oddiy fuqarosi.",
        ability="Maxsus tungi qobiliyati yo‘q. Muhokama va ovoz berish orqali Kronni himoya qiladi.",
        night_action=None,
    ),
    Role(
        id="aygoqchi",
        name="Ayg‘oqchi",
        team=Team.KRON,
        description="Dushmanlar orasidan yashirin ma’lumot izlaydi.",
        ability="Har kecha bir o‘yinchining jamoasini aniqlashga urinadi.",
        night_action="investigate_team",
        night_priority=40,
        unique=True,
    ),

    # --------------------------------------------------------
    # SOYA — 10 ROL
    # --------------------------------------------------------

    Role(
        id="soya_hukmdori",
        name="Soya hukmdori",
        team=Team.SOYA,
        description="Soya jamoasining boshlig‘i.",
        ability="Soya jamoasining tungi hujumini belgilaydi.",
        night_action="team_attack",
        night_priority=60,
        unique=True,
    ),
    Role(
        id="soya_qotili",
        name="Soya qotili",
        team=Team.SOYA,
        description="Soya hukmdorining asosiy jangchisi.",
        ability="Jamoaviy hujumda qatnashadi.",
        night_action="team_attack",
        night_priority=60,
    ),
    Role(
        id="soya_josusi",
        name="Soya josusi",
        team=Team.SOYA,
        description="Nishonlar haqida ma’lumot yig‘ib, Soya hukmdoriga yetkazadi.",
        ability="Har kecha bir o‘yinchining jamoasini tekshiradi.",
        night_action="investigate_team",
        night_priority=40,
        unique=True,
    ),
    Role(
        id="zaharsoz",
        name="Zaharsoz",
        team=Team.SOYA,
        description="Dushmanlarni zahar orqali zaiflashtiradi.",
        ability="Belgilangan tungi harakat orqali bitta o‘yinchini zaharlashi mumkin.",
        night_action="poison",
        night_priority=50,
    ),
    Role(
        id="soya_tabibi",
        name="Soya tabibi",
        team=Team.SOYA,
        description="Soya a’zolarini saqlab qolishga urinadi.",
        ability="Har kecha bitta Soya a’zosini himoya qiladi.",
        night_action="protect_ally",
        night_priority=20,
    ),
    Role(
        id="qorongu_vazir",
        name="Qorong‘u vazir",
        team=Team.SOYA,
        description="Raqiblarning rejalarini izdan chiqaradi.",
        ability="Bir o‘yinchining tungi qobiliyatini to‘xtatishga urinadi.",
        night_action="block",
        night_priority=10,
    ),
    Role(
        id="soya_ayg oqchisi",
        name="Soya kuzatuvchisi",
        team=Team.SOYA,
        description="Dushmanlarning tungi harakatlarini kuzatadi.",
        ability="Tanlangan o‘yinchining tungi harakati haqida ma’lumot oladi.",
        night_action="observe",
        night_priority=40,
    ),
    Role(
        id="soxta_maslahatchi",
        name="Soxta maslahatchi",
        team=Team.SOYA,
        description="O‘zini ishonchli maslahatchidek ko‘rsatadi.",
        ability="Tekshiruvlarda chalg‘ituvchi natija berish mexanizmiga ega.",
        night_action="mislead",
        night_priority=35,
    ),
    Role(
        id="soya_jallodi",
        name="Soya jallodi",
        team=Team.SOYA,
        description="Soya hukmdorining maxsus topshiriqlarini bajaradi.",
        ability="Jamoaviy hujumga qo‘shiladi.",
        night_action="team_attack",
        night_priority=60,
    ),
    Role(
        id="soya_qorovuli",
        name="Soya qorovuli",
        team=Team.SOYA,
        description="Soya a’zolarining xavfsizligini saqlaydi.",
        ability="Har kecha bitta sherigini himoya qilishga urinadi.",
        night_action="protect_ally",
        night_priority=20,
    ),

    # --------------------------------------------------------
    # ISYON — 10 ROL
    # --------------------------------------------------------

    Role(
        id="isyon_boshligi",
        name="Isyon boshlig‘i",
        team=Team.ISYON,
        description="Qirollik hokimiyatini ag‘darishni maqsad qiladi.",
        ability="Isyon jamoasining maxsus harakatlarini boshqaradi.",
        night_action="rebellion_action",
        night_priority=50,
        unique=True,
    ),
    Role(
        id="isyon_jangchisi",
        name="Isyon jangchisi",
        team=Team.ISYON,
        description="Isyon uchun kurashadi.",
        ability="Isyon jamoasining hujumida qatnashadi.",
        night_action="rebellion_attack",
        night_priority=60,
    ),
    Role(
        id="isyon josusi",
        name="Isyon josusi",
        team=Team.ISYON,
        description="Raqib jamoalar haqida ma’lumot izlaydi.",
        ability="Har kecha bir o‘yinchining jamoasini aniqlashga urinadi.",
        night_action="investigate_team",
        night_priority=40,
    ),
    Role(
        id="fitnachi",
        name="Fitnachi",
        team=Team.ISYON,
        description="O‘yinchilar orasida kelishmovchilik keltirib chiqaradi.",
        ability="Tanlangan o‘yinchining harakatiga xalaqit berishga urinadi.",
        night_action="block",
        night_priority=10,
    ),
    Role(
        id="isyon_tabibi",
        name="Isyon tabibi",
        team=Team.ISYON,
        description="Isyonchilarni saqlab qoladi.",
        ability="Har kecha bitta o‘yinchini himoya qiladi.",
        night_action="protect",
        night_priority=20,
    ),
    Role(
        id="isyon_mergan",
        name="Isyon mergani",
        team=Team.ISYON,
        description="Isyonning uzoq masofali jangchisi.",
        ability="Jamoaviy hujumda qatnashadi.",
        night_action="rebellion_attack",
        night_priority=60,
    ),
    Role(
        id="isyon_qorovuli",
        name="Isyon qorovuli",
        team=Team.ISYON,
        description="Isyon a’zolarini himoya qiladi.",
        ability="Tanlangan isyonchini hujumdan saqlashga urinadi.",
        night_action="protect_ally",
        night_priority=20,
    ),
    Role(
        id="isyon_usta",
        name="Isyon ustasi",
        team=Team.ISYON,
        description="Yashirin rejalarni amalga oshiradi.",
        ability="Bir o‘yinchining maxsus harakatini zaiflashtirishga urinadi.",
        night_action="weaken",
        night_priority=15,
    ),
    Role(
        id="isyon_targibotchisi",
        name="Isyon targ‘ibotchisi",
        team=Team.ISYON,
        description="Kunduzgi muhokamada odamlarni o‘z tomoniga og‘diradi.",
        ability="Ovoz berish mexanizmidagi maxsus ta’sir tizimiga ulanadi.",
        night_action=None,
    ),
    Role(
        id="yashirin_isyonchi",
        name="Yashirin isyonchi",
        team=Team.ISYON,
        description="O‘z jamoasini yashirincha qo‘llab-quvvatlaydi.",
        ability="Tekshiruvlarda o‘zini yashirish mexanizmiga ega.",
        night_action="conceal",
        night_priority=35,
    ),

    # --------------------------------------------------------
    # MUSTAQIL — 4 ROL
    # --------------------------------------------------------

    Role(
        id="yollanma_qotil",
        name="Yollanma qotil",
        team=Team.MUSTAQIL,
        description="Boshqa jamoalardan mustaqil ravishda o‘z maqsadini ko‘zlaydi.",
        ability="Shaxsiy g‘alaba shartlariga muvofiq nishonga hujum qiladi.",
        night_action="solo_attack",
        night_priority=60,
        unique=True,
    ),
    Role(
        id="soya_sayyohi",
        name="Soya sayyohi",
        team=Team.MUSTAQIL,
        description="O‘z yo‘lidan boradigan sirli o‘yinchi.",
        ability="Har kecha o‘zini yashirishga urinadi.",
        night_action="conceal",
        night_priority=35,
        unique=True,
    ),
    Role(
        id="qasoskor",
        name="Qasoskor",
        team=Team.MUSTAQIL,
        description="Shaxsiy qasosini olish uchun kurashadi.",
        ability="Belgilangan shaxsiy maqsad bajarilganda g‘alaba qozonadi.",
        night_action="revenge",
        night_priority=55,
        unique=True,
    ),
    Role(
        id="omon_qoluvchi",
        name="Omon qoluvchi",
        team=Team.MUSTAQIL,
        description="Asosiy maqsadi o‘yin oxirigacha tirik qolish.",
        ability="Bir necha marta foydalanish mumkin bo‘lgan himoya mexanizmiga ega.",
        night_action="self_protect",
        night_priority=20,
        unique=True,
    ),
)


# ============================================================
# UMUMIY ROLLAR KATALOGI
# ============================================================

ROLES: dict[str, Role] = {
    role.id: role for role in _ROLE_LIST
}

ROLE_COUNTS: dict[Team, int] = {
    team: sum(1 for role in _ROLE_LIST if role.team == team)
    for team in Team
}

TOTAL_ROLES = len(ROLES)


def get_role(role_id: str) -> Role | None:
    """Rol ID si bo‘yicha rolni qaytaradi."""
    return ROLES.get(role_id)


def roles_for_team(team: Team | str) -> tuple[Role, ...]:
    """Berilgan jamoaga tegishli rollarni qaytaradi."""
    normalized_team = Team(team)
    return tuple(
        role for role in _ROLE_LIST
        if role.team == normalized_team
    )


def get_role_names() -> dict[str, str]:
    """Rol ID va ko‘rinadigan nomlar lug‘atini qaytaradi."""
    return {
        role.id: role.name
        for role in _ROLE_LIST
    }


def validate_role_catalog() -> None:
    """Dastur ishga tushishida rol katalogini tekshirish uchun."""
    if TOTAL_ROLES != 36:
        raise ValueError(
            f"THRONE katalogida 36 ta rol bo‘lishi kerak. "
            f"Hozir: {TOTAL_ROLES}"
        )

    expected_counts = {
        Team.KRON: 12,
        Team.SOYA: 10,
        Team.ISYON: 10,
        Team.MUSTAQIL: 4,
    }

    if ROLE_COUNTS != expected_counts:
        raise ValueError(
            f"Jamoalar soni noto‘g‘ri: {ROLE_COUNTS}"
        )

    ids = [role.id for role in _ROLE_LIST]
    if len(ids) != len(set(ids)):
        raise ValueError("Rollar orasida takrorlangan ID mavjud.")


# Import qilinganda katalogni darhol tekshiramiz.
validate_role_catalog()
