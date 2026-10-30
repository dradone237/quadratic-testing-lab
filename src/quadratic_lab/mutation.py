"""Analyse de mutation : évaluer scientifiquement les stratégies de test.

Un *mutant* est une copie du solveur dans laquelle on a injecté un défaut
réaliste. Une stratégie « tue » un mutant si au moins un de ses cas le fait
échouer face à l'oracle (ou planter). Le score de mutation mesure ainsi la
capacité de détection d'un jeu de tests, et pas seulement sa couverture.

Ces mutants servent uniquement à évaluer les tests : le solveur réel
(``solver.py``) n'est jamais modifié.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, localcontext

from .combinatorial import GeneratedSuite, Method
from .models import Category, SolveResult
from .oracle import compare, expected_result
from .solver import WORK_CONTEXT
from .validation import InvalidCoefficientError, validate_coefficients


@dataclass(frozen=True)
class Mutant:
    mutant_id: str
    title: str
    description: str
    trigger: str
    solve: Callable[[object, object, object], SolveResult]


def _canonical(value: Decimal) -> Decimal:
    return Decimal(0) if value.is_zero() else value


def _faulty_solve(a: Decimal, b: Decimal, c: Decimal, fault: str) -> SolveResult:
    """Solveur « de référence » simplifié dans lequel ``fault`` active un défaut."""
    if a.is_zero() and fault != "M03":
        if b.is_zero() and fault != "M04":
            if c.is_zero():
                category = Category.NO_SOLUTION if fault == "M05" else Category.INFINITE_SOLUTIONS
                return SolveResult(category, a, b, c)
            return SolveResult(Category.NO_SOLUTION, a, b, c)
        root = c / b if fault == "M08" else -c / b
        return SolveResult(Category.LINEAR_ROOT, a, b, c, roots=(_canonical(root),))

    delta = b * b + 4 * a * c if fault == "M01" else b * b - 4 * a * c
    radicand = delta
    if delta < 0:
        if fault != "M09":
            return SolveResult(Category.NO_REAL_ROOT, a, b, c, discriminant=delta)
        radicand = -delta  # défaut : √|Δ| fabrique de fausses racines réelles
    elif delta == 0:
        if fault == "M02":
            return SolveResult(Category.NO_REAL_ROOT, a, b, c, discriminant=delta)
        root = -b / a if fault == "M06" else -b / (2 * a)
        return SolveResult(Category.DOUBLE_REAL_ROOT, a, b, c, discriminant=delta, roots=(_canonical(root),))

    if fault == "M07":
        fa, fb = float(a), float(b)
        s = math.sqrt(float(radicand))
        x1, x2 = Decimal(repr((-fb - s) / (2 * fa))), Decimal(repr((-fb + s) / (2 * fa)))
    else:
        sign = 0 if (fault == "M10" and b.is_zero()) else (1 if b >= 0 else -1)
        q = -(b + sign * radicand.sqrt()) / 2
        x1, x2 = q / a, c / q
    roots = tuple(sorted((_canonical(x1), _canonical(x2))))
    return SolveResult(Category.TWO_REAL_ROOTS, a, b, c, discriminant=delta, roots=roots)


def _make(fault: str) -> Callable[[object, object, object], SolveResult]:
    def solve_mutant(a: object, b: object, c: object) -> SolveResult:
        try:
            a_dec, b_dec, c_dec = validate_coefficients(a, b, c)
        except InvalidCoefficientError as exc:
            return SolveResult(Category.INVALID_INPUT, None, None, None, error=str(exc))
        with localcontext(WORK_CONTEXT):
            return _faulty_solve(a_dec, b_dec, c_dec, fault)

    solve_mutant.__name__ = f"solve_{fault}"
    return solve_mutant


_CATALOGUE = [
    ("M01", "Signe du discriminant inversé", "Δ = b² + 4ac au lieu de b² - 4ac.", "a ≠ 0 et c ≠ 0 (paire a × c)"),
    ("M02", "Delta nul traité comme négatif", "Test « Δ ≤ 0 » au lieu de « Δ < 0 ».", "Δ = 0 : b² = 4ac"),
    ("M03", "Cas a = 0 non traité", "Pas de branche a = 0 : division par zéro.", "a = 0 (valeur seule, 1-way)"),
    (
        "M04",
        "a = 0 et b = 0 non distingués",
        "0·x + c traité comme une équation linéaire : division par zéro.",
        "paire (a = 0, b = 0) (2-way)",
    ),
    ("M05", "0 = 0 déclaré sans solution", "INFINITE_SOLUTIONS remplacé par NO_SOLUTION.", "triplet (0, 0, 0) (3-way)"),
    ("M06", "Racine double -b/a", "Facteur 2 oublié : -b/a au lieu de -b/(2a).", "Δ = 0 avec b ≠ 0 (triplet précis)"),
    (
        "M07",
        "Formule scolaire en double précision",
        "Calcul en float (≈ 16 chiffres) avec la formule (-b ± √Δ)/(2a).",
        "racine non représentable exactement en binaire",
    ),
    ("M08", "Signe de la solution linéaire", "x = c/b au lieu de x = -c/b.", "a = 0, b ≠ 0, c ≠ 0"),
    ("M09", "Delta négatif ignoré", "√|Δ| utilisé : fausses racines réelles.", "Δ < 0"),
    (
        "M10",
        "Formule stable avec signe(0) = 0",
        "q = -(b + signe(b)·√Δ)/2 avec signe(0) = 0 : q = 0 puis division par zéro.",
        "b = 0 et a·c < 0 (triplet : signes de a et c opposés)",
    ),
]

MUTANTS: tuple[Mutant, ...] = tuple(Mutant(mid, title, desc, trig, _make(mid)) for mid, title, desc, trig in _CATALOGUE)


@dataclass(frozen=True)
class MutantDetail:
    mutant_id: str
    method: Method
    killed: bool
    killing_cases: tuple[str, ...]


@dataclass(frozen=True)
class MutationReport:
    mutants: tuple[Mutant, ...]
    methods: tuple[Method, ...]
    details: Mapping[tuple[Method, str], MutantDetail]

    def detail(self, method: Method, mutant_id: str) -> MutantDetail:
        return self.details[(method, mutant_id)]

    def killed(self, method: Method) -> set[str]:
        return {m.mutant_id for m in self.mutants if self.details[(method, m.mutant_id)].killed}

    def score(self, method: Method) -> float:
        return 100.0 * len(self.killed(method)) / len(self.mutants)


def run_mutation_analysis(
    suites: Mapping[Method, GeneratedSuite], mutants: tuple[Mutant, ...] = MUTANTS
) -> MutationReport:
    """Exécute chaque mutant sur chaque jeu de cas et note les cas qui le tuent."""
    details: dict[tuple[Method, str], MutantDetail] = {}
    for method, suite in suites.items():
        expectations = [(case, expected_result(case.a, case.b, case.c)) for case in suite.cases]
        for mutant in mutants:
            killers = []
            for case, expected in expectations:
                try:
                    verdict = compare(expected, mutant.solve(case.a, case.b, case.c))
                except Exception:  # noqa: BLE001 - un plantage du mutant est une détection
                    killers.append(case.case_id)
                    continue
                if not verdict.passed:
                    killers.append(case.case_id)
            details[(method, mutant.mutant_id)] = MutantDetail(mutant.mutant_id, method, bool(killers), tuple(killers))
    return MutationReport(mutants, tuple(suites), details)
