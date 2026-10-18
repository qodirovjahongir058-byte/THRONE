
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from game_actions import ActionResult, GameActionManager
from game_engine import Game, GamePhase
from roles import get_role


# O'ziga hujum qilish mumkin bo'lmagan harakatlar.
NO_SELF_ATTACK = {
    "attack",
    "team_attack",
    "hidden_attack",
    "contract_attack",
}


def build_night_action_keyboard(
    game: Game,
    actor_id: int,
) -> InlineKeyboardMarkup | None:
    """O'yinchining tungi harakati uchun tugmalar yaratadi."""

    if game.phase != GamePhase.NIGHT:
        return None

    actor = game.players.get(actor_id)

    if actor is None or not actor.alive:
        return None

    role = get_role(actor.role_id or "")

    if role is None or role.action is None:
        return None

    action_type = role.action

    # Nishonsiz bajariladigan harakatlar.
    if action_type in GameActionManager.NON_TARGET_ACTIONS:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🌙 Harakatni tasdiqlash",
                        callback_data=(
                            f"throne_night|{game.game_id}|"
                            f"{action_type}|0"
                        ),
                    )
                ]
            ]
        )

    # Tirik o'yinchilarni nishon sifatida ko'rsatamiz.
    buttons = []

    for target in game.alive_players:
        if (
            target.user_id == actor_id
            and action_type in NO_SELF_ATTACK
        ):
            continue

        buttons.append(
            InlineKeyboardButton(
                text=f"👤 {target.name[:35]}",
                callback_data=(
                    f"throne_night|{game.game_id}|"
                    f"{action_type}|{target.user_id}"
                ),
            )
        )

    # Har qatorda ikkita o'yinchi tugmasi.
    rows = [
        buttons[index:index + 2]
        for index in range(0, len(buttons), 2)
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="❌ Harakatni bekor qilish",
                callback_data=(
                    f"throne_cancel|{game.game_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def submit_night_action(
    game: Game,
    actor_id: int,
    action_type: str,
    target_id: int | None,
) -> ActionResult:
    """Tanlangan tungi harakatni mavjud menejer orqali tekshiradi."""

    return GameActionManager.submit_action(
        game=game,
        actor_id=actor_id,
        action_type=action_type,
        target_id=target_id,
    )


def parse_night_action_callback(
    callback_data: str,
) -> tuple[str, str, int] | None:
    """Tungi tugma ma'lumotini xavfsiz ajratadi."""

    parts = callback_data.split("|")

    if len(parts) != 4 or parts[0] != "throne_night":
        return None

    game_id = parts[1]
    action_type = parts[2]

    try:
        target_id = int(parts[3])
    except ValueError:
        return None

    if not game_id or target_id < 0:
        return None

    return game_id, action_type, target_id
