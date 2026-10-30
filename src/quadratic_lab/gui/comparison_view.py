"""Onglet D — Comparaison des stratégies (mesures réelles + analyse de mutation)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..combinatorial import Method
from ..jenny_adapter import JennyAdapter
from ..reporting import REPORTS_DIR, export_comparison
from ..runner import COMPARISON_ORDER, ComparisonResult, compare_strategies
from .theme import FONT, make_table, make_text, set_text

COLUMNS = [
    ("method", "Méthode", 130),
    ("cases", "Cas", 50),
    ("ratio", "% exhaustif", 80),
    ("gen", "Génération (ms)", 100),
    ("exec", "Exécution (ms)", 100),
    ("c1", "1-way", 110),
    ("c2", "2-way", 110),
    ("c3", "3-way", 120),
    ("cat", "Catégories", 80),
    ("ok", "Réussis", 65),
    ("ko", "Échecs", 60),
    ("missing", "Non couverts (paires / triplets)", 190),
    ("mut", "Score mutation", 100),
]


class ComparisonView(ttk.Frame):
    def __init__(self, master: tk.Misc, adapter: JennyAdapter | None = None) -> None:
        super().__init__(master, padding=12)
        self.adapter = adapter
        self.comparison: ComparisonResult | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(4, weight=2)

        ttk.Label(
            self,
            text="Comparaison mesurée des stratégies : nombre de cas, durée, couvertures 1/2/3-way, catégories "
            "mathématiques atteintes, résultats et score de mutation (défauts injectés détectés).",
            wraplength=1100,
        ).grid(row=0, column=0, sticky="w")
        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", pady=8)
        self.run_button = ttk.Button(controls, text="Lancer la comparaison", style="Accent.TButton", command=self.run)
        self.run_button.pack(side="left")
        self.export_button = ttk.Button(controls, text="Exporter les rapports", command=self.export)
        self.export_button.pack(side="left", padx=8)
        self.status_var = tk.StringVar(value="Cliquez sur « Lancer la comparaison ».")
        ttk.Label(controls, textvariable=self.status_var, style="Muted.TLabel").pack(side="left", padx=12)

        frame, self.table = make_table(self, COLUMNS, height=5)
        frame.grid(row=2, column=0, sticky="nsew")

        ttk.Label(self, text="Analyse de mutation (tué = défaut détecté par au moins un cas)", font=(FONT, 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(10, 2)
        )
        mutation_columns = [("id", "Mutant", 60), ("title", "Défaut injecté", 260), ("trigger", "Déclencheur", 300)] + [
            (m.value, m.label, 110) for m in COMPARISON_ORDER
        ]
        frame, self.mutation_table = make_table(self, mutation_columns, height=10)
        frame.grid(row=4, column=0, sticky="nsew")

        ttk.Label(self, text="Conclusions (calculées à partir des mesures)", font=(FONT, 10, "bold")).grid(
            row=5, column=0, sticky="w", pady=(10, 2)
        )
        self.conclusions = make_text(self, height=5)
        self.conclusions.grid(row=6, column=0, sticky="ew")

    def run(self) -> None:
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            self.comparison = compare_strategies(adapter=self.adapter)
        finally:
            self.configure(cursor="")
        self._fill()

    def _fill(self) -> None:
        comparison = self.comparison
        exhaustive = 125
        self.table.delete(*self.table.get_children())
        for method in COMPARISON_ORDER:
            campaign = comparison.campaigns.get(method)
            if campaign is None:
                self.table.insert("", "end", values=(method.label, "indisponible", *[""] * 11), tags=("fail",))
                continue
            score = f"{comparison.mutation.score(method):.0f} %" if comparison.mutation else "-"
            self.table.insert(
                "",
                "end",
                values=(
                    method.label,
                    campaign.total,
                    f"{100 * campaign.total / exhaustive:.1f} %",
                    f"{campaign.suite.duration_s * 1000:.1f}",
                    f"{campaign.duration_s * 1000:.1f}",
                    campaign.coverage[1].summary(),
                    campaign.coverage[2].summary(),
                    campaign.coverage[3].summary(),
                    f"{len(campaign.categories.covered)}/6",
                    campaign.passed,
                    campaign.failed + campaign.errors,
                    f"{len(campaign.coverage[2].missing)} / {len(campaign.coverage[3].missing)}",
                    score,
                ),
                tags=("pass" if campaign.all_passed else "fail",),
            )
        self.mutation_table.delete(*self.mutation_table.get_children())
        mutation = comparison.mutation
        if mutation is not None:
            for mutant in mutation.mutants:
                cells = []
                for method in COMPARISON_ORDER:
                    if method in mutation.methods:
                        cells.append("tué" if mutation.detail(method, mutant.mutant_id).killed else "SURVIT")
                    else:
                        cells.append("-")
                self.mutation_table.insert("", "end", values=(mutant.mutant_id, mutant.title, mutant.trigger, *cells))
        set_text(self.conclusions, self._conclusions())
        unavailable = ", ".join(m.label for m in comparison.unavailable)
        self.status_var.set(
            "Comparaison terminée." + (f" Jenny indisponible pour : {unavailable}." if unavailable else "")
        )

    def _conclusions(self) -> str:
        comparison = self.comparison
        lines = []
        exhaustive = comparison.campaigns.get(Method.EXHAUSTIVE)
        for method in (Method.UNIWISE, Method.PAIRWISE):
            campaign = comparison.campaigns.get(method)
            if campaign is None or exhaustive is None:
                continue
            survivors = []
            if comparison.mutation is not None:
                survivors = sorted({m.mutant_id for m in comparison.mutation.mutants} - comparison.mutation.killed(method))
            missing = ", ".join(c.value for c in campaign.categories.missing) or "aucune"
            lines.append(
                f"• {method.label} : {campaign.total} cas ({100 * campaign.total / exhaustive.total:.1f} % de "
                f"l'exhaustif), 2-way {campaign.coverage[2].percent:.1f} %, catégories non atteintes : {missing}, "
                f"mutants survivants : {', '.join(survivors) or 'aucun'}."
            )
        lines.append(
            "• Pairwise couvre 100 % des paires mais pas tous les triplets : les défauts qui dépendent de trois "
            "valeurs à la fois (ex. 0 = 0) peuvent lui échapper. Les cas ciblés complètent la stratégie."
        )
        lines.append("• Aucune stratégie ne prouve l'absence de défauts ; moins de tests ne signifie pas meilleure méthode.")
        return "\n".join(lines)

    def export(self) -> None:
        if self.comparison is None:
            self.status_var.set("Lancez d'abord la comparaison.")
            return
        paths = export_comparison(self.comparison, REPORTS_DIR)
        self.status_var.set(f"{len(paths)} fichiers écrits dans {REPORTS_DIR}")
