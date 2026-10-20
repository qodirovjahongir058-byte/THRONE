
from __future__ import annotations

import asyncio
import logging
import time

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


logger = logging.getLogger(__name__)


class TimerPhase(StrEnum):
    LOBBY = "LOBBY"
    NIGHT = "NIGHT"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    LAST_WORDS = "LAST_WORDS"


DEFAULT_DURATIONS: dict[TimerPhase, int] = {
    TimerPhase.LOBBY: 20 * 60,
    TimerPhase.NIGHT: 90,
    TimerPhase.DISCUSSION: 120,
    TimerPhase.VOTING: 60,
    TimerPhase.LAST_WORDS: 30,
}


class TimerError(Exception):
    """Taymer bilan bog'liq xato."""


@dataclass(frozen=True, slots=True)
class TimerInfo:
    key: str
    phase: TimerPhase
    started_at: float
    deadline: float
    duration_seconds: int

    @property
    def remaining_seconds(self) -> int:
        return max(0, int(self.deadline - time.monotonic()))


TimerCallback = Callable[[TimerInfo], Awaitable[None]]


class GameTimer:
    """Bir nechta o'yin uchun xavfsiz asinxron taymerlar."""

    def __init__(
        self,
        durations: dict[TimerPhase, int] | None = None,
    ) -> None:
        self.durations = dict(DEFAULT_DURATIONS)

        if durations:
            self.durations.update(durations)

        for phase, duration in self.durations.items():
            if duration <= 0:
                raise ValueError(
                    f"{phase.value} davomiyligi musbat bo'lishi kerak."
                )

        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._timers: dict[str, TimerInfo] = {}
        self._lock = asyncio.Lock()
        self._closed = False

    async def start(
        self,
        key: str,
        phase: TimerPhase,
        callback: TimerCallback,
        duration_seconds: int | None = None,
    ) -> TimerInfo:
        """Taymerni boshlaydi yoki shu kalitdagi taymerni almashtiradi."""

        if self._closed:
            raise TimerError("Taymer menejeri yopilgan.")

        if not key.strip():
            raise TimerError("Taymer kaliti bo'sh bo'lmasligi kerak.")

        duration = (
            duration_seconds
            if duration_seconds is not None
            else self.durations[phase]
        )

        if duration <= 0:
            raise TimerError("Taymer davomiyligi musbat bo'lishi kerak.")

        async with self._lock:
            old_task = self._tasks.pop(key, None)

            if old_task is not None:
                old_task.cancel()

            now = time.monotonic()
            info = TimerInfo(
                key=key,
                phase=phase,
                started_at=now,
                deadline=now + duration,
                duration_seconds=duration,
            )

            self._timers[key] = info
            self._tasks[key] = asyncio.create_task(
                self._run(info, callback),
                name=f"throne-timer-{key}",
            )

            return info

    async def _run(
        self,
        info: TimerInfo,
        callback: TimerCallback,
    ) -> None:
        current_task = asyncio.current_task()

        try:
            await asyncio.sleep(info.duration_seconds)

            # Taymer almashtirilgan bo'lsa, eskisi callbackni bajarmaydi.
            async with self._lock:
                if self._timers.get(info.key) != info:
                    return

            await callback(info)

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Taymer callbackida xato: key=%s phase=%s",
                info.key,
                info.phase.value,
            )

        finally:
            async with self._lock:
                if self._timers.get(info.key) == info:
                    self._timers.pop(info.key, None)

                if self._tasks.get(info.key) is current_task:
                    self._tasks.pop(info.key, None)

    async def cancel(self, key: str) -> bool:
        """Taymerni bekor qiladi."""

        async with self._lock:
            task = self._tasks.pop(key, None)
            self._timers.pop(key, None)

            if task is None:
                return False

            task.cancel()
            return True

    async def cancel_game(self, game_id: str) -> int:
        """O'yinga tegishli barcha taymerlarni bekor qiladi."""

        prefix = f"{game_id}:"

        async with self._lock:
            keys = [
                key
                for key in self._tasks
                if key.startswith(prefix)
            ]

            tasks = [self._tasks.pop(key) for key in keys]

            for key in keys:
                self._timers.pop(key, None)

            for task in tasks:
                task.cancel()

            return len(tasks)

    async def get_timer(self, key: str) -> TimerInfo | None:
        """Taymer holatini qaytaradi."""

        async with self._lock:
            return self._timers.get(key)

    async def remaining(self, key: str) -> int | None:
        """Qolgan soniyalarni qaytaradi."""

        info = await self.get_timer(key)

        if info is None:
            return None

        return info.remaining_seconds

    async def is_running(self, key: str) -> bool:
        async with self._lock:
            task = self._tasks.get(key)
            return task is not None and not task.done()

    async def close(self) -> None:
        """Bot o'chayotganda barcha taymerlarni to'xtatadi."""

        async with self._lock:
            self._closed = True

            tasks = list(self._tasks.values())
            self._tasks.clear()
            self._timers.clear()

            for task in tasks:
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def timer_key(game_id: str, phase: TimerPhase) -> str:
    """O'yin va bosqich uchun yagona taymer kaliti."""

    return f"{game_id}:{phase.value.lower()}"


def create_game_timer() -> GameTimer:
    return GameTimer()
  
