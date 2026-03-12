"""Mission planner panel — waypoint list."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import List

BG      = "#0f0f11"
SURFACE = "#18181b"
BORDER  = "#27272a"
PRIMARY = "#7c3aed"
DANGER  = "#ef4444"
TEXT    = "#fafafa"
MUTED   = "#71717a"


@dataclass
class Waypoint:
    index: int
    lat:   float
    lon:   float
    alt:   float
    cmd:   str = "NAV_WAYPOINT"


class MissionPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._waypoints: List[Waypoint] = []
        self._build()

    def _build(self):
        tk.Label(self, text="MISSION PLANNER", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        cols = ("#", "Lat", "Lon", "Alt (m)", "Command")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("M.Treeview", background=SURFACE, foreground=TEXT,
                         fieldbackground=SURFACE, rowheight=28, borderwidth=0)
        style.configure("M.Treeview.Heading", background=BG, foreground=MUTED,
                         font=("Helvetica", 8, "bold"), relief="flat")
        style.map("M.Treeview", background=[("selected", PRIMARY)])

        self._tree = ttk.Treeview(self, columns=cols, show="headings",
                                   style="M.Treeview", height=8)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=60 if col == "#" else 110, anchor="center")
        self._tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill=tk.X, padx=12, pady=(4, 10))

        self._entries: dict[str, tk.Entry] = {}
        for lbl, default in [("Lat", "47.606"), ("Lon", "-122.332"), ("Alt", "30")]:
            tk.Label(btn_row, text=lbl, bg=BG, fg=MUTED, font=("Helvetica", 8)).pack(side=tk.LEFT)
            e = tk.Entry(btn_row, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                         relief=tk.FLAT, font=("Helvetica", 9), width=9)
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=(2, 6), ipady=3)
            self._entries[lbl] = e

        tk.Button(btn_row, text="+ Add", bg=PRIMARY, fg=TEXT, relief=tk.FLAT,
                  font=("Helvetica", 9, "bold"), padx=8, cursor="hand2",
                  command=self._add).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="\u2715 Remove", bg=SURFACE, fg=DANGER, relief=tk.FLAT,
                  font=("Helvetica", 9, "bold"), padx=8, cursor="hand2",
                  command=self._remove).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="Clear", bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                  font=("Helvetica", 9, "bold"), padx=8, cursor="hand2",
                  command=self._clear).pack(side=tk.LEFT, padx=4)

    def _add(self):
        try:
            lat = float(self._entries["Lat"].get())
            lon = float(self._entries["Lon"].get())
            alt = float(self._entries["Alt"].get())
        except ValueError:
            return
        idx = len(self._waypoints) + 1
        self._waypoints.append(Waypoint(idx, lat, lon, alt))
        self._tree.insert("", "end", values=(idx, f"{lat:.5f}", f"{lon:.5f}", f"{alt:.0f}", "NAV_WAYPOINT"))

    def _remove(self):
        for item in self._tree.selection():
            self._tree.delete(item)
        self._waypoints = []
        for i, item in enumerate(self._tree.get_children(), 1):
            vals = self._tree.item(item, "values")
            self._waypoints.append(Waypoint(i, float(vals[1]), float(vals[2]), float(vals[3])))
            self._tree.item(item, values=(i, vals[1], vals[2], vals[3], vals[4]))

    def _clear(self):
        self._waypoints.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)

    @property
    def waypoints(self) -> List[Waypoint]:
        return list(self._waypoints)
