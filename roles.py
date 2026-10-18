from dataclasses import dataclass
from enum import Enum


class Team(str, Enum):
    KRON = "KRON"
    SOYA = "SOYA"
    YAKKA = "YAKKA"
    LEGION = "LEGION"


@dataclass(frozen=True, slots=True)
class Role:
    id: str
    name: str
    team: Team
    ability: str
    action: str | None
    win_condition: str
    passive: bool = False

    @property
    def key(self) -> str:
        return self.id


ROLES: dict[str, Role] = {
    # KRON — 12 ta rol
    "shoh": Role(
        "shoh", "Shoh", Team.KRON,
        "Dushman qobiliyatini to'sadi.",
        "block", "Soya tahdidlari yo'q qilinib, Shoh tirik qolsa."
    ),
    "malika": Role(
        "malika", "Malika", Team.KRON,
        "Saroy aloqalarini boshqaradi.",
        "influence", "KRON g'alaba qilsa."
    ),
    "shahzoda": Role(
        "shahzoda", "Shahzoda", Team.KRON,
        "Shoh halok bo'lsa, vorislik huquqi faollashadi.",
        "succession", "KRON g'alaba qilsa."
    ),
    "vazir": Role(
        "vazir", "Vazir", Team.KRON,
        "O'yinchini tekshiradi.",
        "investigate", "KRON g'alaba qilsa."
    ),
    "bosh_qomondon": Role(
        "bosh_qomondon", "Bosh qo'mondon", Team.KRON,
        "Harbiy hujum uyushtiradi.",
        "attack", "KRON g'alaba qilsa."
    ),
    "qirol_qorovuli": Role(
        "qirol_qorovuli", "Qirol qo'riqchisi", Team.KRON,
        "Tanlangan o'yinchini himoya qiladi.",
        "protect", "KRON g'alaba qilsa."
    ),
    "qozi": Role(
        "qozi", "Qozi", Team.KRON,
        "Sud va ovoz berishda maxsus vakolatga ega.",
        "judge", "KRON g'alaba qilsa."
    ),
    "xazinachi": Role(
        "xazinachi", "Xazinachi", Team.KRON,
        "Xazina ma'lumotlarini tekshiradi.",
        "inspect_treasury", "KRON g'alaba qilsa."
    ),
    "ritsar": Role(
        "ritsar", "Ritsar", Team.KRON,
        "Ittifoqchini qo'riqlaydi.",
        "guard", "KRON g'alaba qilsa."
    ),
    "xizmatkor": Role(
        "xizmatkor", "Xizmatkor", Team.KRON,
        "Tungi faoliyatni kuzatadi.",
        "observe", "KRON g'alaba qilsa."
    ),
    "tinch_aholi": Role(
        "tinch_aholi", "Tinch aholi", Team.KRON,
        "Maxsus tungi qobiliyati yo'q.",
        None, "KRON g'alaba qilsa.", passive=True
    ),
    "aygoqchi": Role(
        "aygoqchi", "Ayg'oqchi", Team.KRON,
        "O'yinchi faoliyatini kuzatadi.",
        "observe", "KRON g'alaba qilsa."
    ),

    # SOYA — 10 ta rol
    "soya_boshligi": Role(
        "soya_boshligi", "Soya boshlig'i", Team.SOYA,
        "Soya hujumini boshqaradi.",
        "team_attack", "SOYA g'alaba qilsa."
    ),
    "qotil": Role(
        "qotil", "Qotil", Team.SOYA,
        "Nishonga hujum qiladi.",
        "attack", "SOYA g'alaba qilsa."
    ),
    "josus": Role(
        "josus", "Josus", Team.SOYA,
        "Raqiblarni kuzatadi.",
        "observe", "SOYA g'alaba qilsa."
    ),
    "soxta_maslahatchi": Role(
        "soxta_maslahatchi", "Soxta maslahatchi", Team.SOYA,
        "Tekshiruvni chalg'itadi.",
        "mislead", "SOYA g'alaba qilsa."
    ),
    "xoin": Role(
        "xoin", "Xoin", Team.SOYA,
        "Raqiblarga xalaqit beradi.",
        "sabotage", "SOYA g'alaba qilsa."
    ),
    "qora_vazir": Role(
        "qora_vazir", "Qora vazir", Team.SOYA,
        "O'yinchi harakatini to'sadi.",
        "block", "SOYA g'alaba qilsa."
    ),
    "dushman_qiroli": Role(
        "dushman_qiroli", "Dushman qiroli", Team.SOYA,
        "Soya strategiyasini boshqaradi.",
        "team_attack", "SOYA g'alaba qilsa."
    ),
    "dushman_qomondoni": Role(
        "dushman_qomondoni", "Dushman qo'mondoni", Team.SOYA,
        "Kuchli hujum qiladi.",
        "attack", "SOYA g'alaba qilsa."
    ),
    "dushman_josusi": Role(
        "dushman_josusi", "Dushman josusi", Team.SOYA,
        "O'yinchi jamoasini aniqlaydi.",
        "investigate", "SOYA g'alaba qilsa."
    ),
    "dushman_suiqasdchisi": Role(
        "dushman_suiqasdchisi", "Dushman suiqasdchisi", Team.SOYA,
        "Himoyani chetlab hujum qiladi.",
        "hidden_attack", "SOYA g'alaba qilsa."
    ),

    # YAKKA — 7 ta rol
    "ovchi": Role(
        "ovchi", "Ovchi", Team.YAKKA,
        "Shaxsiy nishonini ovlaydi.",
        "attack", "Shaxsiy maqsadini bajarsa."
    ),
    "telba": Role(
        "telba", "Telba", Team.YAKKA,
        "Ovoz bilan chiqarib yuborilishga urinadi.",
        None, "Ovoz bilan chiqarilsa.", passive=True
    ),
    "sayyoh": Role(
        "sayyoh", "Sayyoh", Team.YAKKA,
        "Boshqa o'yinchiga tashrif buyuradi.",
        "visit", "Shaxsiy maqsadini bajarsa."
    ),
    "yollanma_jangchi": Role(
        "yollanma_jangchi", "Yollanma jangchi", Team.YAKKA,
        "Shartnoma bo'yicha hujum qiladi.",
        "contract_attack", "Shartnomasini bajarsa."
    ),
    "surgun_shahzoda": Role(
        "surgun_shahzoda", "Surgun shahzoda", Team.YAKKA,
        "Omon qolishga va maqsadini bajarishga urinadi.",
        "survive", "Shaxsiy maqsadini bajarsa."
    ),
    "taxt_davogari": Role(
        "taxt_davogari", "Taxt da'vogari", Team.YAKKA,
        "Taxtni egallashga urinadi.",
        "claim_throne", "Taxtni egallasa."
    ),
    "qaroqchi": Role(
        "qaroqchi", "Qaroqchi", Team.YAKKA,
        "Resurs o'g'irlashga urinadi.",
        "steal_gold", "Shaxsiy o'lja maqsadini bajarsa."
    ),

    # LEGION — 7 ta rol
    "tabib": Role(
        "tabib", "Tabib", Team.LEGION,
        "Tanlangan o'yinchiga yordam beradi.",
        "heal", "LEGION g'alaba qilsa."
    ),
    "kuzatuvchi": Role(
        "kuzatuvchi", "Kuzatuvchi", Team.LEGION,
        "Tungi faoliyatni kuzatadi.",
        "observe", "LEGION g'alaba qilsa."
    ),
    "qorovul": Role(
        "qorovul", "Qorovul", Team.LEGION,
        "O'yinchini qo'riqlaydi.",
        "guard", "LEGION g'alaba qilsa."
    ),
    "solnomachi": Role(
        "solnomachi", "Solnomachi", Team.LEGION,
        "Oldingi voqealarni tekshiradi.",
        "memory_check", "LEGION g'alaba qilsa."
    ),
    "savdogar": Role(
        "savdogar", "Savdogar", Team.LEGION,
        "Savdo orqali foyda olishga urinadi.",
        "trade", "LEGION g'alaba qilsa."
    ),
    "suiqasdchi": Role(
        "suiqasdchi", "Suiqasdchi", Team.LEGION,
        "Yashirin hujum uyushtiradi.",
        "hidden_attack", "LEGION g'alaba qilsa."
    ),
    "oshpaz": Role(
        "oshpaz", "Oshpaz", Team.LEGION,
        "Tanlangan o'yinchiga ovqat yuboradi.",
        "feed", "LEGION g'alaba qilsa."
    ),
}


def get_all_roles() -> list[Role]:
    return list(ROLES.values())


def get_role(role_id: str) -> Role | None:
    return ROLES.get(role_id)


def get_roles_by_team(team: Team) -> list[Role]:
    return [role for role in ROLES.values() if role.team == team]


def get_active_roles() -> list[Role]:
    return [role for role in ROLES.values() if role.action is not None]


def validate_roles() -> None:
    expected = {
        Team.KRON: 12,
        Team.SOYA: 10,
        Team.YAKKA: 7,
        Team.LEGION: 7,
    }

    if len(ROLES) != 36:
        raise ValueError(f"36 ta rol kerak; topildi: {len(ROLES)}")

    for team, count in expected.items():
        actual = len(get_roles_by_team(team))
        if actual != count:
            raise ValueError(
                f"{team.value}: {count} ta rol kerak; topildi: {actual}"
            )


validate_roles()
