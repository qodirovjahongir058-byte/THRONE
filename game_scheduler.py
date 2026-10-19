
import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

TimerCallback = Callable[[], Any | Awaitable[Any]]


@dataclass
class ScheduledPhase:
    phase_name: str
    task: asyncio.Task[None]


class GameScheduler:
    """Har bir o'yin uchun bittadan faol bosqich taymerini boshqaradi."""

    def __init__(self) -> None:
        self._timers: dict[str, ScheduledPhase] = {}

    @staticmethod
    def _key(game_id: str | int) -> str:
        return str(game_id)

    async def _wait_and_run(
        self,
        key: str,
        phase_name: str,
        duration: float,
        callback: TimerCallback,
    ) -> None:
        try:
            await asyncio.sleep(max(0.0, duration))

            # Taymer o'rniga boshqa taymer qo'yilgan bo'lsa,
            # eski taymer callback'ni bajarmaydi.
            current = self._timers.get(key)
            if current is None or current.task is not asyncio.current_task():
                return

            result = callback()
            if inspect.isawaitable(result):
                await result

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "O'yin taymeri callback xatosi: game_id=%s, phase=%s",
                key,
                phase_name,
            )
        finally:
            current = self._timers.get(key)
            if current is not None and current.task is asyncio.current_task():
                self._timers.pop(key, None)

    def schedule(
        self,
        game_id: str | int,
        phase_name: str,
        duration: float,
        callback: TimerCallback,
    ) -> None:
        """O'yin uchun taymer yaratadi; eskisi bo'lsa almashtiradi."""
        key = self._key(game_id)
        self.cancel(key)

        task = asyncio.create_task(
            self._wait_and_run(key, phase_name, duration, callback),
            name=f"game-timer-{key}-{phase_name}",
        )
        self._timers[key] = ScheduledPhase(
            phase_name=phase_name,
            task=task,
        )

    def cancel(self, game_id: str | int) -> bool:
        """O'yin taymerini bekor qiladi. Bekor qilingan bo'lsa True."""
        key = self._key(game_id)
        scheduled = self._timers.pop(key, None)

        if scheduled is None:
            return False

        current_task = asyncio.current_task()
        if scheduled.task is not current_task and not scheduled.task.done():
            scheduled.task.cancel()

        return True

    def is_scheduled(self, game_id: str | int) -> bool:
        scheduled = self._timers.get(self._key(game_id))
        return scheduled is not None and not scheduled.task.done()

    def get_phase_name(self, game_id: str | int) -> str | None:
        scheduled = self._timers.get(self._key(game_id))
        if scheduled is None or scheduled.task.done():
            return None
        return scheduled.phase_name

    async def cancel_all(self) -> None:
        """Barcha faol taymerlarni bekor qilib, tugashini kutadi."""
        tasks = [
            scheduled.task
            for scheduled in self._timers.values()
            if not scheduled.task.done()
        ]
        self._timers.clear()

        current_task = asyncio.current_task()
        to_cancel = [task for task in tasks if task is not current_task]

        for task in to_cancel:
            task.cancel()

        if to_cancel:
            await asyncio.gather(*to_cancel, return_exceptions=True)


game_scheduler = GameScheduler()
