"""Main dashboard — 5 tabs: Telemetry / Map / Controls / Mission / Log + Alerts."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from app.mavlink_handler import MAVLinkHandler, TelemetryFrame
from app.simulator       import TelemetrySimulator
from app.telemetry       import TelemetryHistory
from app.logger          import FlightLogger
from app.ui.controls     import ControlsPanel
from app.ui.mission      import MissionPanel
from app.ui.map_view     import MapView
from app.ui.alerts       import AlertsPanel
from app.ui.log_panel    import LogPanel

BG      = "#0f0f11"
SURFACE = "#18181b"
BORDER  = "#27272a"
PRIMARY = "#7c3aed"
SUCCESS = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"
TEXT    = "#fafafa"
MUTED   = "#71717a"


class TelemetryCard(tk.Frame):
    def __init__(self, parent, label: str, unit: str = "", **kw):
        super().__init__(parent, bg=SURFACE, **kw)
        self.configure(highlightbackground=BORDER, highlightthickness=1)
        tk.Label(self, text=label.upper(), bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        self._var = tk.StringVar(value="\u2014")
        tk.Label(self, textvariable=self._var, bg=SURFACE, fg=TEXT,
                 font=("Helvetica", 22, "bold")).pack(anchor="w", padx=12)
        if unit:
            tk.Label(self, text=unit, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9)).pack(anchor="w", padx=12, pady=(0, 10))

    def update_value(self, value: str, color: str = TEXT):
        self._var.set(value)


class DashboardApp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._handler:  MAVLinkHandler    | None = None
        self._sim:      TelemetrySimulator | None = None
        self._history   = TelemetryHistory()
        self._logger    = FlightLogger()
        self._was_armed = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ---- top bar ----
        bar = tk.Frame(self, bg=SURFACE, height=52)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tk.Label(bar, text="\U0001f7e9  DronePad", bg=SURFACE, fg=TEXT,
                 font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=16)
        self._status_label = tk.Label(bar, text="\u25cf  Disconnected",
                                       bg=SURFACE, fg=DANGER,
                                       font=("Helvetica", 10, "bold"))
        self._status_label.pack(side=tk.RIGHT, padx=16)
        self._armed_label = tk.Label(bar, text="DISARMED",
                                      bg=SURFACE, fg=SUCCESS,
                                      font=("Helvetica", 10, "bold"))
        self._armed_label.pack(side=tk.RIGHT, padx=8)
        self._log_indicator = tk.Label(bar, text="", bg=SURFACE, fg=DANGER,
                                        font=("Helvetica", 9, "bold"))
        self._log_indicator.pack(side=tk.RIGHT, padx=8)

        # ---- connection bar ----
        row = tk.Frame(self, bg="#101012")
        row.pack(fill=tk.X, padx=16, pady=6)
        tk.Label(row, text="Connection:", bg="#101012", fg=MUTED,
                 font=("Helvetica", 9)).pack(side=tk.LEFT)
        self._conn_entry = tk.Entry(row, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                     relief=tk.FLAT, font=("Helvetica", 10), width=28)
        self._conn_entry.insert(0, "udp:127.0.0.1:14550")
        self._conn_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        tk.Button(row, text="Connect", bg=PRIMARY, fg=TEXT, relief=tk.FLAT,
                   font=("Helvetica", 9, "bold"), padx=10, cursor="hand2",
                   command=self._connect).pack(side=tk.LEFT)
        tk.Button(row, text="Simulate", bg="#27272a", fg=TEXT, relief=tk.FLAT,
                   font=("Helvetica", 9, "bold"), padx=10, cursor="hand2",
                   command=self._start_sim).pack(side=tk.LEFT, padx=6)
        tk.Button(row, text="Disconnect", bg="#27272a", fg=MUTED, relief=tk.FLAT,
                   font=("Helvetica", 9, "bold"), padx=10, cursor="hand2",
                   command=self._disconnect).pack(side=tk.LEFT, padx=2)

        # ---- tabs ----
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("DP.TNotebook",     background=BG, borderwidth=0)
        style.configure("DP.TNotebook.Tab", background=SURFACE, foreground=MUTED,
                         font=("Helvetica", 9, "bold"), padding=(16, 6))
        style.map("DP.TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", TEXT)])

        nb = ttk.Notebook(self, style="DP.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1 — Telemetry
        t1 = tk.Frame(nb, bg=BG)
        nb.add(t1, text="  Telemetry  ")
        self._build_telemetry(t1)

        # Tab 2 — Map
        t2 = tk.Frame(nb, bg=BG)
        nb.add(t2, text="  Map  ")
        self._map = MapView(t2)
        self._map.pack(fill=tk.BOTH, expand=True)

        # Tab 3 — Controls
        t3 = tk.Frame(nb, bg=BG)
        nb.add(t3, text="  Controls  ")
        self._controls = ControlsPanel(
            t3,
            on_arm=self._cmd_arm, on_disarm=self._cmd_disarm,
            on_takeoff=self._cmd_takeoff, on_land=self._cmd_land,
            on_rtl=self._cmd_rtl, on_mode=self._cmd_mode,
        )
        self._controls.pack(fill=tk.BOTH, expand=True)

        # Tab 4 — Mission
        t4 = tk.Frame(nb, bg=BG)
        nb.add(t4, text="  Mission  ")
        self._mission = MissionPanel(t4)
        self._mission.pack(fill=tk.BOTH, expand=True)

        # Tab 5 — Alerts
        t5 = tk.Frame(nb, bg=BG)
        nb.add(t5, text="  Alerts  ")
        self._alerts = AlertsPanel(t5, on_alert=self._handle_alert)
        self._alerts.pack(fill=tk.BOTH, expand=True)

        # Tab 6 — Log
        t6 = tk.Frame(nb, bg=BG)
        nb.add(t6, text="  Log  ")
        self._log = LogPanel(t6)
        self._log.pack(fill=tk.BOTH, expand=True)
        self._log.log("DronePad started.", "OK")
        self._log.log("Press Simulate to generate synthetic telemetry, or enter a MAVLink connection string.", "INFO")

    def _build_telemetry(self, parent: tk.Frame) -> None:
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)
        for i in range(4):
            grid.columnconfigure(i, weight=1, uniform="col")
        self._cards = {
            "alt":     TelemetryCard(grid, "Altitude",    "m AGL"),
            "speed":   TelemetryCard(grid, "Groundspeed", "m/s"),
            "batt":    TelemetryCard(grid, "Battery",     "%"),
            "heading": TelemetryCard(grid, "Heading",     "deg"),
            "sats":    TelemetryCard(grid, "Satellites",  "GPS"),
            "mode":    TelemetryCard(grid, "Flight Mode", ""),
            "roll":    TelemetryCard(grid, "Roll",        "deg"),
            "pitch":   TelemetryCard(grid, "Pitch",       "deg"),
        }
        positions = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
        for (r, c), card in zip(positions, self._cards.values()):
            card.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        gps_row = tk.Frame(parent, bg=SURFACE,
                            highlightbackground=BORDER, highlightthickness=1)
        gps_row.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(gps_row, text="GPS:", bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=12, pady=6)
        self._gps_var = tk.StringVar(value="\u2014")
        tk.Label(gps_row, textvariable=self._gps_var, bg=SURFACE, fg=TEXT,
                 font=("Courier", 10)).pack(side=tk.LEFT, padx=4)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        cs = self._conn_entry.get().strip()
        if not cs:
            return
        self._disconnect()
        self._handler = MAVLinkHandler(cs, self._on_telemetry)
        self._handler.connect()
        self._status_label.config(text="\u25cf  Connecting…", fg=WARn if False else "#f59e0b")
        self._log.log(f"Connecting to {cs}…", "INFO")

    def _start_sim(self) -> None:
        self._disconnect()
        self._sim = TelemetrySimulator(self._on_telemetry)
        self._sim.start()
        self._status_label.config(text="\u25cf  Simulating", fg=WARn if False else "#f59e0b")
        self._map.reset()
        self._history.clear()
        self._log.log("Simulator started — synthetic telemetry at 4 Hz.", "OK")

    def _disconnect(self) -> None:
        if self._handler:
            self._handler.disconnect()
            self._handler = None
        if self._sim:
            self._sim.stop()
            self._sim = None
        if self._logger.is_logging:
            path = self._logger.stop()
            self._log.log(f"Log saved: {path}", "OK")
            self._log_indicator.config(text="")
        self._status_label.config(text="\u25cf  Disconnected", fg=DANGER)

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    def _on_telemetry(self, frame: TelemetryFrame) -> None:
        self.after(0, self._update_ui, frame)

    def _update_ui(self, f: TelemetryFrame) -> None:
        # History & logging
        self._history.push(f)
        # Auto-start log on arm, auto-stop on disarm
        if f.armed and not self._was_armed:
            path = self._logger.start()
            self._log.log(f"Flight log started: {path}", "OK")
            self._log_indicator.config(text="● REC", fg=DANGER)
        elif not f.armed and self._was_armed and self._logger.is_logging:
            path = self._logger.stop()
            self._log.log(f"Flight log saved: {path}", "OK")
            self._log_indicator.config(text="")
        self._was_armed = f.armed
        if self._logger.is_logging:
            self._logger.write(f)

        # Cards
        self._cards["alt"].update_value(f"{f.rel_alt:.1f}")
        self._cards["speed"].update_value(f"{f.groundspeed:.1f}")
        self._cards["batt"].update_value(str(f.battery_pct))
        self._cards["heading"].update_value(f"{f.heading:.0f}")
        self._cards["sats"].update_value(str(f.satellites))
        self._cards["mode"].update_value(f.mode)
        self._cards["roll"].update_value(f"{f.roll:.1f}")
        self._cards["pitch"].update_value(f"{f.pitch:.1f}")
        self._gps_var.set(f"{f.lat:.6f}, {f.lon:.6f}")
        self._armed_label.config(text="ARMED" if f.armed else "DISARMED",
                                  fg=DANGER if f.armed else SUCCESS)
        if self._handler and self._handler.connected:
            self._status_label.config(text="\u25cf  Connected", fg=SUCCESS)

        # Map
        self._map.update_frame(f)

        # Alerts
        self._alerts.check_frame(f)

        # Controls state
        self._controls.set_armed_state(f.armed)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _cmd_arm(self) -> None:
        if self._sim:
            self._sim.arm()
        elif self._handler:
            pass  # send MAVLink arm command
        self._log.log("ARM command sent.", "WARN")

    def _cmd_disarm(self) -> None:
        if self._sim:
            self._sim.disarm()
        self._log.log("DISARM command sent.", "INFO")

    def _cmd_takeoff(self, alt: float) -> None:
        if self._sim:
            self._sim.arm()
        self._log.log(f"TAKEOFF to {alt:.0f} m requested.", "INFO")

    def _cmd_land(self) -> None:
        if self._sim:
            self._sim.set_mode("LAND")
        self._log.log("LAND command sent.", "WARN")

    def _cmd_rtl(self) -> None:
        if self._sim:
            self._sim.set_mode("RTL")
        self._log.log("RTL command sent.", "WARN")

    def _cmd_mode(self, mode: str) -> None:
        if self._sim:
            self._sim.set_mode(mode)
        self._log.log(f"Mode \u2192 {mode}", "INFO")

    def _handle_alert(self, level: str, msg: str) -> None:
        lvl_map = {"CRITICAL": "ERROR", "WARN": "WARN"}
        self._log.log(f"[ALERT] {msg}", lvl_map.get(level, "WARN"))  # type: ignore
