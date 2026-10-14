from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =========================================================
# O'YIN SOZLAMALARI
# =========================================================

MIN_PLAYERS = 7
MAX_PLAYERS = 35

LAST_WORDS_DURATION = 30
DEFAULT_DISCUSSION_DURATION = 120
DEFAULT_VOTING_DURATION = 60
DEFAULT_NIGHT_DURATION = 90


# =========================================================
# O'YIN BOSQICHLARI
# =========================================================

class GamePhase(str, Enum):
    LOBBY = "LOBBY"
    ROLE_REVEAL = "ROLE_REVEAL"
    NIGHT = "NIGHT"
    DAY = "DAY"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    REVOTE = "REVOTE"
    LAST_WORDS = "LAST_WORDS"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


class GameStatus(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


# =========================================================
# O'YINCHI HOLATI
# =========================================================

@dataclass
class PlayerState:
    user_id: int
    username: str | None = None
    display_name: str = ""

    role_key: str | None = None
    faction: str | None = None

    alive: bool = True
    connected: bool = True
    has_acted: bool = False

    protected: bool = False
    blocked: bool = False
    poisoned: bool = False
    weakened: bool = False

    votes_received: int = 0
    voted_for: int | None = None

    joined_at: str | None = None
    eliminated_at: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def eliminate(self) -> None:
        """O'yinchini o'lgan holatga o'tkazadi."""
        self.alive = False
        self.has_acted = False
        self.voted_for = None

    def reset_night_state(self) -> None:
        """Tungi vaqtinchalik ta'sirlarni tozalaydi."""
        self.has_acted = False
        self.protected = False
        self.blocked = False
        self.poisoned = False
        self.weakened = False

    def reset_vote_state(self) -> None:
        """Ovoz berish ma'lumotlarini tozalaydi."""
        self.votes_received = 0
        self.voted_for = None


# =========================================================
# O'YIN HOLATI
# =========================================================

@dataclass
class GameState:
    game_id: int
    chat_id: int
    creator_id: int

    status: GameStatus = GameStatus.WAITING
    phase: GamePhase = GamePhase.LOBBY

    round_number: int = 0
    night_number: int = 0

    players: dict[int, PlayerState] = field(default_factory=dict)

    current_target: int | None = None
    last_words_player_id: int | None = None

    created_at: str | None = None
    updated_at: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # O'YINCHI QO'SHISH VA OLIB TASHLASH
    # -----------------------------------------------------

    def add_player(self, player: PlayerState) -> None:
        """Lobbiga o'yinchi qo'shadi."""
        if self.phase != GamePhase.LOBBY:
            raise ValueError("O'yin boshlanganidan keyin qo'shilib bo'lmaydi.")

        if player.user_id in self.players:
            raise ValueError("Bu o'yinchi allaqachon qo'shilgan.")

        if len(self.players) >= MAX_PLAYERS:
            raise ValueError(
                f"O'yinchilar soni {MAX_PLAYERS} tadan oshmasligi kerak."
            )

        self.players[player.user_id] = player

    def remove_player(self, user_id: int) -> bool:
        """Lobbidan o'yinchini olib tashlaydi."""
        if self.phase != GamePhase.LOBBY:
            return False

        return self.players.pop(user_id, None) is not None

    def get_player(self, user_id: int) -> PlayerState | None:
        """O'yinchini Telegram ID orqali topadi."""
        return self.players.get(user_id)

    # -----------------------------------------------------
    # O'YINCHILAR RO'YXATI
    # -----------------------------------------------------

    def alive_players(self) -> list[PlayerState]:
        return [
            player
            for player in self.players.values()
            if player.alive
        ]

    def dead_players(self) -> list[PlayerState]:
        return [
            player
            for player in self.players.values()
            if not player.alive
        ]

    def alive_count(self) -> int:
        return sum(
            1 for player in self.players.values()
            if player.alive
        )

    def player_count(self) -> int:
        return len(self.players)

    def can_start(self) -> bool:
        """O'yinni boshlash uchun o'yinchilar sonini tekshiradi."""
        return (
            self.phase == GamePhase.LOBBY
            and MIN_PLAYERS <= len(self.players) <= MAX_PLAYERS
        )

    # -----------------------------------------------------
    # TUNGI BOSQICH VA OVOZ BERISH
    # -----------------------------------------------------

    def reset_night_actions(self) -> None:
        for player in self.players.values():
            player.reset_night_state()

        self.current_target = None

    def reset_votes(self) -> None:
        for player in self.players.values():
            player.reset_vote_state()

    # -----------------------------------------------------
    # BOSQICHNI BOSHQARISH
    # -----------------------------------------------------

    def set_phase(self, phase: GamePhase) -> None:
        self.phase = phase

        if phase == GamePhase.FINISHED:
            self.status = GameStatus.FINISHED
        elif phase == GamePhase.STOPPED:
            self.status = GameStatus.STOPPED
        elif phase != GamePhase.LOBBY:
            self.status = GameStatus.ACTIVE

    def start_night(self) -> None:
        if self.phase not in {
            GamePhase.ROLE_REVEAL,
            GamePhase.DAY,
            GamePhase.DISCUSSION,
            GamePhase.VOTING,
            GamePhase.REVOTE,
            GamePhase.LAST_WORDS,
        }:
            raise ValueError("Hozir tungi bosqichni boshlash mumkin emas.")

        self.night_number += 1
        self.reset_night_actions()
        self.set_phase(GamePhase.NIGHT)

    def start_day(self) -> None:
        if self.phase != GamePhase.NIGHT:
            raise ValueError("Kunduzgi bosqich uchun avval tun tugashi kerak.")

        self.round_number += 1
        self.set_phase(GamePhase.DAY)

    def finish_game(self) -> None:
        self.set_phase(GamePhase.FINISHED)

    def stop_game(self) -> None:
        self.set_phase(GamePhase.STOPPED)
