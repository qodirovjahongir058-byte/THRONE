
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from roles import Role, Team, get_role


# ============================================================
# THRONE — O'YIN HOLATI
# ============================================================


class GamePhase(StrEnum):
    LOBBY = "LOBBY"
    ROLE_REVEAL = "ROLE_REVEAL"
    NIGHT = "NIGHT"
    DAY = "DAY"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    LAST_WORDS = "LAST_WORDS"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


class PlayerStatus(StrEnum):
    ALIVE = "ALIVE"
    ELIMINATED = "ELIMINATED"
    LEFT = "LEFT"


class GameEndReason(StrEnum):
    VICTORY = "VICTORY"
    CANCELLED = "CANCELLED"
    ADMIN_STOPPED = "ADMIN_STOPPED"
    INSUFFICIENT_PLAYERS = "INSUFFICIENT_PLAYERS"
    ERROR = "ERROR"


def utc_now() -> datetime:
    """Joriy UTC vaqtini qaytaradi."""
    return datetime.now(timezone.utc)


# ============================================================
# O'YINCHI HOLATI
# ============================================================


@dataclass(slots=True)
class PlayerState:
    user_id: int
    full_name: str
    username: str | None = None

    role_id: str | None = None
    team: Team | None = None

    status: PlayerStatus = PlayerStatus.ALIVE
    joined_at: datetime = field(default_factory=utc_now)
    eliminated_at: datetime | None = None

    elimination_reason: str | None = None
    last_words: str | None = None

    # Tungi harakatlar va himoya holati
    protected: bool = False
    blocked: bool = False
    poisoned: bool = False
    weakened: bool = False
    concealed: bool = False

    # Maxsus qobiliyatlar uchun ma'lumot
    ability_uses: dict[str, int] = field(default_factory=dict)
    ability_data: dict[str, Any] = field(default_factory=dict)

    # Ovoz berish
    voted_for: int | None = None

    # Maxfiy sheriklar
    partner_ids: set[int] = field(default_factory=set)

    @property
    def is_alive(self) -> bool:
        return self.status == PlayerStatus.ALIVE

    @property
    def is_eliminated(self) -> bool:
        return self.status == PlayerStatus.ELIMINATED

    @property
    def role(self) -> Role | None:
        if self.role_id is None:
            return None
        return get_role(self.role_id)

    def assign_role(self, role_id: str) -> None:
        """O'yinchiga katalogdagi rolni biriktiradi."""
        role = get_role(role_id)
        if role is None:
            raise ValueError(f"Noma'lum rol: {role_id}")

        self.role_id = role.id
        self.team = role.team

    def eliminate(
        self,
        reason: str,
        eliminated_at: datetime | None = None,
    ) -> bool:
        """O'yinchini o'yindan chiqaradi. Takroriy chiqarishni oldini oladi."""
        if not self.is_alive:
            return False

        self.status = PlayerStatus.ELIMINATED
        self.eliminated_at = eliminated_at or utc_now()
        self.elimination_reason = reason
        self.voted_for = None
        return True

    def reset_night_effects(self) -> None:
        """Har yangi tun oldidan vaqtinchalik holatlarni tozalaydi."""
        self.protected = False
        self.blocked = False
        self.poisoned = False
        self.weakened = False
        self.concealed = False

    def reset_vote(self) -> None:
        self.voted_for = None


# ============================================================
# O'YIN HOLATI
# ============================================================


@dataclass(slots=True)
class GameState:
    chat_id: int
    creator_id: int

    game_id: str = field(
        default_factory=lambda: uuid4().hex
    )

    phase: GamePhase = GamePhase.LOBBY
    round_number: int = 0

    min_players: int = 7
    max_players: int = 50

    lobby_duration_seconds: int = 20 * 60
    night_duration_seconds: int = 90
    discussion_duration_seconds: int = 120
    voting_duration_seconds: int = 60
    last_words_duration_seconds: int = 30

    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    phase_started_at: datetime = field(default_factory=utc_now)
    phase_deadline: datetime | None = None

    players: dict[int, PlayerState] = field(default_factory=dict)

    # Tun davomida yig'iladigan harakatlar.
    # game_actions.py keyinchalik shu maydonlardan foydalanadi.
    pending_actions: list[dict[str, Any]] = field(
        default_factory=list
    )

    # Ovozlar: ovoz beruvchi ID -> nishon ID.
    votes: dict[int, int] = field(default_factory=dict)

    # Oxirgi so'z aytishi kerak bo'lgan o'yinchi.
    last_words_player_id: int | None = None

    # Durang bo'lsa, qayta ovoz berish hisoblagichi.
    revote_count: int = 0

    winner: Team | str | None = None
    end_reason: GameEndReason | None = None

    # Qo'shimcha o'yin ma'lumotlari.
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def alive_players(self) -> list[PlayerState]:
        return [
            player
            for player in self.players.values()
            if player.is_alive
        ]

    @property
    def alive_count(self) -> int:
        return len(self.alive_players)

    @property
    def eliminated_players(self) -> list[PlayerState]:
        return [
            player
            for player in self.players.values()
            if player.is_eliminated
        ]

    @property
    def is_active(self) -> bool:
        return self.phase not in {
            GamePhase.FINISHED,
            GamePhase.STOPPED,
        }

    @property
    def is_running(self) -> bool:
        return self.started_at is not None and self.is_active

    @property
    def can_start(self) -> bool:
        return (
            self.phase == GamePhase.LOBBY
            and self.min_players <= self.player_count <= self.max_players
        )

    def get_player(self, user_id: int) -> PlayerState | None:
        return self.players.get(user_id)

    def add_player(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None,
    ) -> PlayerState:
        """Lobbyga yangi o'yinchi qo'shadi."""
        if self.phase != GamePhase.LOBBY:
            raise ValueError("O'yin lobby bosqichida emas.")

        if user_id in self.players:
            raise ValueError("Bu o'yinchi allaqachon qo'shilgan.")

        if self.player_count >= self.max_players:
            raise ValueError("O'yinchilar soni maksimal chegaraga yetdi.")

        player = PlayerState(
            user_id=user_id,
            full_name=full_name,
            username=username,
        )
        self.players[user_id] = player
        return player

    def remove_lobby_player(self, user_id: int) -> bool:
        """Faqat lobbyda turgan o'yinchini ro'yxatdan chiqaradi."""
        if self.phase != GamePhase.LOBBY:
            return False

        return self.players.pop(user_id, None) is not None

    def start(self, now: datetime | None = None) -> None:
        """O'yinni boshlashga tayyorlaydi."""
        if self.phase != GamePhase.LOBBY:
            raise ValueError("O'yin allaqachon boshlangan yoki yopilgan.")

        if self.player_count < self.min_players:
            raise ValueError(
                f"O'yinni boshlash uchun kamida "
                f"{self.min_players} nafar o'yinchi kerak."
            )

        current_time = now or utc_now()
        self.started_at = current_time
        self.phase_started_at = current_time
        self.phase = GamePhase.ROLE_REVEAL
        self.phase_deadline = None

    def set_phase(
        self,
        phase: GamePhase,
        duration_seconds: int | None = None,
        now: datetime | None = None,
    ) -> None:
        """O'yin bosqichini va uning muddatini o'zgartiradi."""
        if not self.is_active:
            raise ValueError("Yopilgan o'yin bosqichini o'zgartirib bo'lmaydi.")

        current_time = now or utc_now()

        self.phase = phase
        self.phase_started_at = current_time
        self.phase_deadline = (
            current_time.timestamp() + duration_seconds
            if duration_seconds is not None
            else None
        )

        if phase == GamePhase.NIGHT:
            self.round_number += 1
            self.pending_actions.clear()
            for player in self.alive_players:
                player.reset_night_effects()

        if phase == GamePhase.VOTING:
            self.votes.clear()
            for player in self.alive_players:
                player.reset_vote()

    def finish(
        self,
        winner: Team | str | None,
        reason: GameEndReason = GameEndReason.VICTORY,
        now: datetime | None = None,
    ) -> None:
        """O'yinni yakunlaydi."""
        if not self.is_active:
            return

        self.phase = GamePhase.FINISHED
        self.winner = winner
        self.end_reason = reason
        self.finished_at = now or utc_now()
        self.phase_deadline = None
        self.pending_actions.clear()
        self.votes.clear()

    def stop(
        self,
        reason: GameEndReason = GameEndReason.ADMIN_STOPPED,
        now: datetime | None = None,
    ) -> None:
        """O'yinni majburiy to'xtatadi."""
        if not self.is_active:
            return

        self.phase = GamePhase.STOPPED
        self.end_reason = reason
        self.finished_at = now or utc_now()
        self.phase_deadline = None
        self.pending_actions.clear()
        self.votes.clear()
    
