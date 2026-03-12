"""Simulated telemetry — no real drone needed for demo/testing."""
from __future__ import annotations
import math
import threading
import time
from typing import Callable
from app.mavlink_handler import TelemetryFrame


class TelemetrySimulator:
    """Generates realistic synthetic telemetry at ~4 Hz."""

    def __init__(self, on_update: Callable[[TelemetryFrame], None]):
        self.on_update = on_update
        self._running  = False
        self._thread: threading.Thread | None = None
        self._t        = 0.0
        self.connected = True
        self.frame     = TelemetryFrame(
            lat=47.6062, lon=-122.3321,
            alt=0.0, rel_alt=0.0,
            heading=0.0, groundspeed=0.0,
            battery_pct=100, battery_v=12.6,
            armed=False, mode="STABILIZE",
            satellites=12, fix_type=3,
        )
        self._modes    = ["STABILIZE", "LOITER", "AUTO", "RTL", "LAND"]
        self._mode_idx = 0

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def arm(self):
        self.frame.armed = True

    def disarm(self):
        self.frame.armed = False

    def set_mode(self, mode: str):
        if mode in self._modes:
            self._mode_idx = self._modes.index(mode)

    def _loop(self):
        while self._running:
            self._t += 0.25
            f = self.frame
            if f.armed:
                if self._modes[self._mode_idx] == "LAND":
                    f.rel_alt = max(0.0, f.rel_alt - 0.3)
                else:
                    f.rel_alt += (30.0 - f.rel_alt) * 0.03
            else:
                f.rel_alt = max(0.0, f.rel_alt - 0.5)
            f.alt         = f.rel_alt + 50.0
            f.groundspeed = abs(math.sin(self._t * 0.2)) * 8.0 if f.armed else 0.0
            f.heading     = (self._t * 5.0) % 360
            f.roll        = math.degrees(math.sin(self._t * 0.5)) * 4
            f.pitch       = math.degrees(math.cos(self._t * 0.3)) * 3
            f.battery_pct = max(0, int(100 - self._t * 0.04))
            f.battery_v   = max(9.0, 12.6 - self._t * 0.003)
            f.satellites  = 12
            f.fix_type    = 3
            f.mode        = self._modes[self._mode_idx]
            f.timestamp   = time.time()
            f.lat        += math.sin(self._t * 0.07) * 0.000005
            f.lon        += math.cos(self._t * 0.07) * 0.000005
            self.on_update(f)
            time.sleep(0.25)
