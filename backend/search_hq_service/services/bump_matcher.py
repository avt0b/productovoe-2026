"""Сопоставление встрясок краеведа и участников экскурсии.

Встряска живёт секунды, поэтому хранится в памяти процесса — ни база, ни Redis
не нужны. Цена: сервис должен работать одним процессом uvicorn (так он и
запускается в Dockerfile). Встряски из разных процессов друг друга не увидят;
для нескольких экземпляров сервиса это хранилище надо вынести в Redis.

Пара — это краевед и участник одной экскурсии, чьи встряски разошлись по
времени не больше чем на `window_seconds`. Участники между собой не совпадают:
отмечаться нужно у краеведа.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from core.config import settings


@dataclass(frozen=True)
class Shake:
    excursion_id: str
    user_id: str
    is_guide: bool
    # Когда телефон тряхнули — unix-время по часам сервера, в секундах.
    shaken_at: float


class BumpMatcher:
    def __init__(
        self,
        *,
        window_seconds: float,
        wait_seconds: float,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.window_seconds = window_seconds
        self.wait_seconds = wait_seconds
        self._clock = clock
        self._condition = threading.Condition()
        self._shakes: dict[str, list[Shake]] = {}

    def now(self) -> float:
        return self._clock()

    def shake(self, shake: Shake) -> list[Shake]:
        """Записать встряску и дождаться встряски другой стороны.

        Участник ждёт краеведа, краевед — участников. Возвращает совпавшие
        встряски, как только нашлась хотя бы одна, или пустой список, если за
        `wait_seconds` пары не появилось. Обе стороны получают ответ почти
        одновременно — поэтому анимации на телефонах стартуют вместе и без
        WebSocket.
        """
        deadline = time.monotonic() + self.wait_seconds
        with self._condition:
            self._prune(shake.excursion_id)
            self._shakes.setdefault(shake.excursion_id, []).append(shake)
            # Разбудить тех, кто уже ждёт пару: возможно, это она.
            self._condition.notify_all()
            while True:
                matches = self._matches_for(shake)
                if matches:
                    return matches
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return []
                self._condition.wait(remaining)

    def forget(self, excursion_id: str) -> None:
        """Сбор закрыт — его встряски больше не нужны."""
        with self._condition:
            self._shakes.pop(excursion_id, None)

    def reset(self) -> None:
        with self._condition:
            self._shakes.clear()

    def _matches_for(self, shake: Shake) -> list[Shake]:
        return [
            other
            for other in self._shakes.get(shake.excursion_id, [])
            if other.is_guide != shake.is_guide
            and abs(other.shaken_at - shake.shaken_at) <= self.window_seconds
        ]

    def _prune(self, excursion_id: str) -> None:
        # Встряска старше окна и ожидания уже ни с кем не совпадёт.
        horizon = self.now() - (self.window_seconds + self.wait_seconds + 1)
        fresh = [s for s in self._shakes.get(excursion_id, []) if s.shaken_at >= horizon]
        if fresh:
            self._shakes[excursion_id] = fresh
        else:
            self._shakes.pop(excursion_id, None)


bump_matcher = BumpMatcher(
    window_seconds=settings.bump_window_seconds,
    wait_seconds=settings.bump_wait_seconds,
)
