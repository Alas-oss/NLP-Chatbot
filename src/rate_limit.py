from __future__ import annotations

import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float, *, clock=time.monotonic):
        if max_events < 1:
            raise ValueError("max_events must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._clock = clock
        self._events: deque[float] = deque()

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._events and self._events[0] <= cutoff:
            self._events.popleft()

    def allow(self) -> bool:
        now = self._clock()
        self._evict_old(now)
        if len(self._events) >= self._max_events:
            return False
        self._events.append(now)
        return True

    def retry_after(self) -> float:
        now = self._clock()
        self._evict_old(now)
        if len(self._events) < self._max_events:
            return 0.0
        return max(0.0, self._events[0] + self._window_seconds - now)