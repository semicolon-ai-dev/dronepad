"""CSV flight log writer — auto-saves telemetry when armed, reads back sessions."""
from __future__ import annotations
import csv
import os
import time
from pathlib import Path
from typing import List, Optional
from app.mavlink_handler import TelemetryFrame

LOG_DIR = Path("logs")
_FIELDS = [
    "timestamp", "lat", "lon", "alt", "rel_alt",
    "heading", "groundspeed", "roll", "pitch",
    "battery_pct", "battery_v", "armed", "mode",
    "satellites", "fix_type",
]


class FlightLogger:
    """Opens a new CSV file per arm event and writes one row per TelemetryFrame."""

    def __init__(self, log_dir: Path = LOG_DIR):
        self._dir = log_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._writer: Optional[csv.DictWriter] = None
        self._fp = None
        self._current_path: Optional[Path] = None
        self._logging = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> Path:
        """Open a new log file. Returns the path."""
        if self._logging:
            self.stop()
        ts_str = time.strftime("%Y%m%d_%H%M%S")
        self._current_path = self._dir / f"flight_{ts_str}.csv"
        self._fp = open(self._current_path, "w", newline="")
        self._writer = csv.DictWriter(self._fp, fieldnames=_FIELDS)
        self._writer.writeheader()
        self._logging = True
        return self._current_path

    def write(self, frame: TelemetryFrame) -> None:
        """Write one row. No-op if not started."""
        if not self._logging or self._writer is None:
            return
        self._writer.writerow({
            "timestamp":   frame.timestamp,
            "lat":         frame.lat,
            "lon":         frame.lon,
            "alt":         frame.alt,
            "rel_alt":     frame.rel_alt,
            "heading":     frame.heading,
            "groundspeed": frame.groundspeed,
            "roll":        frame.roll,
            "pitch":       frame.pitch,
            "battery_pct": frame.battery_pct,
            "battery_v":   frame.battery_v,
            "armed":       int(frame.armed),
            "mode":        frame.mode,
            "satellites":  frame.satellites,
            "fix_type":    frame.fix_type,
        })

    def stop(self) -> Optional[Path]:
        """Flush and close current log file. Returns its path."""
        self._logging = False
        if self._fp:
            self._fp.flush()
            self._fp.close()
            self._fp = None
        self._writer = None
        return self._current_path

    @property
    def is_logging(self) -> bool:
        return self._logging

    @property
    def current_path(self) -> Optional[Path]:
        return self._current_path

    # ------------------------------------------------------------------
    # Session listing
    # ------------------------------------------------------------------

    def list_sessions(self) -> List[Path]:
        """Return all CSV log files sorted newest-first."""
        return sorted(self._dir.glob("flight_*.csv"), reverse=True)

    @staticmethod
    def read_session(path: Path) -> List[dict]:
        """Read a saved CSV log and return a list of row dicts."""
        rows: List[dict] = []
        if not path.exists():
            return rows
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows
