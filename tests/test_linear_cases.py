"""Tests des cas dégénérés a = 0 (S-01) : premier degré, 0 = 0, c = 0."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quadratic_lab.models import Category
from quadratic_lab.solver import solve

D = Decimal


@pytest.mark.parametrize(
    "b,c,root",
    [
        (2, -4, "2"),
        (-4, 2, "0.5"),
        (1, 0, "0"),
        (-1, 0, "0"),
        ("0.5", "1", "-2"),
        ("1e12", "1e-12", "-1E-24"),
        ("1e-12", "1e12", "-1E+24"),
        (10, -10, "1"),
    ],
)
def test_linear_equation_single_root(b, c, root):
    result = solve(0, b, c)
    assert result.category is Category.LINEAR_ROOT
    assert result.roots == (D(root),)
    assert result.discriminant is None
    assert not result.roots[0].is_signed() or result.roots[0] != 0


def test_linear_is_not_confused_with_double_root():
    # 0x² + 2x + 0 : premier degré (racine 0), PAS une racine double.
    result = solve(0, 2, 0)
    assert result.category is Category.LINEAR_ROOT
    assert result.roots == (D(0),)


@pytest.mark.parametrize("zero", [0, "0", "0.0", "-0", "0e5", D("-0.000"), 0.0, -0.0])
def test_all_zero_spellings_give_infinite_solutions(zero):
    result = solve(zero, zero, zero)
    assert result.category is Category.INFINITE_SOLUTIONS
    assert result.roots == ()


@pytest.mark.parametrize("c", [5, -5, "1e-12", "-1e12", "0.000000000001"])
def test_constant_nonzero_equation_has_no_solution(c):
    result = solve(0, 0, c)
    assert result.category is Category.NO_SOLUTION
    assert result.roots == ()
    assert result.error is None  # ce n'est PAS une erreur de saisie


def test_no_solution_differs_from_no_real_root_and_invalid_input():
    impossible = solve(0, 0, 5)
    complex_only = solve(1, 0, 5)
    invalid = solve("abc", 0, 5)
    assert {impossible.category, complex_only.category, invalid.category} == {
        Category.NO_SOLUTION,
        Category.NO_REAL_ROOT,
        Category.INVALID_INPUT,
    }
