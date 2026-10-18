
from dataclasses import dataclass
from enum import Enum


class Team(str, Enum):
    KRON = "KRON"
    SOYA = "SOYA"
    YAKKA = "YAKKA"
    LEGION = "LEGION"


@dataclass(frozen=True)
class Role:
    id: str
    name: str
    team: Team
    ability: str
    action: str | None
    win_condition: str
    passive: bool = False


# ==================================================
# THRONE — 36 TA ROL
# KRON 12 | SOYA 10 | YAKKA 7 | LEGION 7
# ==================================================

ROLES: dict[str, Role] = {

    # --------------------------------------------------
    # KRON — 12 TA ROL
    # --------------------------------------------------

    "shoh": Role(
        "shoh", "Shoh", Team.KRON,
        "Har kecha bitta dushman qobiliyatini to'sadi; "
        "kuchli himoyaga ega.",
        "block",
        "Soya tahdidlari yo'q qilinganda va Shoh tirik qolsa."
    ),

    "malika": Role(
        "malika", "Malika", Team.KRON,
        "Saroydagi ittifoqlar va muhim aloqalarni boshqaradi.",
        "influence",
        "KRON jamoasi g'alaba qilsa."
    ),

    "shahzoda": Role(
        "shahzoda", "Shahzoda", Team.KRON,
        "Shoh halok bo'lsa, vorislik huquqi faollashadi.",
        "succession",
        "KRON jamoasi g'alaba qilsa."
    ),

    "vazir": Role(
        "vazir", "Vazir", Team.KRON,
        "Siyosiy ma'lumotlarni tekshiradi va qarorlarga ta'sir qiladi.",
        "investigate",
        "KRON jamoasi g'alaba qilsa."
    ),

    "bosh_qomondon": Role(
        "bosh_qomondon", "Bosh qo'mondon", Team.KRON,
        "Harbiy strategiya orqali bitta o'yinchiga hujum qiladi.",
        "attack",
        "KRON jamoasi g'alaba qilsa."
    ),

    "qirol_qorovuli": Role(
        "qirol_qorovuli", "Qirol qo'riqchisi", Team.KRON,
        "Tanlangan o'yinchini tungi hujumdan himoya qiladi.",
        "protect",
        "KRON jamoasi g'alaba qilsa."
    ),

    "qozi": Role(
        "qozi", "Qozi", Team.KRON,
        "Ovoz berish va sud jarayonida maxsus vakolatga ega.",
        "judge",
        "KRON jamoasi g'alaba qilsa."
    ),

    "xazinachi": Role(
        "xazinachi", "Xazinachi", Team.KRON,
        "O'yinchi iqtisodiyoti va mukofotlar haqida ma'lumot oladi.",
        "inspect_treasury",
        "KRON jamoasi g'alaba qilsa."
    ),

    "ritsar": Role(
        "ritsar", "Ritsar", Team.KRON,
        "Bir kecha tanlangan ittifoqchini qo'riqlaydi.",
        "guard",
        "KRON jamoasi g'alaba qilsa."
    ),

    "xizmatkor": Role(
        "xizmatkor", "Xizmatkor", Team.KRON,
        "Saroydagi yashirin faoliyat haqida ma'lumot izlaydi.",
        "observe",
        "KRON jamoasi g'alaba qilsa."
    ),

    "tinch_aholi": Role(
        "tinch_aholi", "Tinch aholi", Team.KRON,
        "Maxsus tungi qobiliyati yo'q; kunduzgi ovozda qatnashadi.",
        None,
        "KRON jamoasi g'alaba qilsa.",
        passive=True,
    ),

    "aygoqchi": Role(
        "aygoqchi", "Ayg'oqchi", Team.KRON,
        "Har kecha tanlangan o'yinchining faoliyatini kuzatadi.",
        "observe",
        "KRON jamoasi g'alaba qilsa."
    ),

    # --------------------------------------------------
    # SOYA — 10 TA ROL
    # --------------------------------------------------

    "soya_boshligi": Role(
        "soya_boshligi", "Soya boshlig'i", Team.SOYA,
        "Soya hujumini boshqaradi va nishonni tanlaydi.",
        "team_attack",
        "KRON tahdidlari yo'q qilinib, SOYA g'alaba qilsa."
    ),

    "qotil": Role(
        "qotil", "Qotil", Team.SOYA,
        "Tunda tanlangan o'yinchiga hujum qiladi.",
        "attack",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "josus": Role(
        "josus", "Josus", Team.SOYA,
        "Dushman o'yinchilarining faoliyatini kuzatadi.",
        "observe",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "soxta_maslahatchi": Role(
        "soxta_maslahatchi", "Soxta maslahatchi", Team.SOYA,
        "Tekshiruvlarda o'z jamoasi haqidagi ma'lumotni yashiradi.",
        "mislead",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "xoin": Role(
        "xoin", "Xoin", Team.SOYA,
        "KRON orasida ishonchni buzish uchun maxsus harakat qiladi.",
        "sabotage",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "qora_vazir": Role(
        "qora_vazir", "Qora vazir", Team.SOYA,
        "Bir o'yinchining tungi harakatini to'sadi.",
        "block",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "dushman_qiroli": Role(
        "dushman_qiroli", "Dushman qiroli", Team.SOYA,
        "SOYA jamoasining strategik qarorlarini boshqaradi.",
        "team_attack",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "dushman_qomondoni": Role(
        "dushman_qomondoni", "Dushman qo'mondoni", Team.SOYA,
        "Tanlangan nishonga kuchli hujum uyushtiradi.",
        "attack",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "dushman_josusi": Role(
        "dushman_josusi", "Dushman josusi", Team.SOYA,
        "Bir o'yinchining jamoasini aniqlashga urinadi.",
        "investigate",
        "SOYA jamoasi g'alaba qilsa."
    ),

    "dushman_suiqasdchisi": Role(
        "dushman_suiqasdchisi", "Dushman suiqasdchisi", Team.SOYA,
        "Maxsus hujum orqali himoyani chetlab o'tishga urinadi.",
        "hidden_attack",
        "SOYA jamoasi g'alaba qilsa."
    ),

    # --------------------------------------------------
    # YAKKA — 7 TA ROL
    # --------------------------------------------------

    "ovchi": Role(
        "ovchi", "Ovchi", Team.YAKKA,
        "O'z nishonini ovlaydi va xavf tug'dirganlarga hujum qiladi.",
        "attack",
        "Shaxsiy ov maqsadini bajarsa."
    ),

    "telba": Role(
        "telba", "Telba", Team.YAKKA,
        "Kunduzgi ovoz bilan chiqarib yuborilish orqali yutishga urinadi.",
        None,
        "Ovoz berish orqali chiqarib yuborilsa.",
        passive=True,
    ),

    "sayyoh": Role(
        "sayyoh", "Sayyoh", Team.YAKKA,
        "Har kecha bir o'yinchining oldiga boradi; tashrif xavfli bo'lishi mumkin.",
        "visit",
        "Belgilangan sayohat maqsadini bajarsa."
    ),

    "yollanma_jangchi": Role(
        "yollanma_jangchi", "Yollanma jangchi", Team.YAKKA,
        "Shaxsiy topshiriq bo'yicha nishonga hujum qiladi.",
        "contract_attack",
        "Shaxsiy shartnomani bajarsa."
    ),

    "surgun_shahzoda": Role(
        "surgun_shahzoda", "Surgun shahzoda", Team.YAKKA,
        "Omon qolish va shaxsiy vorislik maqsadini bajarishga urinadi.",
        "survive",
        "Shaxsiy maqsadini bajarib, belgilangan yakungacha tirik qolsa."
    ),

    "taxt_davogari": Role(
        "taxt_davogari", "Taxt da'vogari", Team.YAKKA,
        "Taxt uchun yashirin kurash olib boradi.",
        "claim_throne",
        "Taxtni egallash shartini bajarsa."
    ),

    "qaroqchi": Role(
        "qaroqchi", "Qaroqchi", Team.YAKKA,
        "Tunda o'yinchidan resurs yoki foyda olishga urinadi.",
        "steal_gold",
        "Shaxsiy o'lja maqsadini bajarsa."
    ),

    # --------------------------------------------------
    # LEGION — 7 TA ROL
    # --------------------------------------------------

    "tabib": Role(
        "tabib", "Tabib", Team.LEGION,
        "Tanlangan o'yinchining holatini yaxshilashga urinadi.",
        "heal",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "kuzatuvchi": Role(
        "kuzatuvchi", "Kuzatuvchi", Team.LEGION,
        "Bir o'yinchining tungi harakatini kuzatadi.",
        "observe",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "qorovul": Role(
        "qorovul", "Qorovul", Team.LEGION,
        "Bir hudud yoki o'yinchini qo'riqlaydi.",
        "guard",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "solnomachi": Role(
        "solnomachi", "Solnomachi", Team.LEGION,
        "Oldingi bosqichlarda sodir bo'lgan voqealarni tekshiradi.",
        "memory_check",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "savdogar": Role(
        "savdogar", "Savdogar", Team.LEGION,
        "O'yin iqtisodiyoti orqali foyda olishga harakat qiladi.",
        "trade",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "suiqasdchi": Role(
        "suiqasdchi", "Suiqasdchi", Team.LEGION,
        "Belgilangan nishonga yashirin hujum uyushtiradi.",
        "hidden_attack",
        "LEGION jamoasi g'alaba qilsa."
    ),

    "oshpaz": Role(
        "oshpaz", "Oshpaz", Team.LEGION,
        "Tanlangan o'yinchiga ovqat yuboradi; bu himoya qobiliyati emas.",
        "feed",
        "LEGION jamoasi g'alaba qilsa."
    ),
}


# ==================================================
# TEKSHIRUV VA YORDAMCHI FUNKSIYALAR
# ==================================================

def get_role(role_id: str) -> Role | None:
    """Rol identifikatori bo'yicha rolni qaytaradi."""
    return ROLES.get(role_id)


def get_roles_by_team(team: Team) -> list[Role]:
    """Tanlangan jamoaning barcha rollarini qaytaradi."""
    return [
        role for role in ROLES.values()
        if role.team == team
    ]


def get_active_roles() -> list[Role]:
    """Tungi faol harakatga ega rollarni qaytaradi."""
    return [
        role for role in ROLES.values()
        if role.action is not None
    ]


def validate_roles() -> None:
    """Rol soni va jamoa taqsimotini tekshiradi."""
    expected = {
        Team.KRON: 12,
        Team.SOYA: 10,
        Team.YAKKA: 7,
        Team.LEGION: 7,
    }

    if len(ROLES) != 36:
        raise ValueError(
            f"36 ta rol bo'lishi kerak; topildi: {len(ROLES)}"
        )

    for team, expected_count in expected.items():
        actual_count = len(get_roles_by_team(team))

        if actual_count != expected_count:
            raise ValueError(
                f"{team.value}: {expected_count} ta rol kerak, "
                f"topildi {actual_count}"
            )


validate_roles()
