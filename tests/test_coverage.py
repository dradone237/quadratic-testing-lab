"""Tests du vérificateur de couverture combinatoire (S-50 à S-52).

Le vérificateur est indépendant de Jenny : il travaille sur les VALEURS
numériques des cas et la table du domaine. On le teste ici sur des jeux de
cas construits à la main, dont la couverture est connue analytiquement.
"""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from quadratic_lab.coverage import (
    category_coverage,
    covering_cases,
    interaction_coverage,
    pairwise_coverage,
    triplewise_coverage,
    uniwise_coverage,
)
from quadratic_lab.mapping import DEFAULT_DOMAIN
from quadratic_lab.models import Category, QuadraticCase

D = Decimal
VALUES = [dim.values for dim in DEFAULT_DOMAIN]
EXHAUSTIVE = list(itertools.product(*VALUES))
DIAGONAL = [(VALUES[0][i], VALUES[1][i], VALUES[2][i]) for i in range(5)]
# Carré latin d'ordre 5 : tableau orthogonal OA(25; 3, 5, 2), optimal en Pairwise.
LATIN = [(VALUES[0][i], VALUES[1][j], VALUES[2][(i + j) % 5]) for i in range(5) for j in range(5)]


def test_theoretical_totals():
    assert uniwise_coverage([]).total == 15
    assert pairwise_coverage([]).total == 75
    assert triplewise_coverage([]).total == 125


def test_empty_suite_has_zero_coverage_without_division_error():
    report = pairwise_coverage([])
    assert report.covered_count == 0
    assert report.ratio == 0
    assert not report.is_complete
    assert len(report.missing) == 75


def test_exhaustive_covers_everything():
    assert uniwise_coverage(EXHAUSTIVE).is_complete
    assert pairwise_coverage(EXHAUSTIVE).is_complete
    assert triplewise_coverage(EXHAUSTIVE).is_complete


def test_diagonal_is_uniwise_complete_but_not_pairwise():
    assert uniwise_coverage(DIAGONAL).is_complete
    pairs = pairwise_coverage(DIAGONAL)
    assert pairs.covered_count == 15  # 5 cas × 3 paires chacun
    assert len(pairs.missing) == 60
    assert pairs.percent == pytest.approx(20.0)


def test_latin_square_is_optimal_pairwise_with_25_cases():
    assert len(LATIN) == 25
    assert pairwise_coverage(LATIN).is_complete
    triples = triplewise_coverage(LATIN)
    assert triples.covered_count == 25
    assert not triples.is_complete  # 100 % Pairwise != tous les triplets


def test_missing_elements_are_listed_precisely():
    report = uniwise_coverage(DIAGONAL[:4])
    assert not report.is_complete
    assert report.covered_count == 12
    assert [report.format_element(e) for e in report.missing] == ["a=10", "b=10", "c=10"]


def test_pairwise_breakdown_by_dimension_pair():
    breakdown = pairwise_coverage(DIAGONAL).by_dimensions()
    assert breakdown == {("a", "b"): (5, 25), ("a", "c"): (5, 25), ("b", "c"): (5, 25)}


def test_format_element_for_pairs():
    report = pairwise_coverage([])
    assert report.format_element(report.missing[0]) == "a=-10, b=-10"


def test_duplicates_are_not_double_counted():
    assert uniwise_coverage(DIAGONAL + DIAGONAL).covered_count == 15


def test_values_outside_domain_are_reported_separately():
    report = uniwise_coverage([(D(3), D(0), D(0))])
    assert report.covered_count == 2  # b=0 et c=0
    assert report.out_of_domain == (("a", D(3)),)


def test_accepts_quadratic_case_objects():
    cases = [
        QuadraticCase(case_id=f"X-{i}", method="test", a=a, b=b, c=c)
        for i, (a, b, c) in enumerate(DIAGONAL)
    ]
    assert uniwise_coverage(cases).is_complete


def test_strength_validation():
    with pytest.raises(ValueError):
        interaction_coverage(EXHAUSTIVE, DEFAULT_DOMAIN, 0)
    with pytest.raises(ValueError):
        interaction_coverage(EXHAUSTIVE, DEFAULT_DOMAIN, 4)
    with pytest.raises(ValueError):
        interaction_coverage([(D(1), D(2))], DEFAULT_DOMAIN, 1)  # mauvais nombre de valeurs


def test_covering_cases_lists_case_ids_per_pair():
    cases = [
        QuadraticCase(case_id=f"D-{i}", method="test", a=a, b=b, c=c) for i, (a, b, c) in enumerate(DIAGONAL)
    ]
    mapping = covering_cases(cases)
    assert len(mapping) == 75
    assert mapping[(("a", D(-10)), ("b", D(-10)))] == ("D-0",)
    assert mapping[(("a", D(-10)), ("b", D(10)))] == ()
    assert sum(1 for ids in mapping.values() if ids) == 15


def test_category_coverage():
    report = category_coverage(
        [Category.TWO_REAL_ROOTS, Category.TWO_REAL_ROOTS, Category.LINEAR_ROOT, Category.INVALID_INPUT]
    )
    assert report.covered == frozenset({Category.TWO_REAL_ROOTS, Category.LINEAR_ROOT})
    assert Category.INFINITE_SOLUTIONS in report.missing
    assert Category.INVALID_INPUT not in report.missing  # hors catégories mathématiques
    assert report.counts[Category.TWO_REAL_ROOTS] == 2
    assert report.total == 6
    assert report.percent == pytest.approx(100 * 2 / 6)
