"""Telemetry history buffer — keeps a rolling window of TelemetryFrames."""
from __future__ import annotations
import time
from collections import deque
from typing import Deque, List
from app.mavlink_handler import TelemetryFrame

_DEFAULT_MAX = 600  # 10 minutes @ 1 Hz, or 2.5 min @ 4 Hz


class TelemetryHistory:
    """Thread-safe rolling window of TelemetryFrame snapshots."""

    def __init__(self, maxlen: int = _DEFAULT_MAX):
        self._buf: Deque[TelemetryFrame] = deque(maxlen=maxlen)
        self._start: float = time.time()

    def push(self, frame: TelemetryFrame) -> None:
        self._buf.append(frame)

    def latest(self) -> TelemetryFrame | None:
        return self._buf[-1] if self._buf else None

    def as_list(self) -> List[TelemetryFrame]:
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()
        self._start = time.time()

    @property
    def elapsed(self) -> float:
        """Seconds since first push or last clear."""
        return time.time() - self._start

    def get_series(self, field: str) -> tuple[list[float], list[float]]:
        """Return (timestamps_relative, values) lists for a named TelemetryFrame field."""
        if not self._buf:
            return [], []
        t0 = self._buf[0].timestamp
        ts, vs = [], []
        for f in self._buf:
            ts.append(f.timestamp - t0)
            vs.append(getattr(f, field, 0.0))
        return ts, vs
