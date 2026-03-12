"""MAVLink connection handler — UDP and serial."""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None  # type: ignore


@dataclass
class TelemetryFrame:
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0          # metres AMSL
    rel_alt: float = 0.0      # metres AGL
    heading: float = 0.0      # degrees
    groundspeed: float = 0.0  # m/s
    battery_pct: int = 0
    battery_v: float = 0.0
    armed: bool = False
    mode: str = "UNKNOWN"
    satellites: int = 0
    fix_type: int = 0
    roll: float = 0.0
    pitch: float = 0.0
    timestamp: float = field(default_factory=time.time)


class MAVLinkHandler:
    def __init__(self, connection_string: str, on_update: Callable[[TelemetryFrame], None]):
        self.connection_string = connection_string
        self.on_update = on_update
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.frame = TelemetryFrame()
        self.connected = False

    def connect(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def disconnect(self):
        self._running = False

    def _run(self):
        if mavutil is None:
            return
        try:
            conn = mavutil.mavlink_connection(self.connection_string, autoreconnect=True)
            conn.wait_heartbeat(timeout=10)
            self.connected = True
            conn.mav.request_data_stream_send(
                conn.target_system, conn.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1
            )
            while self._running:
                msg = conn.recv_match(blocking=True, timeout=1)
                if msg is None:
                    continue
                self._parse(msg)
                self.on_update(self.frame)
        except Exception as e:
            print(f"[MAVLink] Connection error: {e}")
            self.connected = False

    def _parse(self, msg):
        t = msg.get_type()
        if t == "GLOBAL_POSITION_INT":
            self.frame.lat      = msg.lat / 1e7
            self.frame.lon      = msg.lon / 1e7
            self.frame.alt      = msg.alt / 1000
            self.frame.rel_alt  = msg.relative_alt / 1000
            self.frame.heading  = msg.hdg / 100
        elif t == "VFR_HUD":
            self.frame.groundspeed = msg.groundspeed
            self.frame.alt         = msg.alt
        elif t == "BATTERY_STATUS":
            self.frame.battery_pct = msg.battery_remaining
            if msg.voltages:
                self.frame.battery_v = msg.voltages[0] / 1000
        elif t == "HEARTBEAT":
            self.frame.armed = bool(msg.base_mode & 0x80)
            self.frame.mode  = str(msg.custom_mode)
        elif t == "GPS_RAW_INT":
            self.frame.satellites = msg.satellites_visible
            self.frame.fix_type   = msg.fix_type
        elif t == "ATTITUDE":
            import math
            self.frame.roll  = math.degrees(msg.roll)
            self.frame.pitch = math.degrees(msg.pitch)
        self.frame.timestamp = time.time()
