"""Onglet B — Tests Uniwise (jenny -n1)."""

from __future__ import annotations

from tkinter import ttk

from ..combinatorial import Method
from ..coverage import covering_cases
from ..mapping import DEFAULT_DOMAIN
from .campaign_view import CampaignView
from .theme import FONT, make_table


class UniwiseView(CampaignView):
    method = Method.UNIWISE
    intro = (
        "Uniwise (couverture 1-way) : chaque valeur de chaque coefficient apparaît au moins une fois. "
        "Avec 5 valeurs par coefficient, 5 cas suffisent au minimum. Jenny est exécuté réellement "
        "(jenny -n1 5 5 5) ; la couverture est ensuite recalculée indépendamment à partir des valeurs décodées."
    )

    def _build_extra(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Valeurs couvertes (15 attendues)", font=(FONT, 10, "bold")).pack(anchor="w")
        frame, self.values_table = make_table(
            parent,
            [("label", "Étiquette", 70), ("coef", "Coefficient", 80), ("value", "Valeur", 60), ("cases", "Couverte par", 160)],
            height=8,
        )
        frame.pack(fill="both", expand=True, pady=(2, 0))

    def _refresh_extra(self) -> None:
        self.values_table.delete(*self.values_table.get_children())
        mapping = covering_cases(self.suite.cases, strength=1)
        for dim in DEFAULT_DOMAIN:
            for letter, value in zip(dim.labels, dim.values):
                ids = mapping[((dim.name, value),)]
                self.values_table.insert(
                    "",
                    "end",
                    values=(f"{dim.index}{letter}", dim.name, str(value), ", ".join(ids) or "MANQUANTE"),
                    tags=("pass" if ids else "fail",),
                )
