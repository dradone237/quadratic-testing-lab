"""Fenêtre principale « QUADRATIC TESTING LAB » et mode Démonstration.

L'interface appelle les mêmes modules métier que la CLI (solver, oracle,
combinatorial, runner, reporting) et le véritable Jenny : aucun algorithme
n'est recopié dans les widgets.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk

from ..jenny_adapter import JennyAdapter, JennyError
from .comparison_view import ComparisonView
from .pairwise_view import PairwiseView
from .solver_view import SolverView
from .theme import FONT, apply_theme
from .uniwise_view import UniwiseView

TITLE = "QUADRATIC TESTING LAB"


@dataclass(frozen=True)
class DemoStep:
    title: str
    narration: str
    action: Callable[[], None]


class DemoController:
    """Présente successivement les 8 étapes de la démonstration."""

    def __init__(self, app: QuadraticLabApp) -> None:
        self.app = app
        self.index = 0
        solver = app.solver_view

        def equation(a: str, b: str, c: str) -> Callable[[], None]:
            def run() -> None:
                app.notebook.select(0)
                solver.set_coefficients(a, b, c)
                solver.solve()

            return run

        def campaign(view, tab: int) -> Callable[[], None]:
            def run() -> None:
                app.notebook.select(tab)
                view.generate()
                view.execute()

            return run

        def comparison() -> None:
            app.notebook.select(3)
            app.comparison_view.run()

        self.steps = [
            DemoStep("Équation simple : x² - 3x + 2 = 0", "Factorisation (x - 1)(x - 2) : racines 1 et 2, vérifiées par l'oracle.", equation("1", "-3", "2")),
            DemoStep("Delta positif : x² - x - 1 = 0", "Delta = 5 > 0 : deux racines irrationnelles (nombre d'or), précision 50 chiffres.", equation("1", "-1", "-1")),
            DemoStep("Delta nul : x² + 2x + 1 = 0", "Delta = 0 exactement : une racine double -b/(2a) = -1.", equation("1", "2", "1")),
            DemoStep("Delta négatif : x² + 2x + 5 = 0", "Delta = -16 < 0 : aucune racine réelle (racines complexes -1 ± 2i à titre informatif).", equation("1", "2", "5")),
            DemoStep("Cas a = 0 : 2x - 4 = 0", "a = 0 : ce n'est plus une équation du second degré mais du premier degré, x = 2.", equation("0", "2", "-4")),
            DemoStep("Génération Uniwise (jenny -n1)", "Jenny produit 5 cas : chaque valeur apparaît au moins une fois, couverture 1-way vérifiée.", campaign(app.uniwise_view, 1)),
            DemoStep("Génération Pairwise (jenny -n2)", "Jenny produit les cas couvrant les 75 paires ; vérification indépendante de chaque paire.", campaign(app.pairwise_view, 2)),
            DemoStep("Comparaison des stratégies", "Nombre de cas, couvertures, durées et mutants détectés : Pairwise ne remplace pas les cas ciblés.", comparison),
        ]

    def has_next(self) -> bool:
        return self.index < len(self.steps)

    def next_step(self) -> str:
        if not self.has_next():
            return ""
        step = self.steps[self.index]
        self.index += 1
        step.action()
        self.app.demo_var.set(f"Étape {self.index}/{len(self.steps)} — {step.title}")
        self.app.narration_var.set(step.narration)
        return step.title

    def reset(self) -> None:
        self.index = 0
        self.app.demo_var.set("Démonstration prête : cliquez sur « Étape suivante ».")
        self.app.narration_var.set("")


class QuadraticLabApp:
    def __init__(self, root: tk.Tk, adapter: JennyAdapter | None = None) -> None:
        self.root = root
        root.title(TITLE)
        # Taille adaptée à l'écran (vidéoprojecteur 1366×768 ou 1024×768 compris).
        width = min(1280, root.winfo_screenwidth() - 40)
        height = min(820, root.winfo_screenheight() - 80)
        root.geometry(f"{width}x{height}+20+20")
        root.minsize(min(1000, width), min(640, height))
        apply_theme(root)

        jenny_text = "Jenny : indisponible (voir docs/GUIDE_JENNY.md)"
        if adapter is None:
            try:
                adapter = JennyAdapter()
                adapter.verify()
            except JennyError:
                adapter = None
        if adapter is not None:
            jenny_text = f"Jenny : opérationnel — {adapter.executable}"
        self.adapter = adapter

        header = ttk.Frame(root, style="Header.TFrame", padding=(18, 12))
        header.pack(fill="x")
        ttk.Label(header, text=TITLE, style="Header.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="Résolution et vérification robuste des équations du second degré — Jenny, Uniwise, Pairwise",
            style="SubHeader.TLabel",
        ).pack(side="left", padx=16)
        self.jenny_var = tk.StringVar(value=jenny_text)

        demo_bar = ttk.Frame(root, padding=(18, 8))
        demo_bar.pack(fill="x")
        ttk.Label(demo_bar, text="Mode Démonstration :", font=(FONT, 10, "bold")).pack(side="left")
        self.next_button = ttk.Button(demo_bar, text="Étape suivante ▶", style="Accent.TButton", command=self._next)
        self.next_button.pack(side="left", padx=8)
        self.reset_button = ttk.Button(demo_bar, text="Recommencer", command=self._reset)
        self.reset_button.pack(side="left")
        self.demo_var = tk.StringVar(value="Démonstration prête : cliquez sur « Étape suivante ».")
        ttk.Label(demo_bar, textvariable=self.demo_var, font=(FONT, 10, "bold")).pack(side="left", padx=16)
        ttk.Label(demo_bar, textvariable=self.jenny_var, style="Muted.TLabel").pack(side="right")

        self.narration_var = tk.StringVar()
        ttk.Label(root, textvariable=self.narration_var, padding=(18, 0), style="Muted.TLabel").pack(fill="x")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        self.solver_view = SolverView(self.notebook)
        self.uniwise_view = UniwiseView(self.notebook, adapter)
        self.pairwise_view = PairwiseView(self.notebook, adapter)
        self.comparison_view = ComparisonView(self.notebook, adapter)
        self.notebook.add(self.solver_view, text="A. Résolution")
        self.notebook.add(self.uniwise_view, text="B. Tests Uniwise")
        self.notebook.add(self.pairwise_view, text="C. Tests Pairwise")
        self.notebook.add(self.comparison_view, text="D. Comparaison")

        self.demo = DemoController(self)

    def set_adapter(self, adapter: JennyAdapter | None) -> None:
        self.adapter = adapter
        for view in (self.uniwise_view, self.pairwise_view, self.comparison_view):
            view.adapter = adapter

    def _next(self) -> None:
        if not self.demo.has_next():
            self.demo_var.set("Démonstration terminée. Cliquez sur « Recommencer » pour la rejouer.")
            return
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            self.demo.next_step()
        finally:
            self.root.configure(cursor="")

    def _reset(self) -> None:
        self.demo.reset()
        self.notebook.select(0)


def _enable_dpi_awareness() -> None:  # pragma: no cover - spécifique Windows
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main() -> None:  # pragma: no cover - boucle interactive
    _enable_dpi_awareness()
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Interface graphique indisponible ({exc}). Utilisez la CLI : python -m quadratic_lab --help")
        raise SystemExit(2) from exc
    QuadraticLabApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
