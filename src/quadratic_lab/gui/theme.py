"""Thème visuel commun (couleurs, polices, tableaux)."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

from ..models import Category

# Polices présentes par défaut sur chaque système (DejaVu est installée sur Ubuntu).
if sys.platform == "win32":
    FONT, MONO = "Segoe UI", "Consolas"
elif sys.platform == "darwin":  # pragma: no cover - non testé
    FONT, MONO = "Helvetica", "Menlo"
else:
    FONT, MONO = "DejaVu Sans", "DejaVu Sans Mono"

COLORS = {
    "primary": "#1F3A5F",
    "primary_light": "#E8EEF6",
    "bg": "#F4F6F9",
    "card": "#FFFFFF",
    "text": "#1C2430",
    "muted": "#5F6B7A",
    "pass": "#E6F4EA",
    "fail": "#FDE7E9",
    "pending": "#FFFFFF",
    "ok": "#1B7F3B",
    "ko": "#B3261E",
}

CATEGORY_COLORS = {
    Category.TWO_REAL_ROOTS: "#1B7F3B",
    Category.DOUBLE_REAL_ROOT: "#00695C",
    Category.NO_REAL_ROOT: "#B45309",
    Category.LINEAR_ROOT: "#1F5FAF",
    Category.INFINITE_SOLUTIONS: "#6A1B9A",
    Category.NO_SOLUTION: "#8D4E2A",
    Category.INVALID_INPUT: "#B3261E",
}


def apply_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    root.configure(background=COLORS["bg"])
    style.configure(".", font=(FONT, 10), background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["card"])
    style.configure("TLabelframe", background=COLORS["bg"], padding=10)
    style.configure("TLabelframe.Label", font=(FONT, 10, "bold"), foreground=COLORS["primary"], background=COLORS["bg"])
    style.configure("TLabel", background=COLORS["bg"])
    style.configure("Muted.TLabel", foreground=COLORS["muted"])
    style.configure("Big.TLabel", font=(FONT, 13, "bold"))
    style.configure("Mono.TLabel", font=(MONO, 10))
    style.configure("Header.TFrame", background=COLORS["primary"])
    style.configure("Header.TLabel", background=COLORS["primary"], foreground="white", font=(FONT, 18, "bold"))
    style.configure("SubHeader.TLabel", background=COLORS["primary"], foreground="#C9D6E8", font=(FONT, 10))
    style.configure("TButton", padding=(12, 6))
    style.configure("Accent.TButton", font=(FONT, 10, "bold"), foreground="white", background=COLORS["primary"])
    style.map("Accent.TButton", background=[("active", "#2C5282"), ("disabled", "#9AA8B8")])
    style.configure("TNotebook", background=COLORS["bg"], tabmargins=(8, 6, 8, 0))
    style.configure("TNotebook.Tab", padding=(16, 8), font=(FONT, 10, "bold"))
    style.map("TNotebook.Tab", background=[("selected", COLORS["card"])], foreground=[("selected", COLORS["primary"])])
    style.configure("Treeview", rowheight=24, font=(FONT, 9), fieldbackground=COLORS["card"])
    style.configure("Treeview.Heading", font=(FONT, 9, "bold"), background=COLORS["primary_light"])
    return style


def make_table(parent: tk.Misc, columns: list[tuple[str, str, int]], height: int = 10) -> tuple[ttk.Frame, ttk.Treeview]:
    """Tableau (Treeview) avec barres de défilement. ``columns`` : (id, titre, largeur)."""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
    for col_id, title, width in columns:
        tree.heading(col_id, text=title)
        tree.column(col_id, width=width, minwidth=40, anchor="center", stretch=True)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tree.tag_configure("pass", background=COLORS["pass"])
    tree.tag_configure("fail", background=COLORS["fail"])
    tree.tag_configure("pending", background=COLORS["pending"])
    return frame, tree


def make_text(parent: tk.Misc, height: int = 8, mono: bool = False) -> tk.Text:
    widget = tk.Text(
        parent,
        height=height,
        wrap="none" if mono else "word",
        font=(MONO, 10) if mono else (FONT, 10),
        relief="flat",
        background=COLORS["card"],
        foreground=COLORS["text"],
        padx=8,
        pady=6,
        borderwidth=1,
        highlightthickness=1,
        highlightbackground="#D5DCE5",
    )
    widget.configure(state="disabled")
    return widget


def set_text(widget: tk.Text, content: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", content)
    widget.configure(state="disabled")
