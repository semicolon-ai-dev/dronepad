"""Alert configuration panel — thresholds for battery, signal loss, geofence."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Callable, Optional
from app.mavlink_handler import TelemetryFrame

BG      = "#0f0f11"
SURFACE = "#18181b"
BORDER  = "#27272a"
PRIMARY = "#7c3aed"
SUCCESS = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"
TEXT    = "#fafafa"
MUTED   = "#71717a"


@dataclass
class AlertConfig:
    battery_warn_pct:  int   = 30
    battery_crit_pct:  int   = 15
    min_satellites:    int   = 6
    max_altitude_m:    float = 120.0
    signal_timeout_s:  float = 5.0
    geofence_radius_m: float = 500.0
    enabled:           bool  = True


class AlertEngine:
    """Evaluates a TelemetryFrame against an AlertConfig and fires callbacks."""

    def __init__(self, config: AlertConfig,
                 on_alert: Callable[[str, str], None]):
        self._cfg      = config
        self._on_alert = on_alert
        self._last_ts: Optional[float] = None

    def check(self, frame: TelemetryFrame) -> None:
        if not self._cfg.enabled:
            return
        c = self._cfg
        # Battery
        if frame.battery_pct <= c.battery_crit_pct:
            self._on_alert("CRITICAL", f"Battery critical: {frame.battery_pct}%")
        elif frame.battery_pct <= c.battery_warn_pct:
            self._on_alert("WARN", f"Battery low: {frame.battery_pct}%")
        # GPS
        if frame.satellites < c.min_satellites:
            self._on_alert("WARN", f"Low GPS sats: {frame.satellites} (min {c.min_satellites})")
        # Altitude
        if frame.rel_alt > c.max_altitude_m:
            self._on_alert("WARN", f"Altitude {frame.rel_alt:.1f}m exceeds limit {c.max_altitude_m}m")
        self._last_ts = frame.timestamp


class AlertsPanel(tk.Frame):
    """UI panel for configuring and viewing active alerts."""

    def __init__(self, parent, on_alert: Callable[[str, str], None], **kw):
        super().__init__(parent, bg=BG, **kw)
        self._config = AlertConfig()
        self._engine = AlertEngine(self._config, self._handle_alert)
        self._on_alert = on_alert
        self._alert_history: list[tuple[str, str]] = []
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # ---- Configuration section ----
        tk.Label(self, text="ALERT THRESHOLDS", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        cfg_frame = tk.Frame(self, bg=SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        cfg_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        self._vars: dict[str, tk.Variable] = {}
        rows = [
            ("Battery warn (%)",        "battery_warn_pct",  "int",   30),
            ("Battery critical (%)",     "battery_crit_pct",  "int",   15),
            ("Min GPS satellites",        "min_satellites",    "int",    6),
            ("Max altitude (m)",          "max_altitude_m",    "float", 120.0),
            ("Signal timeout (s)",        "signal_timeout_s",  "float",  5.0),
            ("Geofence radius (m)",       "geofence_radius_m", "float", 500.0),
        ]
        for row_lbl, key, typ, default in rows:
            row = tk.Frame(cfg_frame, bg=SURFACE)
            row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(row, text=row_lbl, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9), width=22, anchor="w").pack(side=tk.LEFT)
            var: tk.Variable = tk.IntVar(value=int(default)) if typ == "int" \
                else tk.DoubleVar(value=float(default))
            self._vars[key] = var
            e = tk.Entry(row, textvariable=var, bg=BG, fg=TEXT,
                          insertbackground=TEXT, relief=tk.FLAT,
                          font=("Helvetica", 9), width=8)
            e.pack(side=tk.LEFT, ipady=3)

        # Enable toggle
        en_row = tk.Frame(cfg_frame, bg=SURFACE)
        en_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(en_row, text="Alerts enabled", variable=self._enabled_var,
                        bg=SURFACE, fg=TEXT, selectcolor=BG,
                        activebackground=SURFACE, activeforeground=TEXT,
                        font=("Helvetica", 9), command=self._apply).pack(side=tk.LEFT)
        tk.Button(en_row, text="Apply", bg=PRIMARY, fg=TEXT, relief=tk.FLAT,
                   font=("Helvetica", 9, "bold"), padx=8, cursor="hand2",
                   command=self._apply).pack(side=tk.RIGHT, padx=4)

        # ---- Active alerts log ----
        tk.Label(self, text="ACTIVE ALERTS", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12, pady=(6, 2))

        tbl_frame = tk.Frame(self, bg=SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        tbl_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("A.Treeview", background=SURFACE, foreground=TEXT,
                         fieldbackground=SURFACE, rowheight=24, borderwidth=0)
        style.configure("A.Treeview.Heading", background=BG, foreground=MUTED,
                         font=("Helvetica", 8, "bold"), relief="flat")
        style.map("A.Treeview", background=[("selected", PRIMARY)])

        cols = ("Level", "Message")
        self._tree = ttk.Treeview(tbl_frame, columns=cols, show="headings",
                                   style="A.Treeview")
        self._tree.heading("Level",   text="Level")
        self._tree.heading("Message", text="Message")
        self._tree.column("Level",   width=80,  anchor="center")
        self._tree.column("Message", width=400, anchor="w")

        sb = ttk.Scrollbar(tbl_frame, orient=tk.VERTICAL,
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True)

        # Tag colours
        self._tree.tag_configure("CRITICAL", foreground=DANGER)
        self._tree.tag_configure("WARN",     foreground=WARn if False else WARn)
        self._tree.tag_configure("WARN",     foreground="#f59e0b")

        btn_row2 = tk.Frame(self, bg=BG)
        btn_row2.pack(fill=tk.X, padx=12, pady=(0, 6))
        tk.Button(btn_row2, text="Clear alerts", bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                   font=("Helvetica", 9, "bold"), padx=8, cursor="hand2",
                   command=self._clear).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply(self) -> None:
        c = self._config
        c.battery_warn_pct  = int(self._vars["battery_warn_pct"].get())
        c.battery_crit_pct  = int(self._vars["battery_crit_pct"].get())
        c.min_satellites    = int(self._vars["min_satellites"].get())
        c.max_altitude_m    = float(self._vars["max_altitude_m"].get())
        c.signal_timeout_s  = float(self._vars["signal_timeout_s"].get())
        c.geofence_radius_m = float(self._vars["geofence_radius_m"].get())
        c.enabled           = bool(self._enabled_var.get())

    def _handle_alert(self, level: str, msg: str) -> None:
        # Deduplicate — don't flood identical consecutive alerts
        if self._alert_history and self._alert_history[-1] == (level, msg):
            return
        self._alert_history.append((level, msg))
        tag = level
        self._tree.insert("", 0, values=(level, msg), tags=(tag,))
        self._on_alert(level, msg)

    def _clear(self) -> None:
        self._alert_history.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)

    def check_frame(self, frame: TelemetryFrame) -> None:
        """Called by dashboard every telemetry tick."""
        self._engine.check(frame)
