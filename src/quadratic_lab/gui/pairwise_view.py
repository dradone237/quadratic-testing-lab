"""Onglet C — Tests Pairwise (jenny -n2) et vérification des 75 paires."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..combinatorial import Method
from ..coverage import covering_cases, triplewise_coverage
from .campaign_view import CampaignView
from .theme import FONT, make_table


class PairwiseView(CampaignView):
    method = Method.PAIRWISE
    intro = (
        "Pairwise (couverture 2-way) : chaque paire de valeurs issues de deux coefficients différents apparaît "
        "au moins une fois. Paires (a,b), (a,c), (b,c) : 3 × 25 = 75 paires à couvrir. Attention : cela ne "
        "signifie pas que les 125 triplets ont été testés."
    )

    def _build_extra(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Vérification des 75 paires", font=(FONT, 10, "bold")).pack(anchor="w")
        frame, self.pairs_table = make_table(
            parent,
            [("dims", "Paire", 60), ("values", "Valeurs", 120), ("cases", "Couverte par", 150)],
            height=9,
        )
        frame.pack(fill="both", expand=True, pady=(2, 4))
        self.triples_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.triples_var, wraplength=380, justify="left").pack(anchor="w")

    def _refresh_extra(self) -> None:
        self.pairs_table.delete(*self.pairs_table.get_children())
        mapping = covering_cases(self.suite.cases, strength=2)
        for element, ids in mapping.items():
            dims = "(" + ",".join(name for name, _ in element) + ")"
            values = ", ".join(f"{name}={value}" for name, value in element)
            self.pairs_table.insert(
                "", "end", values=(dims, values, ", ".join(ids) or "MANQUANTE"), tags=("pass" if ids else "fail",)
            )
        triples = triplewise_coverage(self.suite.cases)
        self.triples_var.set(
            f"Triplets (3-way) couverts : {triples.summary()}. Pairwise ne teste pas toutes les "
            "combinaisons de trois valeurs : un défaut qui n'apparaît que pour un triplet précis peut échapper."
        )
