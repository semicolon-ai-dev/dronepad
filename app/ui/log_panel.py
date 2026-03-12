"""Scrollable coloured console log panel."""
from __future__ import annotations
import datetime
import tkinter as tk
from typing import Literal

BG      = "#0f0f11"
SURFACE = "#0d0d0f"
BORDER  = "#27272a"
TEXT    = "#fafafa"
MUTED   = "#71717a"
SUCCESS = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"
INFO    = "#38bdf8"

Level = Literal["INFO", "WARN", "ERROR", "OK"]


class LogPanel(tk.Frame):
    def __init__(self, parent, max_lines: int = 500, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._max = max_lines
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill=tk.X, padx=12, pady=(8, 4))
        tk.Label(header, text="SYSTEM LOG", bg=BG, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        tk.Button(header, text="Clear", bg=SURFACE, fg=MUTED, relief=tk.FLAT,
                  font=("Helvetica", 8), padx=6, cursor="hand2",
                  command=self._clear).pack(side=tk.RIGHT)

        frame = tk.Frame(self, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        self._text = tk.Text(frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                              relief=tk.FLAT, font=("Courier", 9),
                              state=tk.DISABLED, wrap=tk.WORD, padx=8, pady=6,
                              selectbackground="#3f3f46")
        sb = tk.Scrollbar(frame, command=self._text.yview,
                          bg=BG, troughcolor=SURFACE, relief=tk.FLAT)
        self._text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(fill=tk.BOTH, expand=True)

        for tag, color in [("INFO", INFO), ("WARN", WARN), ("ERROR", DANGER),
                            ("OK", SUCCESS), ("ts", MUTED)]:
            self._text.tag_config(tag, foreground=color)

    def log(self, message: str, level: Level = "INFO"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, f"[{ts}] ", "ts")
        self._text.insert(tk.END, f"{level:<5} ", level)
        self._text.insert(tk.END, f"{message}\n")
        lines = int(self._text.index("end-1c").split(".")[0])
        if lines > self._max:
            self._text.delete("1.0", f"{lines - self._max}.0")
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def _clear(self):
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.config(state=tk.DISABLED)
