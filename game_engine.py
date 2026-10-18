from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import secrets
import time


class GamePhase(str, Enum):
    LOBBY = "lobby"
    ROLE_REVEAL = "role_reveal"
    NIGHT = "night"
    DAY = "day"
    DISCUSSION = "discussion"
    VOTING = "voting"
    LAST_WORDS = "last_words"
    FINISHED = "finished"
    STOPPED = "stopped"


@dataclass
class Player:
    user_id: int
    name: str
    username: Optional[str] = None
    role_id: Optional[str] = None
    alive: bool = True
    joined_at: float = field(default_factory=time.time)
    last_words: Optional[str] = None
    vote_target: Optional[int] = None
    night_action: Optional[dict] = None


@dataclass
class Game:
    chat_id: int
    creator_id: int
    game_id: str = field(default_factory=lambda: secrets.token_hex(6))
    phase: GamePhase = GamePhase.LOBBY
    players: dict[int, Player] = field(default_factory=dict)
    round_number: int = 0
    created_at: float = field(default_factory=time.time)
    phase_started_at: float = field(default_factory=time.time)
    winner: Optional[str] = None
    night_actions: list[dict] = field(default_factory=list)
    votes: dict[int, int] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    MIN_PLAYERS = 7
    MAX_PLAYERS = 36
    LAST_WORDS_SECONDS = 30

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def alive_players(self) -> list[Player]:
        return [p for p in self.players.values() if p.alive]

    @property
    def dead_players(self) -> list[Player]:
        return [p for p in self.players.values() if not p.alive]

    def add_player(
        self,
        user_id: int,
        name: str,
        username: Optional[str] = None,
    ) -> tuple[bool, str]:
        if self.phase != GamePhase.LOBBY:
            return False, "O'yinga qo'shilish vaqti tugagan."

        if user_id in self.players:
            return False, "Siz allaqachon o'yindasiz."

        if self.player_count >= self.MAX_PLAYERS:
            return False, "O'yinchilar soni maksimal chegaraga yetdi."

        self.players[user_id] = Player(
            user_id=user_id,
            name=name,
            username=username,
        )
        self.history.append(f"{name} o'yinga qo'shildi.")
        return True, "Siz o'yinga muvaffaqiyatli qo'shildingiz."

    def remove_player(self, user_id: int) -> tuple[bool, str]:
        if self.phase != GamePhase.LOBBY:
            return False, "Boshlangan o'yindan bu usulda chiqib bo'lmaydi."

        player = self.players.pop(user_id, None)
        if player is None:
            return False, "O'yinchi topilmadi."

        self.history.append(f"{player.name} o'yindan chiqdi.")
        return True, "O'yindan chiqdingiz."

    def can_start(self, requester_is_admin: bool) -> tuple[bool, str]:
        if not requester_is_admin:
            return False, "O'yinni faqat guruh administratori boshlashi mumkin."

        if self.phase != GamePhase.LOBBY:
            return False, "O'yin allaqachon boshlangan yoki yakunlangan."

        if self.player_count < self.MIN_PLAYERS:
            return False, (
                f"O'yinni boshlash uchun kamida "
                f"{self.MIN_PLAYERS} nafar o'yinchi kerak."
            )

        return True, "O'yinni boshlash mumkin."

    def start(self, requester_is_admin: bool) -> tuple[bool, str]:
        allowed, message = self.can_start(requester_is_admin)

        if not allowed:
            return False, message

        self.phase = GamePhase.ROLE_REVEAL
        self.phase_started_at = time.time()
        self.round_number = 0
        self.history.append("O'yin boshlandi.")
        return True, "O'yin boshlandi. Rollarni taqsimlash mumkin."

    def assign_role(self, user_id: int, role_id: str) -> bool:
        if self.phase != GamePhase.ROLE_REVEAL:
            return False

        player = self.players.get(user_id)
        if player is None:
            return False

        player.role_id = role_id
        return True

    def all_roles_assigned(self) -> bool:
        return bool(self.players) and all(
            player.role_id is not None
            for player in self.players.values()
        )

    def begin_night(self) -> tuple[bool, str]:
        if self.phase not in (
            GamePhase.ROLE_REVEAL,
            GamePhase.DAY,
            GamePhase.DISCUSSION,
            GamePhase.VOTING,
        ):
            return False, "Hozir tunni boshlash mumkin emas."

        if not self.all_roles_assigned():
            return False, "Avval barcha o'yinchilarga rol berilishi kerak."

        self.phase = GamePhase.NIGHT
        self.round_number += 1
        self.phase_started_at = time.time()
        self.night_actions.clear()
        self.votes.clear()

        for player in self.players.values():
            player.night_action = None
            player.vote_target = None

        self.history.append(f"{self.round_number}-tun boshlandi.")
        return True, f"{self.round_number}-tun boshlandi."

    def begin_day(self) -> tuple[bool, str]:
        if self.phase != GamePhase.NIGHT:
            return False, "Hozir tun bosqichi emas."

        self.phase = GamePhase.DAY
        self.phase_started_at = time.time()
        self.history.append(f"{self.round_number}-kun boshlandi.")
        return True, "Tong otdi. Kun bosqichi boshlandi."

    def begin_discussion(self) -> tuple[bool, str]:
        if self.phase != GamePhase.DAY:
            return False, "Avval tong bosqichi yakunlanishi kerak."

        self.phase = GamePhase.DISCUSSION
        self.phase_started_at = time.time()
        self.history.append("Muhokama boshlandi.")
        return True, "Muhokama boshlandi."

    def begin_voting(self) -> tuple[bool, str]:
        if self.phase != GamePhase.DISCUSSION:
            return False, "Avval muhokama bosqichi o'tishi kerak."

        self.phase = GamePhase.VOTING
        self.phase_started_at = time.time()
        self.votes.clear()

        for player in self.players.values():
            player.vote_target = None

        self.history.append("Ovoz berish boshlandi.")
        return True, "Ovoz berish boshlandi."

    def cast_vote(
        self,
        voter_id: int,
        target_id: int,
    ) -> tuple[bool, str]:
        if self.phase != GamePhase.VOTING:
            return False, "Hozir ovoz berish bosqichi emas."

        voter = self.players.get(voter_id)
        target = self.players.get(target_id)

        if voter is None or not voter.alive:
            return False, "Siz ovoz bera olmaysiz."

        if target is None or not target.alive:
            return False, "Tanlangan o'yinchi topilmadi yoki tirik emas."

        if voter_id == target_id:
            return False, "O'zingizga ovoz bera olmaysiz."

        self.votes[voter_id] = target_id
        voter.vote_target = target_id
        return True, "Ovozingiz qabul qilindi."

    def get_vote_results(self) -> dict[int, int]:
        results: dict[int, int] = {}

        for voter_id, target_id in self.votes.items():
            voter = self.players.get(voter_id)
            target = self.players.get(target_id)

            if (
                voter is not None
                and voter.alive
                and target is not None
                and target.alive
            ):
                results[target_id] = results.get(target_id, 0) + 1

        return results

    def get_voting_winner(self) -> tuple[Optional[int], bool]:
        results = self.get_vote_results()

        if not results:
            return None, False

        highest_votes = max(results.values())
        candidates = [
            user_id
            for user_id, votes in results.items()
            if votes == highest_votes
        ]

        if len(candidates) != 1:
            return None, True

        return candidates[0], False

    def eliminate_player(
        self,
        user_id: int,
        reason: str = "O'yindan chiqarildi",
    ) -> tuple[bool, str]:
        player = self.players.get(user_id)

        if player is None:
            return False, "O'yinchi topilmadi."

        if not player.alive:
            return False, "Bu o'yinchi allaqachon o'yindan chiqqan."

        player.alive = False
        self.history.append(f"{player.name}: {reason}.")
        return True, f"{player.name} o'yindan chiqarildi."

    def start_last_words(self, user_id: int) -> tuple[bool, str]:
        if self.phase != GamePhase.VOTING:
            return False, "Hozir oxirgi so'z bosqichi emas."

        player = self.players.get(user_id)
        if player is None or player.alive:
            return False, "Oxirgi so'z faqat chiqarilgan o'yinchiga beriladi."

        self.phase = GamePhase.LAST_WORDS
        self.phase_started_at = time.time()
        self.history.append(
            f"{player.name} uchun oxirgi so'z bosqichi boshlandi."
        )
        return True, (
            f"{player.name} uchun oxirgi so'z vaqti: "
            f"{self.LAST_WORDS_SECONDS} soniya."
        )

    def save_last_words(
        self,
        user_id: int,
        message: str,
    ) -> tuple[bool, str]:
        if self.phase != GamePhase.LAST_WORDS:
            return False, "Hozir oxirgi so'z bosqichi emas."

        player = self.players.get(user_id)
        if player is None or player.alive:
            return False, "Bu bosqichda faqat chiqarilgan o'yinchi yozishi mumkin."

        if time.time() - self.phase_started_at > self.LAST_WORDS_SECONDS:
            return False, "Oxirgi so'z uchun ajratilgan vaqt tugadi."

        player.last_words = message.strip()[:1000]
        self.history.append(f"{player.name} oxirgi so'zini aytdi.")
        return True, "Oxirgi so'zingiz saqlandi."

    def last_words_time_left(self) -> int:
        elapsed = time.time() - self.phase_started_at
        return max(0, self.LAST_WORDS_SECONDS - int(elapsed))

    def finish(self, winner: str) -> tuple[bool, str]:
        if self.phase in (GamePhase.FINISHED, GamePhase.STOPPED):
            return False, "O'yin allaqachon yakunlangan."

        self.winner = winner
        self.phase = GamePhase.FINISHED
        self.phase_started_at = time.time()
        self.history.append(f"O'yin yakunlandi. G'olib: {winner}.")
        return True, f"O'yin yakunlandi. G'olib: {winner}."

    def stop(self, requester_is_admin: bool) -> tuple[bool, str]:
        if not requester_is_admin:
            return False, "O'yinni faqat guruh administratori to'xtata oladi."

        if self.phase in (GamePhase.FINISHED, GamePhase.STOPPED):
            return False, "O'yin allaqachon yakunlangan."

        self.phase = GamePhase.STOPPED
        self.phase_started_at = time.time()
        self.history.append("O'yin administrator tomonidan to'xtatildi.")
        return True, "O'yin to'xtatildi."
