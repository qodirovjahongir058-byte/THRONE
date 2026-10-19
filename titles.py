
from __future__ import annotations

from dataclasses import dataclass


class TitleError(Exception):
    """Unvonlar tizimidagi xato."""


@dataclass(frozen=True, slots=True)
class Title:
    id: str
    name: str
    description: str
    min_rp: int
    min_level: int


TITLES: dict[str, Title] = {
    "NOVICE": Title(
        id="NOVICE",
        name="Novice",
        description="THRONE olamidagi yangi o'yinchi.",
        min_rp=0,
        min_level=1,
    ),
    "VETERAN": Title(
        id="VETERAN",
        name="Veteran",
        description="Tajribali o'yinchi.",
        min_rp=1000,
        min_level=11,
    ),
    "CHAMPION": Title(
        id="CHAMPION",
        name="Champion",
        description="Yuqori natijalarga erishgan o'yinchi.",
        min_rp=3000,
        min_level=31,
    ),
    "ROYAL": Title(
        id="ROYAL",
        name="Royal",
        description="Qirollik darajasidagi o'yinchi.",
        min_rp=6000,
        min_level=61,
    ),
    "ELITE": Title(
        id="ELITE",
        name="Elite",
        description="Elita darajasidagi o'yinchi.",
        min_rp=9000,
        min_level=91,
    ),
}

TITLE_ORDER = (
    "NOVICE",
    "VETERAN",
    "CHAMPION",
    "ROYAL",
    "ELITE",
)


def get_title(title_id: str) -> Title:
    """Unvonni ID orqali qaytaradi."""

    title_id = title_id.upper().strip()

    if title_id == "CREATOR":
        return Title(
            id="CREATOR",
            name="Creator",
            description="THRONE loyihasi egasi.",
            min_rp=0,
            min_level=1,
        )

    try:
        return TITLES[title_id]
    except KeyError as exc:
        raise TitleError(
            f"Noma'lum unvon: {title_id}"
        ) from exc


def calculate_level(rp: int) -> int:
    """RP asosida 1–100 darajani hisoblaydi."""

    if rp < 0:
        raise ValueError("RP manfiy bo'lishi mumkin emas.")

    return min(100, (rp // 100) + 1)


def get_title_for_player(
    rp: int,
    creator_id: int,
    user_id: int,
) -> Title:
    """O'yinchi uchun mos unvonni aniqlaydi."""

    if user_id == creator_id:
        return get_title("CREATOR")

    if rp < 0:
        raise ValueError("RP manfiy bo'lishi mumkin emas.")

    level = calculate_level(rp)

    for title_id in reversed(TITLE_ORDER):
        title = TITLES[title_id]

        if rp >= title.min_rp and level >= title.min_level:
            return title

    return TITLES["NOVICE"]


def get_all_titles() -> list[Title]:
    """Barcha oddiy unvonlarni tartib bilan qaytaradi."""

    return [TITLES[title_id] for title_id in TITLE_ORDER]


def is_creator(
    user_id: int,
    creator_id: int,
) -> bool:
    """Foydalanuvchi loyiha egasi ekanini tekshiradi."""

    return user_id == creator_id


def title_progress(rp: int) -> dict[str, int | str | None]:
    """Keyingi unvongacha qancha RP kerakligini ko'rsatadi."""

    current = get_title_for_player(
        rp=rp,
        creator_id=-1,
        user_id=0,
    )

    current_index = TITLE_ORDER.index(current.id)

    if current_index == len(TITLE_ORDER) - 1:
        return {
            "current_title": current.id,
            "next_title": None,
            "current_rp": rp,
            "required_rp": current.min_rp,
            "rp_remaining": 0,
        }

    next_title = TITLES[TITLE_ORDER[current_index + 1]]

    return {
        "current_title": current.id,
        "next_title": next_title.id,
        "current_rp": rp,
        "required_rp": next_title.min_rp,
        "rp_remaining": max(0, next_title.min_rp - rp),
    }


def validate_titles() -> bool:
    """Unvonlar sozlamalarini tekshiradi."""

    if not TITLE_ORDER:
        raise TitleError("Unvonlar ro'yxati bo'sh.")

    previous_rp = -1
    previous_level = 0

    for title_id in TITLE_ORDER:
        title = TITLES.get(title_id)

        if title is None:
            raise TitleError(
                f"{title_id} unvoni TITLES ichida mavjud emas."
            )

        if title.min_rp < previous_rp:
            raise TitleError("RP chegaralari tartib bilan oshishi kerak.")

        if title.min_level < previous_level:
            raise TitleError(
                "Daraja chegaralari tartib bilan oshishi kerak."
            )

        previous_rp = title.min_rp
        previous_level = title.min_level

    return True


validate_titles()
