"""Mission logic — validation, distance calculation, MAVLink upload helpers."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Waypoint:
    lat:  float
    lon:  float
    alt:  float          # metres AGL
    cmd:  str = "NAV_WAYPOINT"
    loiter_radius: float = 0.0

    def distance_to(self, other: "Waypoint") -> float:
        """Haversine distance in metres."""
        R = 6_371_000
        lat1, lon1 = math.radians(self.lat), math.radians(self.lon)
        lat2, lon2 = math.radians(other.lat), math.radians(other.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))


@dataclass
class Mission:
    waypoints: List[Waypoint] = field(default_factory=list)

    def add(self, wp: Waypoint) -> None:
        self.waypoints.append(wp)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.waypoints):
            del self.waypoints[index]

    def clear(self) -> None:
        self.waypoints.clear()

    @property
    def total_distance(self) -> float:
        """Sum of leg distances in metres."""
        total = 0.0
        for a, b in zip(self.waypoints, self.waypoints[1:]):
            total += a.distance_to(b)
        return total

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Returns (ok, error_message).  None error_message means all good."""
        if len(self.waypoints) == 0:
            return False, "Mission has no waypoints."
        for i, wp in enumerate(self.waypoints):
            if not (-90 <= wp.lat <= 90):
                return False, f"WP {i+1}: latitude {wp.lat} out of range."
            if not (-180 <= wp.lon <= 180):
                return False, f"WP {i+1}: longitude {wp.lon} out of range."
            if wp.alt < 0:
                return False, f"WP {i+1}: altitude cannot be negative."
            if wp.alt > 400:
                return False, f"WP {i+1}: altitude {wp.alt}m exceeds 400m limit."
        return True, None

    def to_dict_list(self) -> List[dict]:
        """Serialise to a list of dicts (JSON / export friendly)."""
        return [
            {"index": i + 1, "lat": w.lat, "lon": w.lon,
             "alt": w.alt, "cmd": w.cmd}
            for i, w in enumerate(self.waypoints)
        ]
