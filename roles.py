from dataclasses import dataclass
from enum import Enum


class Team(str, Enum):
    KRON = "KRON"
    SOYA = "SOYA"
    ISYON = "ISYON"
    MUSTAQIL = "MUSTAQIL"

    # Eski kodlar bilan vaqtinchalik moslik
    YAKKA = "YAKKA"
    LEGION = "LEGION"


class RoleSide(str, Enum):
    KRON = "KRON"
    SOYA = "SOYA"
    ISYON = "ISYON"
    MUSTAQIL = "MUSTAQIL"


class RoleAbilityType(str, Enum):
    INFORMATION = "information"
    PROTECTION = "protection"
    CONTROL = "control"
    ATTACK = "attack"
    ECONOMY = "economy"
    SPECIAL = "special"
    PASSIVE = "passive"


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

    @property
    def side(self) -> RoleSide:
        return RoleSide(self.team.value)

    @property
    def victory_condition(self) -> str:
        return self.win_condition

    @property
    def ability_type(self) -> RoleAbilityType:
        if self.passive or self.action is None:
            return RoleAbilityType.PASSIVE

        if self.action in {
            "investigate", "observe", "memory_check"
        }:
            return RoleAbilityType.INFORMATION

        if self.action in {"protect", "guard", "heal"}:
            return RoleAbilityType.PROTECTION

        if self.action == "block":
            return RoleAbilityType.CONTROL

        if self.action in {
            "attack", "team_attack", "hidden_attack",
            "attack_bypass", "contract_attack"
        }:
            return RoleAbilityType.ATTACK

        if self.action in {"steal_gold", "trade"}:
            return RoleAbilityType.ECONOMY

        return RoleAbilityType.SPECIAL


RoleDefinition = Role


ROLES: dict[str, Role] = {
    # KRON — 12 ta
    "shoh": Role(
        "shoh", "Shoh", Team.KRON,
        "Tunda bir qobiliyatni to‘sadi va kuchli himoyaga ega.",
        "block", "Soya tahdidlari yo‘q qilinib, Shoh tirik qolsa."
    ),
    "malika": Role(
        "malika", "Malika", Team.KRON,
        "Saroydagi ittifoqlarni boshqaradi.",
        "influence", "KRON g‘alaba qilsa."
    ),
    "shahzoda": Role(
        "shahzoda", "Shahzoda", Team.KRON,
        "Shoh halok bo‘lganda vorislik huquqiga ega.",
        "succession", "KRON g‘alaba qilsa."
    ),
    "vazir": Role(
        "vazir", "Vazir", Team.KRON,
        "Tanlangan o‘yinchini tekshiradi.",
        "investigate", "KRON g‘alaba qilsa."
    ),
    "bosh_qomondon": Role(
        "bosh_qomondon", "Bosh qo‘mondon", Team.KRON,
        "Dushmanga hujum qiladi.",
        "attack", "KRON g‘alaba qilsa."
    ),
    "qirol_qorovuli": Role(
        "qirol_qorovuli", "Qirol qo‘riqchisi", Team.KRON,
        "Tanlangan o‘yinchini himoya qiladi.",
        "protect", "KRON g‘alaba qilsa."
    ),
    "qozi": Role(
        "qozi", "Qozi", Team.KRON,
        "Sud va ovoz berish bilan bog‘liq vakolatga ega.",
        "judge", "KRON g‘alaba qilsa."
    ),
    "xazinachi": Role(
        "xazinachi", "Xazinachi", Team.KRON,
        "Xazina ma’lumotlarini tekshiradi.",
        "inspect_treasury", "KRON g‘alaba qilsa."
    ),
    "ritsar": Role(
        "ritsar", "Ritsar", Team.KRON,
        "Tanlangan ittifoqchini qo‘riqlaydi.",
        "guard", "KRON g‘alaba qilsa."
    ),
    "xizmatkor": Role(
        "xizmatkor", "Xizmatkor", Team.KRON,
        "Tungi faoliyatni kuzatadi.",
        "observe", "KRON g‘alaba qilsa."
    ),
    "tinch_aholi": Role(
        "tinch_aholi", "Tinch aholi", Team.KRON,
        "Maxsus tungi qobiliyati yo‘q.",
        None, "KRON g‘alaba qilsa.", passive=True
    ),
    "aygoqchi": Role(
        "aygoqchi", "Ayg‘oqchi", Team.KRON,
        "O‘yinchilarning tungi harakatlarini kuzatadi.",
        "observe", "KRON g‘alaba qilsa."
    ),

    # SOYA — 10 ta
    "soya_boshligi": Role(
        "soya_boshligi", "Soya boshlig‘i", Team.SOYA,
        "Soya jamoasining hujumini boshqaradi.",
        "team_attack", "SOYA g‘alaba qilsa."
    ),
    "qotil": Role(
        "qotil", "Qotil", Team.SOYA,
        "Tanlangan nishonga hujum qiladi.",
        "attack", "SOYA g‘alaba qilsa."
    ),
    "josus": Role(
        "josus", "Josus", Team.SOYA,
        "Raqiblarning harakatlarini kuzatadi.",
        "observe", "SOYA g‘alaba qilsa."
    ),
    "soxta_maslahatchi": Role(
        "soxta_maslahatchi", "Soxta maslahatchi", Team.SOYA,
        "Tekshiruv natijalarini chalg‘itishga mo‘ljallangan.",
        "mislead", "SOYA g‘alaba qilsa."
    ),
    "xoin": Role(
        "xoin", "Xoin", Team.SOYA,
        "Raqiblar faoliyatiga xalaqit beradi.",
        "sabotage", "SOYA g‘alaba qilsa."
    ),
    "qora_vazir": Role(
        "qora_vazir", "Qora vazir", Team.SOYA,
        "Tanlangan o‘yinchining harakatini to‘sadi.",
        "block", "SOYA g‘alaba qilsa."
    ),
    "dushman_qiroli": Role(
        "dushman_qiroli", "Dushman qiroli", Team.SOYA,
        "Soya jamoasining strategiyasini boshqaradi.",
        "team_attack", "SOYA g‘alaba qilsa."
    ),
    "dushman_qomondoni": Role(
        "dushman_qomondoni", "Dushman qo‘mondoni", Team.SOYA,
        "Tanlangan nishonga hujum qiladi.",
        "attack", "SOYA g‘alaba qilsa."
    ),
    "dushman_josusi": Role(
        "dushman_josusi", "Dushman josusi", Team.SOYA,
        "O‘yinchining jamoasini aniqlaydi.",
        "investigate", "SOYA g‘alaba qilsa."
    ),
    "dushman_suiqasdchisi": Role(
        "dushman_suiqasdchisi", "Dushman suiqasdchisi", Team.SOYA,
        "Himoyani chetlab o‘tuvchi hujum qiladi.",
        "hidden_attack", "SOYA g‘alaba qilsa."
    ),

    # ISYON — 10 ta
    "isyon_boshligi": Role(
        "isyon_boshligi", "Isyon boshlig‘i", Team.ISYON,
        "Isyonchilar hujumini boshqaradi.",
        "team_attack", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "isyonchi": Role(
        "isyonchi", "Isyonchi", Team.ISYON,
        "Tanlangan nishonga hujum qiladi.",
        "attack", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "fitnachi": Role(
        "fitnachi", "Fitnachi", Team.ISYON,
        "Raqiblar rejasini buzadi.",
        "sabotage", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "sobiq_general": Role(
        "sobiq_general", "Sobiq general", Team.ISYON,
        "Harbiy tajribasi orqali hujum qiladi.",
        "attack", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "qora_bozorchi": Role(
        "qora_bozorchi", "Qora bozorchi", Team.ISYON,
        "Nishondan resurs o‘g‘irlashga urinadi.",
        "steal_gold", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "isyon_josusi": Role(
        "isyon_josusi", "Isyon josusi", Team.ISYON,
        "Tanlangan o‘yinchini tekshiradi.",
        "investigate", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "sabotajchi": Role(
        "sabotajchi", "Sabotajchi", Team.ISYON,
        "Raqiblar faoliyatiga xalaqit beradi.",
        "sabotage", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "isyon_qorovuli": Role(
        "isyon_qorovuli", "Isyon qorovuli", Team.ISYON,
        "Tanlangan o‘yinchini qo‘riqlaydi.",
        "guard", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "targibotchi": Role(
        "targibotchi", "Targ‘ibotchi", Team.ISYON,
        "Ovoz va ta’sir bilan bog‘liq qobiliyatga ega.",
        "influence", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),
    "qochqin": Role(
        "qochqin", "Qochqin", Team.ISYON,
        "Omon qolishga urinadi.",
        "survive", "Isyonchilar maxsus g‘alaba shartini bajarsa."
    ),

    # MUSTAQIL — 4 ta
    "ovchi": Role(
        "ovchi", "Ovchi", Team.MUSTAQIL,
        "Shaxsiy nishonini ovlaydi.",
        "contract_attack", "Shaxsiy ov maqsadini bajarsa."
    ),
    "telba": Role(
        "telba", "Telba", Team.MUSTAQIL,
        "Ovoz berishda o‘yindan chiqarilsa, g‘alaba qiladi.",
        None, "Ovoz berish orqali chiqarilsa.", passive=True
    ),
    "yollanma_jangchi": Role(
        "yollanma_jangchi", "Yollanma jangchi", Team.MUSTAQIL,
        "Shartnoma asosida nishonga hujum qiladi.",
        "contract_attack", "Shartnomasini bajarsa."
    ),
    "taxt_davogari": Role(
        "taxt_davogari", "Taxt da’vogari", Team.MUSTAQIL,
        "Taxtni egallash uchun kurashadi.",
        "claim_throne", "Shaxsiy taxt maqsadini bajarsa."
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
        Team.ISYON: 10,
        Team.MUSTAQIL: 4,
    }

    if len(ROLES) != 36:
        raise ValueError(
            f"36 ta rol kerak; topildi: {len(ROLES)}"
        )

    if len(set(ROLES)) != len(ROLES):
        raise ValueError("Takrorlangan rol ID mavjud.")

    for team, count in expected.items():
        actual = len(get_roles_by_team(team))
        if actual != count:
            raise ValueError(
                f"{team.value}: {count} ta rol kerak; topildi: {actual}"
            )


validate_roles()
