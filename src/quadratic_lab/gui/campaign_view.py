"""Base commune des onglets Uniwise et Pairwise : Jenny -> cas -> exécution."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..combinatorial import GeneratedSuite, Method, generate
from ..coverage import CoverageReport, interaction_coverage
from ..jenny_adapter import JennyAdapter, JennyError
from ..models import Status
from ..reporting import delta_text
from ..runner import CampaignResult, run_suite
from ..solver import format_exact, format_roots
from .theme import FONT, make_table, make_text, set_text

CASE_COLUMNS = [
    ("id", "ID", 72),
    ("jenny", "Combinaison Jenny", 110),
    ("a", "a", 42),
    ("b", "b", 42),
    ("c", "c", 42),
    ("delta", "Delta", 52),
    ("expected", "Attendu (oracle)", 128),
    ("actual", "Obtenu (solveur)", 128),
    ("roots", "Racines", 200),
    ("status", "Statut", 82),
]


class CampaignView(ttk.Frame):
    method: Method = Method.UNIWISE
    intro: str = ""

    def __init__(self, master: tk.Misc, adapter: JennyAdapter | None = None) -> None:
        super().__init__(master, padding=12)
        self.adapter = adapter
        self.suite: GeneratedSuite | None = None
        self.campaign: CampaignResult | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(self, text=self.intro, wraplength=1100, justify="left").grid(row=0, column=0, sticky="w")

        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", pady=8)
        self.generate_button = ttk.Button(controls, text="Générer avec Jenny", style="Accent.TButton", command=self.generate)
        self.generate_button.pack(side="left")
        self.execute_button = ttk.Button(controls, text="Exécuter les tests", command=self.execute)
        self.execute_button.pack(side="left", padx=8)
        self.command_var = tk.StringVar(value=f"Commande prévue : jenny -n{self.method.strength} 5 5 5")
        ttk.Label(controls, textvariable=self.command_var, style="Mono.TLabel").pack(side="left", padx=12)

        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew")
        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Sortie brute de Jenny (non modifiée)", font=(FONT, 10, "bold")).pack(anchor="w")
        self.raw_text = make_text(left, height=10, mono=True)
        self.raw_text.configure(width=34)
        self.raw_text.pack(fill="both", expand=False, pady=(2, 8))
        self.extra = ttk.Frame(left)
        self.extra.pack(fill="both", expand=True)
        self._build_extra(self.extra)

        ttk.Label(right, text="Cas de test : coefficients décodés, attendu et obtenu", font=(FONT, 10, "bold")).pack(
            anchor="w"
        )
        table_frame, self.cases_table = make_table(right, CASE_COLUMNS, height=14)
        table_frame.pack(fill="both", expand=True, pady=(2, 0))

        summary = ttk.Frame(self)
        summary.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.coverage_var = tk.StringVar()
        self.results_var = tk.StringVar()
        self.categories_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Cliquez sur « Générer avec Jenny ».")
        ttk.Label(summary, textvariable=self.coverage_var, font=(FONT, 11, "bold")).pack(anchor="w")
        ttk.Label(summary, textvariable=self.results_var).pack(anchor="w")
        ttk.Label(summary, textvariable=self.categories_var).pack(anchor="w")
        ttk.Label(summary, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w")

    # -- points d'extension ------------------------------------------------
    def _build_extra(self, parent: ttk.Frame) -> None:
        """Widgets propres à la méthode (sous la sortie brute)."""

    def _refresh_extra(self) -> None:
        """Mise à jour des widgets propres à la méthode après génération."""

    def coverage_report(self) -> CoverageReport | None:
        if self.suite is None:
            return None
        return interaction_coverage(self.suite.cases, strength=self.method.strength)

    # -- actions -----------------------------------------------------------
    def generate(self) -> None:
        try:
            adapter = self.adapter or JennyAdapter()
            suite = generate(self.method, adapter=adapter)
        except JennyError as exc:
            self.suite = None
            self.campaign = None
            self.status_var.set(f"Jenny indisponible : génération impossible (aucune simulation). {exc}")
            return
        self.adapter = adapter
        self.suite = suite
        self.campaign = None
        self.command_var.set(
            f"Commande exécutée : {suite.command}  —  {len(suite.cases)} combinaisons en {suite.duration_s * 1000:.1f} ms"
        )
        set_text(self.raw_text, suite.raw_output or "")
        self.cases_table.delete(*self.cases_table.get_children())
        for case in suite.cases:
            self.cases_table.insert(
                "",
                "end",
                iid=case.case_id,
                values=(case.case_id, case.jenny_combination, format_exact(case.a), format_exact(case.b),
                        format_exact(case.c), "", "", "", "", Status.NOT_RUN.label),
                tags=("pending",),
            )
        self._show_coverage()
        self.results_var.set("")
        self.categories_var.set("")
        self.status_var.set("Cas générés par Jenny et décodés. Cliquez sur « Exécuter les tests ».")
        self._refresh_extra()

    def execute(self) -> None:
        if self.suite is None:
            self.status_var.set("Veuillez d'abord générer les cas avec Jenny (bouton « Générer avec Jenny »).")
            return
        campaign = run_suite(self.suite)
        self.campaign = campaign
        for outcome in campaign.outcomes:
            case = outcome.case
            expected = outcome.expected
            delta = delta_text(expected)
            actual = outcome.actual
            self.cases_table.item(
                case.case_id,
                values=(
                    case.case_id,
                    case.jenny_combination,
                    format_exact(case.a),
                    format_exact(case.b),
                    format_exact(case.c),
                    delta,
                    expected.category.value,
                    actual.category.value if actual else "plantage",
                    " | ".join(format_roots(actual.roots)) if actual else outcome.error,
                    outcome.status.label,
                ),
                tags=("pass" if outcome.status is Status.PASS else "fail",),
            )
        self._show_coverage()
        self.results_var.set(
            f"Résultats : {campaign.passed} réussis, {campaign.failed} échecs, {campaign.errors} erreurs "
            f"sur {campaign.total} cas ({campaign.duration_s * 1000:.1f} ms)"
        )
        missing = ", ".join(c.value for c in campaign.categories.missing) or "aucune"
        self.categories_var.set(
            f"Catégories mathématiques atteintes : {len(campaign.categories.covered)}/{campaign.categories.total}"
            f" — non atteintes : {missing}"
        )
        if campaign.all_passed:
            self.status_var.set("Exécution terminée : tous les cas sont conformes à l'oracle indépendant.")
        else:
            self.status_var.set("Exécution terminée : des écarts ont été détectés (lignes en rouge).")

    def _show_coverage(self) -> None:
        report = self.coverage_report()
        if report is None:
            return
        verdict = "COMPLÈTE" if report.is_complete else f"{len(report.missing)} élément(s) manquant(s)"
        self.coverage_var.set(f"Couverture {self.method.strength}-way : {report.summary()} — {verdict}")
