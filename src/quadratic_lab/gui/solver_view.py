"""Onglet A — Résolution d'une équation (appelle ``solver.solve`` et l'oracle)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import Category, SolveResult
from ..oracle import REFERENCE_CASES, compare, expected_result
from ..solver import format_complex, format_exact, format_roots, solve
from ..validation import DISPLAY_DIGITS, INTERNAL_PRECISION, InvalidCoefficientError, parse_user_input
from .theme import CATEGORY_COLORS, COLORS, FONT, MONO, make_text, set_text

DELTA_REMINDER = (
    "Rappel : Delta = b² - 4ac\n"
    "• a ≠ 0, Delta > 0 : deux racines réelles distinctes\n"
    "• a ≠ 0, Delta = 0 : une racine double -b/(2a)\n"
    "• a ≠ 0, Delta < 0 : aucune racine réelle\n"
    "• a = 0, b ≠ 0 : premier degré, x = -c/b\n"
    "• a = b = 0 : 0 = 0 (infinité) ou c = 0 impossible"
)


class SolverView(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16)
        self.result: SolveResult | None = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Saisie -------------------------------------------------------
        inputs = ttk.LabelFrame(self, text="Coefficients de a·x² + b·x + c = 0")
        inputs.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.entries: dict[str, ttk.Entry] = {}
        for row, name in enumerate("abc"):
            ttk.Label(inputs, text=f"{name} =", font=(FONT, 12, "bold")).grid(row=row, column=0, sticky="e", pady=6)
            entry = ttk.Entry(inputs, width=26, font=(FONT, 12))
            entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            entry.bind("<Return>", lambda _event: self.solve())
            self.entries[name] = entry
        ttk.Label(
            inputs,
            text="Point ou virgule décimale (ex. 1,5).\nDomaine : |x| ≤ 10¹², au plus 12 décimales.",
            style="Muted.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 8))

        digits_row = ttk.Frame(inputs)
        digits_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(digits_row, text="Chiffres affichés :").pack(side="left")
        self.digits_var = tk.IntVar(value=DISPLAY_DIGITS)
        ttk.Spinbox(digits_row, from_=1, to=INTERNAL_PRECISION, textvariable=self.digits_var, width=5).pack(
            side="left", padx=6
        )

        buttons = ttk.Frame(inputs)
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        self.solve_button = ttk.Button(buttons, text="Résoudre", style="Accent.TButton", command=self.solve)
        self.solve_button.pack(side="left")
        self.clear_button = ttk.Button(buttons, text="Effacer", command=self.clear)
        self.clear_button.pack(side="left", padx=8)

        ttk.Label(inputs, text="Exemples (cas ciblés calculés à la main) :").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(14, 2)
        )
        self.example_var = tk.StringVar()
        self.examples = ttk.Combobox(
            inputs,
            textvariable=self.example_var,
            state="readonly",
            width=46,
            values=[f"{ref.case_id} — {ref.description}" for ref in REFERENCE_CASES],
        )
        self.examples.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.examples.bind("<<ComboboxSelected>>", self._load_example)

        reminder = ttk.Label(inputs, text=DELTA_REMINDER, justify="left", style="Muted.TLabel")
        reminder.grid(row=8, column=0, columnspan=2, sticky="w", pady=(16, 0))

        # --- Résultat -----------------------------------------------------
        results = ttk.LabelFrame(self, text="Résultat")
        results.grid(row=0, column=1, sticky="nsew")
        results.columnconfigure(0, weight=1)
        self.equation_var = tk.StringVar(value="Saisissez a, b, c puis cliquez sur « Résoudre ».")
        self.category_var = tk.StringVar()
        self.delta_var = tk.StringVar()
        self.solutions_var = tk.StringVar()
        self.oracle_var = tk.StringVar()
        ttk.Label(results, textvariable=self.equation_var, font=(FONT, 12)).grid(row=0, column=0, sticky="w")
        self.category_label = tk.Label(
            results, textvariable=self.category_var, font=(FONT, 14, "bold"), anchor="w",
            background=COLORS["bg"], foreground=COLORS["primary"],
        )
        self.category_label.grid(row=1, column=0, sticky="ew", pady=(10, 4))
        ttk.Label(results, textvariable=self.delta_var, font=(FONT, 12)).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(results, textvariable=self.solutions_var, font=(MONO, 13), justify="left").grid(
            row=3, column=0, sticky="w", pady=8
        )
        ttk.Label(results, text="Explication du cas mathématique", style="Big.TLabel").grid(
            row=4, column=0, sticky="w", pady=(8, 2)
        )
        self.explanation_text = make_text(results, height=4)
        self.explanation_text.grid(row=5, column=0, sticky="nsew")
        ttk.Label(results, text="Vérification par l'oracle indépendant", style="Big.TLabel").grid(
            row=6, column=0, sticky="w", pady=(12, 2)
        )
        ttk.Label(results, textvariable=self.oracle_var, wraplength=620, justify="left").grid(
            row=7, column=0, sticky="w"
        )
        results.rowconfigure(8, weight=1)

    # ------------------------------------------------------------------
    def set_coefficients(self, a: str, b: str, c: str) -> None:
        for name, value in zip("abc", (a, b, c)):
            entry = self.entries[name]
            entry.delete(0, "end")
            entry.insert(0, str(value))

    def clear(self) -> None:
        self.set_coefficients("", "", "")
        for var in (self.category_var, self.delta_var, self.solutions_var, self.oracle_var):
            var.set("")
        set_text(self.explanation_text, "")

    def _load_example(self, _event=None) -> None:
        index = self.examples.current()
        if index >= 0:
            ref = REFERENCE_CASES[index]
            self.set_coefficients(ref.a, ref.b, ref.c)
            self.solve()

    def _digits(self) -> int:
        try:
            return min(max(int(self.digits_var.get()), 1), INTERNAL_PRECISION)
        except (tk.TclError, ValueError):
            return DISPLAY_DIGITS

    def solve(self) -> SolveResult | None:
        texts = [self.entries[name].get() for name in "abc"]
        self.equation_var.set(f"Équation : ({texts[0]})·x² + ({texts[1]})·x + ({texts[2]}) = 0")
        try:
            a, b, c = (parse_user_input(text, name) for name, text in zip("abc", texts))
        except InvalidCoefficientError as exc:
            self._show_invalid(str(exc))
            return None
        result = solve(a, b, c)
        self.result = result
        if not result.is_valid:  # pragma: no cover - déjà filtré par parse_user_input
            self._show_invalid(result.error or "")
            return result
        self.equation_var.set(
            f"Équation : {format_exact(a)}·x² + ({format_exact(b)})·x + ({format_exact(c)}) = 0"
        )
        self.category_var.set(f"{result.category.label} ({result.category.value})")
        self.category_label.configure(foreground=CATEGORY_COLORS[result.category])
        if result.discriminant is None:
            self.delta_var.set("Delta : non défini (a = 0, l'équation n'est pas du second degré)")
        else:
            self.delta_var.set(f"Delta = {format_exact(result.discriminant)}")
        self.solutions_var.set(self._solutions_text(result))
        set_text(self.explanation_text, result.explanation())
        verdict = compare(expected_result(a, b, c), result)
        self.oracle_var.set(verdict.summary())
        return result

    def _solutions_text(self, result: SolveResult) -> str:
        digits = self._digits()
        roots = format_roots(result.roots, digits)
        cat = result.category
        if cat is Category.TWO_REAL_ROOTS:
            return f"x1 = {roots[0]}\nx2 = {roots[1]}"
        if cat is Category.DOUBLE_REAL_ROOT:
            return f"x = {roots[0]}   (racine double)"
        if cat is Category.LINEAR_ROOT:
            return f"x = {roots[0]}"
        if cat is Category.NO_REAL_ROOT:
            z1, z2 = (format_complex(re, im, digits) for re, im in result.complex_roots)
            return f"Aucune racine réelle.\n(Extension dans ℂ : z1 = {z1}, z2 = {z2})"
        if cat is Category.INFINITE_SOLUTIONS:
            return "Tout réel x est solution."
        return "Aucune solution."

    def _show_invalid(self, message: str) -> None:
        self.result = None
        self.category_var.set(f"{Category.INVALID_INPUT.label} ({Category.INVALID_INPUT.value})")
        self.category_label.configure(foreground=CATEGORY_COLORS[Category.INVALID_INPUT])
        self.delta_var.set("")
        self.solutions_var.set("Aucun calcul effectué.")
        self.oracle_var.set("")
        set_text(self.explanation_text, message)
