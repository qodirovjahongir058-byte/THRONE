from future import annotations
import html import logging from dataclasses import dataclass from typing import Awaitable, Callable
from game_actions import GameAction from game_engine import GameState from game_messages import ( day_started_message, discussion_started_message, game_finished_message, night_started_message, voting_started_message, ) from game_resolver import resolve_night from game_scheduler import game_scheduler from game_state import ( DEFAULT_DISCUSSION_DURATION, DEFAULT_NIGHT_DURATION, DEFAULT_VOTING_DURATION, GamePhase, GameStatus, VoteResult, ) from game_victory import check_victory from keyboards import voting_keyboard from last_words import last_words_system from phase_manager import phase_manager from vote_system import VoteResolution, vote_system
logger = logging.getLogger("throne.game_flow")
SendMessage = Callable[..., Awaitable[object]] SendPrivateMessage = Callable[[int, str], Awaitable[object]]
LAST_WORDS_DURATION = 30
@dataclass(frozen=True, slots=True) class FlowResult: success: bool message: str
class GameFlow: """THRONE o'yinining asosiy bosqichlarini boshqaradi."""
def __init__(self) -> None:
    self._games: dict[int, GameState] = {}
    self._private_senders: dict[int, SendPrivateMessage] = {}

# =========================================================
# O'YINNI RO'YXATGA OLISH
# =========================================================

def register_game(self, game: GameState) -> None:
    self._games[game.game_id] = game
    game.metadata.setdefault("night_actions", [])

def unregister_game(self, game_id: int) -> None:
    game_scheduler.cancel(game_id)
    self._games.pop(game_id, None)
    self._private_senders.pop(game_id, None)

def get_game(self, game_id: int) -> GameState | None:
    return self._games.get(game_id)

# =========================================================
# TUNGI HARAKATLAR
# =========================================================

def submit_night_action(
    self,
    game: GameState,
    action: GameAction,
) -> FlowResult:
    if game.status != GameStatus.ACTIVE:
        return FlowResult(False, "game_not_active")

    if game.phase != GamePhase.NIGHT:
        return FlowResult(False, "night_not_active")

    actor = game.get_player(action.actor_id)

    if actor is None:
        return FlowResult(False, "player_not_found")

    if not actor.alive:
        return FlowResult(False, "player_not_alive")

    if actor.blocked:
        return FlowResult(False, "player_blocked")

    if actor.has_acted:
        return FlowResult(False, "action_already_submitted")

    if action.target_id is not None:
        target = game.get_player(action.target_id)

        if target is None:
            return FlowResult(False, "target_not_found")

        if not target.alive:
            return FlowResult(False, "target_not_alive")

    actions = game.metadata.setdefault("night_actions", [])

    # Bir o'yinchining bir nechta harakati saqlanib qolmasin.
    actions[:] = [
        existing
        for existing in actions
        if existing.actor_id != action.actor_id
    ]

    actions.append(action)

    actor.has_acted = True
    actor.metadata["night_action"] = action.action_type.value
    actor.metadata["night_target"] = action.target_id

    return FlowResult(True, "night_action_saved")

def get_night_actions(self, game: GameState) -> list[GameAction]:
    return list(game.metadata.get("night_actions", []))

def clear_night_actions(self, game: GameState) -> None:
    game.metadata["night_actions"] = []

def _reset_player_night_flags(self, game: GameState) -> None:
    for player in game.players.values():
        player.has_acted = False
        player.metadata.pop("night_action", None)
        player.metadata.pop("night_target", None)
# =========================================================
# BIRINCHI TUN
# =========================================================

async def start_first_night(
    self,
    game: GameState,
    send_message: SendMessage,
    send_private_message: SendPrivateMessage | None = None,
) -> FlowResult:
    if send_private_message is not None:
        self._private_senders[game.game_id] = send_private_message

    result = phase_manager.start_first_night(game)

    if not result.success:
        return FlowResult(False, result.message)

    self.register_game(game)
    self.clear_night_actions(game)
    self._reset_player_night_flags(game)

    await send_message(
        night_started_message(game.night_number)
    )

    self._schedule_night(game, send_message)

    return FlowResult(True, "first_night_started")

def _schedule_night(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    game_scheduler.schedule(
        game_id=game.game_id,
        phase_name=GamePhase.NIGHT.value,
        duration=DEFAULT_NIGHT_DURATION,
        callback=lambda: self._finish_night(game, send_message),
    )
# =========================================================
# TUNNI YAKUNLASH
# =========================================================

async def _finish_night(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    if (
        game.status != GameStatus.ACTIVE
        or game.phase != GamePhase.NIGHT
    ):
        return

    try:
        resolution = resolve_night(
            game=game,
            actions=self.get_night_actions(game),
        )
    except Exception:
        logger.exception(
            "Tungi harakatlarni hisoblashda xatolik: game_id=%s",
            game.game_id,
        )

        self.clear_night_actions(game)
        self._reset_player_night_flags(game)

        await send_message(
            "⚠️ <b>Tungi harakatlarni hisoblashda xatolik yuz berdi.</b>\n\n"
            "Bu tun natijasi bekor qilindi. O'yin davom etadi."
        )

        day_result = phase_manager.start_day(game)

        if not day_result.success:
            logger.error(
                "Kunduzni boshlash amalga oshmadi: game_id=%s",
                game.game_id,
            )
            return

        await send_message(
            day_started_message(game.night_number)
        )

        victory = check_victory(game)

        if victory.finished:
            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return

        await self.start_discussion(game, send_message)
        return

    eliminated = list(resolution.eliminated_player_ids)

    game.metadata["last_night_results"] = list(
        resolution.context.results
    )
    game.metadata["last_night_eliminated"] = eliminated

    self.clear_night_actions(game)
    self._reset_player_night_flags(game)

    day_result = phase_manager.start_day(game)

    if not day_result.success:
        logger.error(
            "Kunduzni boshlash amalga oshmadi: game_id=%s, reason=%s",
            game.game_id,
            day_result.message,
        )
        return

    await send_message(
        day_started_message(game.night_number)
    )

    if eliminated:
        names: list[str] = []

        for player_id in eliminated:
            player = game.get_player(player_id)

            if player is not None:
                names.append(
                    html.escape(
                        player.display_name or str(player.user_id)
                    )
                )

        if names:
            await send_message(
                "🌅 <b>Tun yakuni</b>\n\n"
                "⚔️ Bu tun o'yindan chiqarilganlar:\n"
                + "\n".join(f"• {name}" for name in names)
            )

        game.metadata["last_words_queue"] = eliminated[1:]
        game.metadata["last_words_next_phase"] = (
            GamePhase.DISCUSSION.value
        )

        await self._start_last_words(
            game=game,
            player_id=eliminated[0],
            send_message=send_message,
            next_phase=GamePhase.DISCUSSION,
        )
        return

    victory = check_victory(game)

    if victory.finished:
        await self._finish_game(
            game,
            victory.winning_side.value,
            victory.reason,
            send_message,
        )
        return

    await self.start_discussion(game, send_message)
# =========================================================
# SO'NGGI SO'Z
# =========================================================

async def _start_last_words(
    self,
    game: GameState,
    player_id: int,
    send_message: SendMessage,
    *,
    next_phase: GamePhase,
) -> None:
    if game.status != GameStatus.ACTIVE:
        return

    result = last_words_system.start(
        game=game,
        player_id=player_id,
    )

    if not result.success:
        logger.warning(
            "So'nggi so'z boshlanmadi: game_id=%s, player_id=%s, reason=%s",
            game.game_id,
            player_id,
            result.message,
        )

        await self._continue_after_last_words(
            game,
            send_message,
            next_phase,
        )
        return

    player = game.get_player(player_id)

    if player is None:
        last_words_system.finish(game)

        await self._continue_after_last_words(
            game,
            send_message,
            next_phase,
        )
        return

    game.metadata["last_words_next_phase"] = next_phase.value

    player_name = html.escape(
        player.display_name or str(player.user_id)
    )

    private_sender = self._private_senders.get(game.game_id)

    if private_sender is not None:
        try:
            await private_sender(
                player_id,
                "🕯️ <b>So'nggi so'z</b>\n\n"
                f"⏳ Sizda {LAST_WORDS_DURATION} soniya bor.\n"
                "So'nggi so'zingizni shu shaxsiy chatga yuboring.",
            )
        except Exception:
            logger.exception(
                "So'nggi so'z uchun shaxsiy xabar yuborilmadi: player_id=%s",
                player_id,
            )

            await send_message(
                "⚠️ <b>So'nggi so'z haqida shaxsiy xabar yuborilmadi.</b>"
            )
    else:
        await send_message(
            "⚠️ <b>So'nggi so'z uchun shaxsiy xabar yuboruvchi "
            "sozlanmagan.</b>"
        )

    await send_message(
        "🕯️ <b>So'nggi so'z boshlandi.</b>\n\n"
        f"👤 {player_name} so'nggi so'zini aytmoqda."
    )

    game_scheduler.schedule(
        game_id=game.game_id,
        phase_name=GamePhase.LAST_WORDS.value,
        duration=LAST_WORDS_DURATION,
        callback=lambda: self._finish_last_words(
            game,
            send_message,
        ),
    )

async def _finish_last_words(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    if (
        game.status != GameStatus.ACTIVE
        or game.phase != GamePhase.LAST_WORDS
    ):
        return

    player_id = game.last_words_player_id
    saved_text = game.metadata.get("last_words_text")

    last_words_system.finish(game)

    if player_id is not None:
        player = game.get_player(player_id)

        if player is not None:
            player_name = html.escape(
                player.display_name or str(player.user_id)
            )

            if saved_text:
                safe_text = html.escape(str(saved_text))

                await send_message(
                    "🕯️ <b>So'nggi so'z</b>\n\n"
                    f"👤 <b>{player_name}</b>:\n"
                    f"“{safe_text}”"
                )
            else:
                await send_message(
                    "🕯️ <b>So'nggi so'z vaqti tugadi.</b>\n\n"
                    f"👤 {player_name} so'z qoldirmadi."
                )

    queue = game.metadata.get("last_words_queue", [])

    if queue:
        next_player_id = queue.pop(0)
        game.metadata["last_words_queue"] = queue

        next_phase_value = game.metadata.get(
            "last_words_next_phase",
            GamePhase.DISCUSSION.value,
        )

        try:
            next_phase = GamePhase(next_phase_value)
        except ValueError:
            next_phase = GamePhase.DISCUSSION

        await self._start_last_words(
            game=game,
            player_id=next_player_id,
            send_message=send_message,
            next_phase=next_phase,
        )
        return

    game.metadata.pop("last_words_queue", None)

    next_phase_value = game.metadata.pop(
        "last_words_next_phase",
        GamePhase.DISCUSSION.value,
    )

    try:
        next_phase = GamePhase(next_phase_value)
    except ValueError:
        next_phase = GamePhase.DISCUSSION

    await self._continue_after_last_words(
        game,
        send_message,
        next_phase,
    )

async def _continue_after_last_words(
    self,
    game: GameState,
    send_message: SendMessage,
    next_phase: GamePhase,
) -> None:
    if game.status != GameStatus.ACTIVE:
        return

    victory = check_victory(game)

    if victory.finished:
        await self._finish_game(
            game,
            victory.winning_side.value,
            victory.reason,
            send_message,
        )
        return

    if next_phase == GamePhase.NIGHT:
        await self._start_next_night(game, send_message)
    else:
        await self.start_discussion(game, send_message)
# =========================================================
# MUHOKAMA
# =========================================================

async def start_discussion(
    self,
    game: GameState,
    send_message: SendMessage,
) -> FlowResult:
    if game.status != GameStatus.ACTIVE:
        return FlowResult(False, "game_not_active")

    result = phase_manager.start_discussion(game)

    if not result.success:
        return FlowResult(False, result.message)

    await send_message(
        discussion_started_message()
    )

    game_scheduler.schedule(
        game_id=game.game_id,
        phase_name=GamePhase.DISCUSSION.value,
        duration=DEFAULT_DISCUSSION_DURATION,
        callback=lambda: self._finish_discussion(
            game,
            send_message,
        ),
    )

    return FlowResult(True, "discussion_started")

async def _finish_discussion(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    if (
        game.status != GameStatus.ACTIVE
        or game.phase != GamePhase.DISCUSSION
    ):
        return

    await self.start_voting(game, send_message)
# =========================================================
# OVOZ BERISH
# =========================================================

async def start_voting(
    self,
    game: GameState,
    send_message: SendMessage,
) -> FlowResult:
    if game.status != GameStatus.ACTIVE:
        return FlowResult(False, "game_not_active")

    result = phase_manager.start_voting(game)

    if not result.success:
        return FlowResult(False, result.message)

    targets = [
        (
            player.user_id,
            html.escape(
                player.display_name or f"User {player.user_id}"
            ),
        )
        for player in game.alive_players()
    ]

    if len(targets) < 2:
        victory = check_victory(game)

        if victory.finished:
            await self._finish_game(
                game,
                victory.winning_side.value,
                victory.reason,
                send_message,
            )
            return FlowResult(True, "game_finished")

    await send_message(
        voting_started_message(),
        reply_markup=voting_keyboard(targets),
    )

    game_scheduler.schedule(
        game_id=game.game_id,
        phase_name=GamePhase.VOTING.value,
        duration=DEFAULT_VOTING_DURATION,
        callback=lambda: self._finish_voting(
            game,
            send_message,
        ),
    )

    return FlowResult(True, "voting_started")

async def _finish_voting(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    if (
        game.status != GameStatus.ACTIVE
        or game.phase != GamePhase.VOTING
    ):
        return

    # Qayta ovoz berish bo'lsa, ikkinchi natijani hisoblaymiz.
    if game.metadata.get("revote"):
        resolution = vote_system.resolve_revote(game)
    else:
        resolution = vote_system.resolve_votes(game)

    if resolution.result == VoteResult.REVOTE:
        vote_system.start_revote(
            game,
            resolution.tied_player_ids,
        )

        targets = []

        for player_id in resolution.tied_player_ids:
            player = game.get_player(player_id)

            if player is not None and player.alive:
                targets.append(
                    (
                        player.user_id,
                        html.escape(
                            player.display_name
                            or f"User {player.user_id}"
                        ),
                    )
                )

        if not targets:
            await self._process_vote_result(
                game,
                VoteResolution(
                    result=VoteResult.NO_ELIMINATION,
                    eliminated_player_id=None,
                    tied_player_ids=(),
                    vote_counts={},
                ),
                send_message,
            )
            return

        await send_message(
            "⚖️ <b>Ovozlar teng keldi.</b>\n\n"
            "Qayta ovoz berish boshlandi.\n"
            "Faqat teng ovoz olgan nomzodlardan birini tanlang.",
            reply_markup=voting_keyboard(targets),
        )

        game_scheduler.schedule(
            game_id=game.game_id,
            phase_name=GamePhase.VOTING.value,
            duration=DEFAULT_VOTING_DURATION,
            callback=lambda: self._finish_voting(
                game,
                send_message,
            ),
        )
        return

    await self._process_vote_result(
        game,
        resolution,
        send_message,
    )

async def _process_vote_result(
    self,
    game: GameState,
    resolution: VoteResolution,
    send_message: SendMessage,
) -> None:
    game.metadata.pop("revote", None)
    game.metadata.pop("revote_targets", None)

    if game.status != GameStatus.ACTIVE:
        return

    if resolution.result == VoteResult.ELIMINATED:
        player_id = resolution.eliminated_player_id
        player = (
            game.get_player(player_id)
            if player_id is not None
            else None
        )

        if player is not None:
            player_name = html.escape(
                player.display_name or str(player.user_id)
            )

            await send_message(
                f"⚔️ <b>{player_name}</b> ovoz berish orqali "
                "o'yindan chiqarildi."
            )

            await self._start_last_words(
                game=game,
                player_id=player.user_id,
                send_message=send_message,
                next_phase=GamePhase.NIGHT,
            )
            return

    await send_message(
        "⚖️ <b>Bu safar hech kim o'yindan chiqarilmadi.</b>"
    )

    victory = check_victory(game)

    if victory.finished:
        await self._finish_game(
            game,
            victory.winning_side.value,
            victory.reason,
            send_message,
        )
        return

    await self._start_next_night(game, send_message)
# =========================================================
# KEYINGI TUN
# =========================================================

async def _start_next_night(
    self,
    game: GameState,
    send_message: SendMessage,
) -> None:
    if game.status != GameStatus.ACTIVE:
        return

    victory = check_victory(game)

    if victory.finished:
        await self._finish_game(
            game,
            victory.winning_side.value,
            victory.reason,
            send_message,
        )
        return

    result = phase_manager.start_next_night(game)

    if not result.success:
        logger.error(
            "Keyingi tun boshlanmadi: game_id=%s, sabab=%s",
            game.game_id,
            result.message,
        )
        return

    self.clear_night_actions(game)
    self._reset_player_night_flags(game)

    await send_message(
        night_started_message(game.night_number)
    )

    self._schedule_night(game, send_message)
# =========================================================
# O'YINNI YAKUNLASH
# =========================================================

async def _finish_game(
    self,
    game: GameState,
    winning_side: str,
    reason: str,
    send_message: SendMessage,
) -> None:
    if game.status != GameStatus.ACTIVE:
        return

    phase_manager.finish(game)
    game_scheduler.cancel(game.game_id)

    try:
        await send_message(
            game_finished_message(
                winning_side=winning_side,
                reason=reason,
            )
        )
    except Exception:
        logger.exception(
            "O'yin yakuni xabari yuborilmadi: game_id=%s",
            game.game_id,
        )
    finally:
        self.unregister_game(game.game_id)

async def stop_game(
    self,
    game: GameState,
    send_message: SendMessage,
) -> FlowResult:
    if game.status in {
        GameStatus.FINISHED,
        GameStatus.STOPPED,
    }:
        return FlowResult(False, "game_already_closed")

    phase_manager.stop(game)
    game_scheduler.cancel(game.game_id)

    try:
        await send_message(
            "🛑 <b>O'yin to'xtatildi.</b>"
        )
    finally:
        self.unregister_game(game.game_id)

    return FlowResult(True, "game_stopped")
game_flow = GameFlow()
