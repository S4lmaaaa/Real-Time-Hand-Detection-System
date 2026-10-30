"""Small helpers."""

from __future__ import annotations

import time


class FPSCounter:
    """Exponentially smoothed frames-per-second counter."""

    def __init__(self, alpha: float = 0.9) -> None:
        self.alpha = alpha
        self.fps = 0.0
        self._last: float | None = None

    def tick(self) -> float:
        now = time.perf_counter()
        if self._last is not None:
            instant = 1.0 / max(now - self._last, 1e-6)
            self.fps = instant if self.fps == 0 else self.alpha * self.fps + (1 - self.alpha) * instant
        self._last = now
        return self.fps
