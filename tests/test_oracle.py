"""Tests de l'oracle mathématique (problème de l'oracle, S-30 à S-33).

On teste l'oracle lui-même : un oracle faux rendrait tous les autres tests
inutiles. Trois angles :
1. indépendance (il n'utilise pas le code du solveur) ;
2. justesse face aux formes closes calculées à la main ;
3. capacité à DÉTECTER des résultats faux (tests « négatifs »).
"""

from __future__ import annotations

import ast
import math
from decimal import Context, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from quadratic_lab import oracle
from quadratic_lab.models import Category, SolveResult
from quadratic_lab.oracle import (
    ORACLE_DIGITS,
    REFERENCE_CASES,
    REL_TOL,
    ClosedForm,
    compare,
    expected_result,
    relative_residual,
    vieta_errors,
)
from quadratic_lab.solver import solve

D = Decimal


# ---------------------------------------------------------------------------
# 1. Indépendance
# ---------------------------------------------------------------------------
def test_oracle_does_not_import_the_solver():
    source = Path(oracle.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
    assert not any("solver" in name for name in imported), imported
    assert not any("validation" in name for name in imported), imported


def test_oracle_uses_exact_arithmetic():
    expectation = expected_result(D(1), D(-3), D(2))
    assert isinstance(expectation.discriminant, Fraction)
    assert all(isinstance(r, Fraction) for r in expectation.roots)
    assert expectation.exact


def test_tolerance_constants():
    assert REL_TOL == Fraction(1, 10**40)
    assert ORACLE_DIGITS >= 100


# ---------------------------------------------------------------------------
# 2. Formes closes calculées à la main
# ---------------------------------------------------------------------------
def test_closed_form_arithmetic():
    golden = ClosedForm(Fraction(1, 2), Fraction(1, 2), Fraction(5))  # (1+√5)/2
    assert not golden.is_rational
    value = golden.to_fraction(60)
    assert abs(value * value - value - 1) < Fraction(1, 10**55)
    assert ClosedForm(Fraction(-3)).is_rational
    assert ClosedForm(Fraction(-3)).to_fraction() == -3
    assert "√5" in str(golden)


def test_reference_cases_cover_every_mathematical_category():
    categories = {case.category for case in REFERENCE_CASES}
    assert categories == {
        Category.TWO_REAL_ROOTS,
        Category.DOUBLE_REAL_ROOT,
        Category.NO_REAL_ROOT,
        Category.LINEAR_ROOT,
        Category.INFINITE_SOLUTIONS,
        Category.NO_SOLUTION,
    }
    ids = [case.case_id for case in REFERENCE_CASES]
    assert len(ids) == len(set(ids))
    assert len(REFERENCE_CASES) >= 20


@pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda c: c.case_id)
def test_hand_computed_roots_satisfy_their_equation(case):
    """Vérifie les calculs « à la main » par substitution directe."""
    a, b, c = (Fraction(D(v)) for v in (case.a, case.b, case.c))
    for root in case.roots:
        x = root.to_fraction(150)
        scale = abs(a) * x * x + abs(b) * abs(x) + abs(c)
        residual = a * x * x + b * x + c
        assert abs(residual) <= Fraction(1, 10**100) * scale, (case.case_id, root)
    if case.discriminant is not None:
        assert b * b - 4 * a * c == Fraction(D(case.discriminant))


@pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda c: c.case_id)
def test_oracle_agrees_with_hand_computation(case):
    expectation = expected_result(D(case.a), D(case.b), D(case.c))
    assert expectation.category is case.category
    assert len(expectation.roots) == len(case.roots)
    for got, root in zip(expectation.roots, case.roots):
        want = root.to_fraction(150)
        if want == 0:
            assert got == 0
        else:
            assert abs(got - want) / abs(want) < Fraction(1, 10**70)
    if case.discriminant is not None:
        assert expectation.discriminant == Fraction(D(case.discriminant))
    # Racines rationnelles => l'oracle doit être exact.
    if all(root.is_rational for root in case.roots):
        assert expectation.exact


def test_oracle_irrational_root_precision():
    expectation = expected_result(D(1), D(0), D(-2))
    assert not expectation.exact
    sqrt2 = Fraction(D(2).sqrt(Context(prec=140)))
    assert abs(expectation.roots[1] - sqrt2) < Fraction(1, 10**118)


@pytest.mark.parametrize(
    "a,b,c,category",
    [
        ("0", "0", "0", Category.INFINITE_SOLUTIONS),
        ("0", "0", "3", Category.NO_SOLUTION),
        ("0", "4", "2", Category.LINEAR_ROOT),
        ("1e13", "0", "0", Category.INVALID_INPUT),
        ("1e-13", "0", "0", Category.INVALID_INPUT),
        ("NaN", "0", "0", Category.INVALID_INPUT),
        ("Infinity", "0", "0", Category.INVALID_INPUT),
    ],
)
def test_oracle_degenerate_and_invalid(a, b, c, category):
    assert expected_result(D(a), D(b), D(c)).category is category


def test_oracle_rejects_unsupported_types():
    assert expected_result(True, 1, 1).category is Category.INVALID_INPUT
    assert expected_result(1.5, 1, 1).category is Category.INVALID_INPUT  # float : ambigu
    assert expected_result("abc", 1, 1).category is Category.INVALID_INPUT
    assert expected_result(Fraction(1, 3), 1, 1).category is Category.INVALID_INPUT


def test_oracle_accepts_int_and_str():
    assert expected_result(1, "-3", 2).roots == (Fraction(1), Fraction(2))


# ---------------------------------------------------------------------------
# 3. L'oracle détecte les résultats faux
# ---------------------------------------------------------------------------
def _result(category, a, b, c, roots=(), delta=None):
    return SolveResult(
        category=category,
        a=D(a),
        b=D(b),
        c=D(c),
        discriminant=None if delta is None else D(delta),
        roots=tuple(D(r) for r in roots),
    )


def test_compare_accepts_correct_result():
    verdict = compare(expected_result(D(1), D(-3), D(2)), solve(1, -3, 2))
    assert verdict.passed
    assert verdict.failures == ()
    assert any("Viète" in check for check in verdict.checks)
    assert any("résidu" in check for check in verdict.checks)
    assert verdict.max_root_error == 0


def test_compare_detects_wrong_category():
    wrong = _result(Category.NO_SOLUTION, 0, 0, 0)
    verdict = compare(expected_result(D(0), D(0), D(0)), wrong)
    assert not verdict.passed
    assert "catégorie" in verdict.failures[0].lower()


def test_compare_detects_tiny_root_error():
    wrong = _result(Category.TWO_REAL_ROOTS, 1, -3, 2, roots=("1", "2.0000000000000000000000000001"), delta="1")
    verdict = compare(expected_result(D(1), D(-3), D(2)), wrong)
    assert not verdict.passed
    assert any("racine" in failure.lower() for failure in verdict.failures)


def test_compare_detects_wrong_discriminant():
    wrong = _result(Category.TWO_REAL_ROOTS, 1, -3, 2, roots=("1", "2"), delta="2")
    verdict = compare(expected_result(D(1), D(-3), D(2)), wrong)
    assert not verdict.passed
    assert any("discriminant" in failure.lower() for failure in verdict.failures)


def test_compare_detects_missing_root():
    wrong = _result(Category.TWO_REAL_ROOTS, 1, -3, 2, roots=("1",), delta="1")
    verdict = compare(expected_result(D(1), D(-3), D(2)), wrong)
    assert not verdict.passed


def test_compare_detects_signed_zero_and_order_issues():
    wrong = _result(Category.TWO_REAL_ROOTS, 1, -3, 2, roots=("2", "1"), delta="1")
    verdict = compare(expected_result(D(1), D(-3), D(2)), wrong)
    assert not verdict.passed  # contrat S-03 : racines triées


def test_naive_float_solver_is_caught_by_the_oracle():
    """Démonstration du problème de l'oracle : la formule scolaire en
    flottants paraît correcte sur les cas simples mais échoue sur un cas
    d'annulation catastrophique, et l'oracle le détecte."""

    def naive(a, b, c):
        delta = b * b - 4 * a * c
        s = math.sqrt(delta)
        return sorted(((-b - s) / (2 * a), (-b + s) / (2 * a)))

    # Cas simple : la formule naïve donne le bon résultat exact.
    assert naive(1.0, -3.0, 2.0) == [1.0, 2.0]

    # Cas difficile : x² + 1e8 x + 1 = 0.
    x1, x2 = naive(1.0, 1e8, 1.0)
    fake = _result(
        Category.TWO_REAL_ROOTS, 1, "1e8", 1, roots=(repr(x1), repr(x2)), delta="9999999999999996"
    )
    verdict = compare(expected_result(D(1), D("1e8"), D(1)), fake)
    assert not verdict.passed
    # Le vrai solveur, lui, passe.
    assert compare(expected_result(D(1), D("1e8"), D(1)), solve(1, "1e8", 1)).passed


def test_residual_and_vieta_helpers():
    a, b, c = Fraction(1), Fraction(-3), Fraction(2)
    assert relative_residual(a, b, c, Fraction(1)) == 0
    assert relative_residual(a, b, c, Fraction(3, 2)) > 0
    sum_err, prod_err = vieta_errors(a, b, c, Fraction(1), Fraction(2))
    assert sum_err == 0 and prod_err == 0
    sum_err, prod_err = vieta_errors(a, b, c, Fraction(1), Fraction(3))
    assert sum_err > 0 and prod_err > 0


def test_residual_for_zero_scale():
    # Polynôme nul évalué en 0 : échelle nulle, résidu nul -> 0 (pas de division par 0).
    assert relative_residual(Fraction(0), Fraction(0), Fraction(0), Fraction(0)) == 0


def test_verdict_summary_is_french():
    verdict = compare(expected_result(D(1), D(0), D(1)), solve(1, 0, 1))
    assert verdict.passed
    assert "conforme" in verdict.summary().lower()
