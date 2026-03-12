"""Main dashboard UI — telemetry widgets."""
import tkinter as tk
from tkinter import ttk, font
from app.mavlink_handler import MAVLinkHandler, TelemetryFrame


BG       = "#0f0f11"
SURFACE  = "#18181b"
BORDER   = "#27272a"
PRIMARY  = "#7c3aed"
SUCCESS  = "#22c55e"
WARN     = "#f59e0b"
DANGER   = "#ef4444"
TEXT     = "#fafafa"
MUTED    = "#71717a"


class TelemetryCard(tk.Frame):
    def __init__(self, parent, label: str, unit: str = "", **kw):
        super().__init__(parent, bg=SURFACE, **kw)
        self.configure(highlightbackground=BORDER, highlightthickness=1)
        tk.Label(self, text=label.upper(), bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        self._var = tk.StringVar(value="—")
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
        self.handler: MAVLinkHandler | None = None
        self._build_ui()

    def _build_ui(self):
        # Top bar
        bar = tk.Frame(self, bg=SURFACE, height=56)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tk.Label(bar, text="🚩  DronePad", bg=SURFACE, fg=TEXT,
                 font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=16)

        self._status_label = tk.Label(bar, text="●  Disconnected", bg=SURFACE, fg=DANGER,
                                       font=("Helvetica", 10, "bold"))
        self._status_label.pack(side=tk.RIGHT, padx=16)

        # Connection bar
        conn_frame = tk.Frame(self, bg="#101012")
        conn_frame.pack(fill=tk.X, padx=16, pady=8)
        tk.Label(conn_frame, text="Connection:", bg="#101012", fg=MUTED,
                 font=("Helvetica", 9)).pack(side=tk.LEFT)
        self._conn_entry = tk.Entry(conn_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                    relief=tk.FLAT, font=("Helvetica", 10), width=30)
        self._conn_entry.insert(0, "udp:127.0.0.1:14550")
        self._conn_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        tk.Button(conn_frame, text="Connect", bg=PRIMARY, fg=TEXT, relief=tk.FLAT,
                  font=("Helvetica", 9, "bold"), padx=10,
                  command=self._connect).pack(side=tk.LEFT)

        # Telemetry cards grid
        grid = tk.Frame(self, bg=BG)
        grid.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        for i in range(4):
            grid.columnconfigure(i, weight=1, uniform="col")

        self._cards = {
            "alt":     TelemetryCard(grid, "Altitude",    "m AGL"),
            "speed":   TelemetryCard(grid, "Groundspeed", "m/s"),
            "batt":    TelemetryCard(grid, "Battery",     "%"),
            "heading": TelemetryCard(grid, "Heading",     "°"),
            "sats":    TelemetryCard(grid, "Satellites",  "GPS"),
            "mode":    TelemetryCard(grid, "Flight Mode", ""),
            "roll":    TelemetryCard(grid, "Roll",        "°"),
            "pitch":   TelemetryCard(grid, "Pitch",       "°"),
        }
        positions = [(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)]
        for (row, col), card in zip(positions, self._cards.values()):
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

        # Armed status
        self._armed_label = tk.Label(self, text="DISARMED", bg=BG, fg=SUCCESS,
                                      font=("Helvetica", 13, "bold"))
        self._armed_label.pack(pady=4)

    def _connect(self):
        cs = self._conn_entry.get().strip()
        if not cs:
            return
        self.handler = MAVLinkHandler(cs, self._on_telemetry)
        self.handler.connect()
        self._status_label.config(text="●  Connecting...", fg=WARN)

    def _on_telemetry(self, frame: TelemetryFrame):
        self.after(0, self._update_ui, frame)

    def _update_ui(self, f: TelemetryFrame):
        self._cards["alt"].update_value(f"{f.rel_alt:.1f}")
        self._cards["speed"].update_value(f"{f.groundspeed:.1f}")
        self._cards["batt"].update_value(str(f.battery_pct))
        self._cards["heading"].update_value(f"{f.heading:.0f}")
        self._cards["sats"].update_value(str(f.satellites))
        self._cards["mode"].update_value(f.mode)
        self._cards["roll"].update_value(f"{f.roll:.1f}")
        self._cards["pitch"].update_value(f"{f.pitch:.1f}")
        self._armed_label.config(
            text="ARMED" if f.armed else "DISARMED",
            fg=DANGER if f.armed else SUCCESS
        )
        if self.handler and self.handler.connected:
            self._status_label.config(text="●  Connected", fg=SUCCESS)
