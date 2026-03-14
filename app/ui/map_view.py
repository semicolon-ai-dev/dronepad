"""Live drone position map — pure Tkinter canvas, no external map tiles required."""
from __future__ import annotations
import math
import tkinter as tk
from typing import List, Optional, Tuple
from app.mavlink_handler import TelemetryFrame

BG      = "#0f0f11"
SURFACE = "#18181b"
BORDER  = "#27272a"
GRID    = "#1f1f22"
PRIMARY = "#7c3aed"
SUCCESS = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"
TEXT    = "#fafafa"
MUTED   = "#71717a"
TRACK   = "#4c1d95"

_EARTH_R = 6_371_000.0  # metres


def _latlon_to_m(lat: float, lon: float, ref_lat: float, ref_lon: float) -> Tuple[float, float]:
    """Convert lat/lon to local East/North metres relative to a reference point."""
    dlat = math.radians(lat - ref_lat)
    dlon = math.radians(lon - ref_lon)
    north = dlat * _EARTH_R
    east  = dlon * _EARTH_R * math.cos(math.radians(ref_lat))
    return east, north


class MapView(tk.Frame):
    """Tkinter canvas showing drone position, heading, track history, and waypoints."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._ref_lat:  Optional[float] = None
        self._ref_lon:  Optional[float] = None
        self._track:    List[Tuple[float, float]] = []  # (east, north) metres
        self._scale:    float = 5.0   # pixels per metre
        self._pan_x:    float = 0.0
        self._pan_y:    float = 0.0
        self._drag_start: Optional[Tuple[int, int]] = None
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill=tk.X, padx=12, pady=(8, 0))
        tk.Label(hdr, text="MAP VIEW", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)

        # Zoom controls
        ctrl = tk.Frame(hdr, bg=BG)
        ctrl.pack(side=tk.RIGHT)
        tk.Button(ctrl, text="+", bg=SURFACE, fg=TEXT, relief=tk.FLAT,
                  font=("Helvetica", 10, "bold"), padx=6, cursor="hand2",
                  command=self._zoom_in).pack(side=tk.LEFT)
        tk.Button(ctrl, text="−", bg=SURFACE, fg=TEXT, relief=tk.FLAT,
                  font=("Helvetica", 10, "bold"), padx=6, cursor="hand2",
                  command=self._zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="⊙ Center", bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                  font=("Helvetica", 8, "bold"), padx=6, cursor="hand2",
                  command=self._recenter).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="✕ Clear track", bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                  font=("Helvetica", 8, "bold"), padx=6, cursor="hand2",
                  command=self._clear_track).pack(side=tk.LEFT, padx=2)

        # Canvas
        self._canvas = tk.Canvas(self, bg=SURFACE,
                                  highlightbackground=BORDER, highlightthickness=1,
                                  cursor="fleur")
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # Coordinate label
        self._coord_var = tk.StringVar(value="Lat: —  Lon: —  Alt: — m")
        tk.Label(self, textvariable=self._coord_var, bg=BG, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=14, pady=(0, 6))

        # Mouse bindings
        self._canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_drag_end)
        self._canvas.bind("<MouseWheel>",        self._on_scroll)
        self._canvas.bind("<Button-4>",          self._on_scroll)
        self._canvas.bind("<Button-5>",          self._on_scroll)
        self._canvas.bind("<Configure>",         lambda e: self._redraw())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_frame(self, frame: TelemetryFrame) -> None:
        if self._ref_lat is None:
            self._ref_lat = frame.lat
            self._ref_lon = frame.lon
        east, north = _latlon_to_m(frame.lat, frame.lon, self._ref_lat, self._ref_lon)
        if not self._track or self._track[-1] != (east, north):
            self._track.append((east, north))
            if len(self._track) > 4000:
                self._track = self._track[-4000:]
        self._heading = frame.heading
        self._armed   = frame.armed
        self._alt     = frame.rel_alt
        self._coord_var.set(
            f"Lat: {frame.lat:.6f}  Lon: {frame.lon:.6f}  Alt: {frame.rel_alt:.1f} m"
        )
        self._redraw()

    def reset(self) -> None:
        self._ref_lat  = None
        self._ref_lon  = None
        self._track    = []
        self._pan_x    = 0.0
        self._pan_y    = 0.0
        self._canvas.delete("all")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _redraw(self) -> None:
        c = self._canvas
        c.delete("all")
        w = c.winfo_width()  or 400
        h = c.winfo_height() or 300
        cx = w / 2 + self._pan_x
        cy = h / 2 + self._pan_y

        # Grid lines
        step_m = self._nice_step()
        step_px = step_m * self._scale
        for i in range(-20, 21):
            x = cx + i * step_px
            y = cy + i * step_px
            c.create_line(x, 0, x, h, fill=GRID, width=1)
            c.create_line(0, y, w, y, fill=GRID, width=1)

        # Grid scale label
        c.create_text(w - 10, h - 10, text=f"{step_m:.0f} m / grid",
                      fill=MUTED, font=("Helvetica", 8), anchor="se")

        if not self._track:
            c.create_text(w // 2, h // 2, text="Waiting for GPS…",
                           fill=MUTED, font=("Helvetica", 12))
            return

        # Track line
        if len(self._track) >= 2:
            pts = []
            for (e, n) in self._track:
                pts.extend([cx + e * self._scale, cy - n * self._scale])
            c.create_line(*pts, fill=TRACK, width=2, smooth=True)

        # Drone icon at last position
        e, n = self._track[-1]
        dx = cx + e * self._scale
        dy = cy - n * self._scale
        heading = getattr(self, "_heading", 0.0)
        armed   = getattr(self, "_armed",   False)
        color   = DANGER if armed else SUCCESS

        # Arrow body
        angle  = math.radians(heading)
        r      = 14
        tip_x  = dx + r * math.sin(angle)
        tip_y  = dy - r * math.cos(angle)
        left_x = dx + (r * 0.55) * math.sin(angle + math.pi * 0.75)
        left_y = dy - (r * 0.55) * math.cos(angle + math.pi * 0.75)
        right_x = dx + (r * 0.55) * math.sin(angle - math.pi * 0.75)
        right_y = dy - (r * 0.55) * math.cos(angle - math.pi * 0.75)
        c.create_polygon(tip_x, tip_y, left_x, left_y, dx, dy, right_x, right_y,
                          fill=color, outline="", smooth=False)
        c.create_oval(dx - 5, dy - 5, dx + 5, dy + 5,
                       fill=color, outline="white", width=1)

        # Origin cross
        c.create_line(cx - 8, cy, cx + 8, cy, fill=MUTED, width=1)
        c.create_line(cx, cy - 8, cx, cy + 8, fill=MUTED, width=1)

    def _world_to_canvas(self, e: float, n: float) -> Tuple[float, float]:
        w = self._canvas.winfo_width()  or 400
        h = self._canvas.winfo_height() or 300
        cx = w / 2 + self._pan_x
        cy = h / 2 + self._pan_y
        return cx + e * self._scale, cy - n * self._scale

    def _nice_step(self) -> float:
        """Pick a round grid step size based on current scale."""
        target_px = 80.0
        raw = target_px / self._scale
        mag = 10 ** math.floor(math.log10(raw))
        for f in (1, 2, 5, 10):
            if f * mag >= raw:
                return f * mag
        return 10 * mag

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def _zoom_in(self):  self._scale = min(self._scale * 1.5, 200.0); self._redraw()
    def _zoom_out(self): self._scale = max(self._scale / 1.5, 0.1);   self._redraw()
    def _recenter(self): self._pan_x = 0.0; self._pan_y = 0.0;        self._redraw()
    def _clear_track(self): self._track = self._track[-1:];            self._redraw()

    def _on_drag_start(self, e): self._drag_start = (e.x, e.y)

    def _on_drag(self, e):
        if self._drag_start:
            self._pan_x += e.x - self._drag_start[0]
            self._pan_y += e.y - self._drag_start[1]
            self._drag_start = (e.x, e.y)
            self._redraw()

    def _on_drag_end(self, _): self._drag_start = None

    def _on_scroll(self, e):
        if e.num == 4 or e.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
