from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable


PhaseCallback = Callable[[], Awaitable[None]]


@dataclass(slots=True)
class ScheduledPhase:
    """Information about one scheduled game phase."""

    game_id: int
    phase_name: str
    task: asyncio.Task[None]


class GameScheduler:
    """Manage asynchronous timers for THRONE game phases."""

    def __init__(self) -> None:
        self._tasks: dict[int, ScheduledPhase] = {}

    def schedule(
        self,
        game_id: int,
        phase_name: str,
        duration: int,
        callback: PhaseCallback,
    ) -> None:
        """Schedule a callback after the specified duration."""

        if duration <= 0:
            raise ValueError(
                "Phase duration must be greater than zero."
            )

        self.cancel(game_id)

        task = asyncio.create_task(
            self._run_timer(
                game_id=game_id,
                phase_name=phase_name,
                duration=duration,
                callback=callback,
            )
        )

        self._tasks[game_id] = ScheduledPhase(
            game_id=game_id,
            phase_name=phase_name,
            task=task,
        )

    async def _run_timer(
        self,
        game_id: int,
        phase_name: str,
        duration: int,
        callback: PhaseCallback,
    ) -> None:
        try:
            await asyncio.sleep(duration)
            await callback()

        except asyncio.CancelledError:
            return

        finally:
            scheduled = self._tasks.get(game_id)

            if (
                scheduled is not None
                and scheduled.phase_name == phase_name
            ):
                self._tasks.pop(game_id, None)

    def cancel(self, game_id: int) -> bool:
        """Cancel the currently scheduled timer for a game."""

        scheduled = self._tasks.pop(game_id, None)

        if scheduled is None:
            return False

        scheduled.task.cancel()
        return True

    def is_scheduled(self, game_id: int) -> bool:
        """Return whether a timer is currently scheduled."""

        scheduled = self._tasks.get(game_id)

        if scheduled is None:
            return False

        return not scheduled.task.done()

    def get_phase_name(
        self,
        game_id: int,
    ) -> str | None:
        """Return the currently scheduled phase name."""

        scheduled = self._tasks.get(game_id)

        if scheduled is None:
            return None

        if scheduled.task.done():
            return None

        return scheduled.phase_name

    def cancel_all(self) -> None:
        """Cancel all active game timers."""

        game_ids = list(self._tasks.keys())

        for game_id in game_ids:
            self.cancel(game_id)


game_scheduler = GameScheduler()
