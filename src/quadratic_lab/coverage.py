"""Vérification indépendante de la couverture combinatoire (S-50 à S-52).

Ce module n'utilise PAS Jenny ni ses étiquettes : il reconstruit l'ensemble
théorique des t-uplets à partir de la table du domaine, puis l'ensemble des
t-uplets réellement présents dans les VALEURS numériques des cas.
Il peut ainsi contredire Jenny si celui-ci (ou le décodage) se trompait.
"""

from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .mapping import DEFAULT_DOMAIN, Dimension
from .models import MATH_CATEGORIES, Category, QuadraticCase

#: Un élément de couverture : ((nom, valeur), ...) — ex. (("a", -10), ("b", 0)).
Element = tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class CoverageReport:
    strength: int
    expected: frozenset
    covered: frozenset
    missing: tuple[Element, ...]
    out_of_domain: tuple[tuple[str, Decimal], ...] = ()

    @property
    def total(self) -> int:
        return len(self.expected)

    @property
    def covered_count(self) -> int:
        return len(self.covered)

    @property
    def ratio(self) -> float:
        return self.covered_count / self.total if self.total else 0.0

    @property
    def percent(self) -> float:
        return round(100.0 * self.ratio, 2)

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and not self.missing

    @staticmethod
    def format_element(element: Element) -> str:
        return ", ".join(f"{name}={value}" for name, value in element)

    def by_dimensions(self) -> dict[tuple[str, ...], tuple[int, int]]:
        """Couverture par groupe de dimensions : {("a","b"): (couverts, total)}."""
        result: dict[tuple[str, ...], list[int]] = {}
        for element in self.expected:
            key = tuple(name for name, _ in element)
            counts = result.setdefault(key, [0, 0])
            counts[1] += 1
            if element in self.covered:
                counts[0] += 1
        return {key: (c, t) for key, (c, t) in sorted(result.items())}

    def summary(self) -> str:
        return f"{self.covered_count}/{self.total} ({self.percent:.1f} %)"


def _values(case: QuadraticCase | Sequence[Decimal]) -> tuple[Decimal, ...]:
    if isinstance(case, QuadraticCase):
        return case.coefficients
    return tuple(case)


def _expected(domain: Sequence[Dimension], strength: int) -> list[Element]:
    elements: list[Element] = []
    for dims in itertools.combinations(domain, strength):
        for values in itertools.product(*(dim.values for dim in dims)):
            elements.append(tuple((dim.name, value) for dim, value in zip(dims, values)))
    return elements


def interaction_coverage(
    cases: Iterable[QuadraticCase | Sequence[Decimal]],
    domain: Sequence[Dimension] = DEFAULT_DOMAIN,
    strength: int = 2,
) -> CoverageReport:
    """Couverture t-wise (t = ``strength``) d'un ensemble de cas."""
    if not 1 <= strength <= len(domain):
        raise ValueError(f"La force doit être comprise entre 1 et {len(domain)}.")
    expected_list = _expected(domain, strength)
    expected = frozenset(expected_list)
    covered: set[Element] = set()
    outside: list[tuple[str, Decimal]] = []
    for case in cases:
        values = _values(case)
        if len(values) != len(domain):
            raise ValueError(f"Un cas doit fournir {len(domain)} valeurs, {len(values)} reçues.")
        for dim, value in zip(domain, values):
            if value not in dim.values and (dim.name, value) not in outside:
                outside.append((dim.name, value))
        for positions in itertools.combinations(range(len(domain)), strength):
            element = tuple((domain[i].name, values[i]) for i in positions)
            if element in expected:
                covered.add(element)
    missing = tuple(e for e in expected_list if e not in covered)
    return CoverageReport(strength, expected, frozenset(covered), missing, tuple(outside))


def covering_cases(
    cases: Iterable[QuadraticCase], domain: Sequence[Dimension] = DEFAULT_DOMAIN, strength: int = 2
) -> dict[Element, tuple[str, ...]]:
    """Pour chaque t-uplet attendu, identifiants des cas qui le couvrent."""
    result: dict[Element, list[str]] = {element: [] for element in _expected(domain, strength)}
    for case in cases:
        values = case.coefficients
        for positions in itertools.combinations(range(len(domain)), strength):
            element = tuple((domain[i].name, values[i]) for i in positions)
            if element in result:
                result[element].append(case.case_id)
    return {element: tuple(ids) for element, ids in result.items()}


def uniwise_coverage(cases, domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> CoverageReport:
    return interaction_coverage(cases, domain, 1)


def pairwise_coverage(cases, domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> CoverageReport:
    return interaction_coverage(cases, domain, 2)


def triplewise_coverage(cases, domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> CoverageReport:
    return interaction_coverage(cases, domain, 3)


@dataclass(frozen=True)
class CategoryCoverage:
    """Catégories mathématiques effectivement atteintes par une campagne."""

    counts: dict
    covered: frozenset
    missing: tuple[Category, ...]

    @property
    def total(self) -> int:
        return len(MATH_CATEGORIES)

    @property
    def percent(self) -> float:
        return 100.0 * len(self.covered) / self.total


def category_coverage(categories: Iterable[Category]) -> CategoryCoverage:
    counts = Counter(c for c in categories if c in MATH_CATEGORIES)
    covered = frozenset(counts)
    missing = tuple(c for c in MATH_CATEGORIES if c not in covered)
    return CategoryCoverage(dict(counts), covered, missing)
