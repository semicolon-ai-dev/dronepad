"""Flight controls panel — arm/disarm, modes, takeoff, land, RTL."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Callable

BG      = "#0f0f11"
SURFACE = "#18181b"
BORDER  = "#27272a"
PRIMARY = "#7c3aed"
SUCCESS = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"
TEXT    = "#fafafa"
MUTED   = "#71717a"

FLIGHT_MODES = ["STABILIZE", "LOITER", "ALT_HOLD", "AUTO", "GUIDED", "RTL", "LAND"]


class ControlsPanel(tk.Frame):
    def __init__(self, parent,
                 on_arm: Callable[[], None],
                 on_disarm: Callable[[], None],
                 on_takeoff: Callable[[float], None],
                 on_land: Callable[[], None],
                 on_rtl: Callable[[], None],
                 on_mode: Callable[[str], None],
                 **kw):
        super().__init__(parent, bg=BG, **kw)
        self._on_arm, self._on_disarm = on_arm, on_disarm
        self._on_takeoff, self._on_land, self._on_rtl = on_takeoff, on_land, on_rtl
        self._on_mode = on_mode
        self._build()

    def _build(self):
        tk.Label(self, text="FLIGHT CONTROLS", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        arm_row = tk.Frame(self, bg=BG)
        arm_row.pack(fill=tk.X, padx=12, pady=2)
        self._arm_btn = tk.Button(arm_row, text="ARM", bg=SUCCESS, fg="#000",
                                   relief=tk.FLAT, font=("Helvetica", 10, "bold"),
                                   padx=14, pady=6, cursor="hand2", command=self._arm)
        self._arm_btn.pack(side=tk.LEFT, padx=(0, 4))
        self._disarm_btn = tk.Button(arm_row, text="DISARM", bg=SURFACE, fg=MUTED,
                                      relief=tk.FLAT, font=("Helvetica", 10, "bold"),
                                      padx=14, pady=6, cursor="hand2", command=self._disarm)
        self._disarm_btn.pack(side=tk.LEFT)

        act_row = tk.Frame(self, bg=BG)
        act_row.pack(fill=tk.X, padx=12, pady=(4, 2))
        for label, cmd, color in [("TAKEOFF", self._takeoff, PRIMARY), ("LAND", self._land, WARN), ("RTL", self._rtl, DANGER)]:
            tk.Button(act_row, text=label, bg=color, fg=TEXT, relief=tk.FLAT,
                      font=("Helvetica", 10, "bold"), padx=10, pady=6,
                      cursor="hand2", command=cmd).pack(side=tk.LEFT, padx=(0, 4))

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, padx=12, pady=8)
        tk.Label(self, text="FLIGHT MODE", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12)

        mode_row = tk.Frame(self, bg=BG)
        mode_row.pack(fill=tk.X, padx=12, pady=4)
        for mode in FLIGHT_MODES:
            tk.Button(mode_row, text=mode, bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                      font=("Helvetica", 8, "bold"), padx=8, pady=4, cursor="hand2",
                      command=lambda m=mode: self._set_mode(m)).pack(side=tk.LEFT, padx=2, pady=2)

        alt_row = tk.Frame(self, bg=BG)
        alt_row.pack(fill=tk.X, padx=12, pady=(4, 10))
        tk.Label(alt_row, text="Takeoff alt (m):", bg=BG, fg=MUTED,
                 font=("Helvetica", 9)).pack(side=tk.LEFT)
        self._alt_entry = tk.Entry(alt_row, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                    relief=tk.FLAT, font=("Helvetica", 9), width=6)
        self._alt_entry.insert(0, "10")
        self._alt_entry.pack(side=tk.LEFT, padx=8, ipady=3)

    def _arm(self):
        if messagebox.askyesno("Confirm", "Arm the drone? Propellers will spin."):
            self._arm_btn.config(bg=DANGER)
            self._disarm_btn.config(bg=SUCCESS, fg="#000")
            self._on_arm()

    def _disarm(self):
        self._arm_btn.config(bg=SUCCESS)
        self._disarm_btn.config(bg=SURFACE, fg=MUTED)
        self._on_disarm()

    def _takeoff(self):
        try: alt = float(self._alt_entry.get())
        except ValueError: alt = 10.0
        self._on_takeoff(alt)

    def _land(self): self._on_land()
    def _rtl(self):  self._on_rtl()
    def _set_mode(self, mode: str): self._on_mode(mode)

    def set_armed_state(self, armed: bool):
        self._arm_btn.config(bg=DANGER if armed else SUCCESS)
        self._disarm_btn.config(bg=SUCCESS if not armed else SURFACE,
                                 fg="#000" if not armed else MUTED)
