"""Tests en boîte blanche du discriminant (S-21, S-22).

Le discriminant doit être EXACT dans tout le domaine d'entrée ; le calcul
piège le signal ``Inexact`` pour qu'un arrondi ne passe jamais inaperçu.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest

from quadratic_lab.solver import NumericalError, compute_discriminant
from quadratic_lab.validation import MAX_ABS_COEFFICIENT

D = Decimal


@pytest.mark.parametrize(
    "a,b,c,expected",
    [
        ("1", "0", "-1", "4"),
        ("1", "2", "1", "0"),
        ("1", "0", "1", "-4"),
        ("1", "-3", "2", "1"),
        ("-1", "0", "1", "4"),
        ("0.5", "-1.5", "1", "0.25"),
        ("2", "0", "0", "0"),
        ("0", "7", "3", "49"),  # a = 0 : b² (non utilisé par le solveur)
        ("-10", "-10", "-10", "-300"),
        ("10", "10", "-10", "500"),
    ],
)
def test_discriminant_values(a, b, c, expected):
    assert compute_discriminant(D(a), D(b), D(c)) == D(expected)


def test_discriminant_exact_at_domain_corners():
    """Pire cas de longueur : 25 chiffres significatifs par coefficient."""
    worst = D("999999999999.999999999999")  # 24 chiffres, 12 décimales
    for a, b, c in [
        (worst, worst, worst),
        (worst, worst, -worst),
        (-worst, D("1E-12"), worst),
        (MAX_ABS_COEFFICIENT, MAX_ABS_COEFFICIENT, -MAX_ABS_COEFFICIENT),
        (D("1E-12"), D("1E-12"), D("1E-12")),
    ]:
        exact = Fraction(b) ** 2 - 4 * Fraction(a) * Fraction(c)
        assert Fraction(compute_discriminant(a, b, c)) == exact


def test_tiny_discriminant_is_exact_and_positive():
    a, b, c = D("1000000.000000000001"), D("2000000"), D("999999.999999999999")
    assert compute_discriminant(a, b, c) == D("4E-24")


def test_discriminant_outside_domain_raises_instead_of_rounding():
    """Hors domaine (trop de chiffres), l'arrondi est détecté, pas masqué."""
    too_precise = D("1." + "1" * 60)
    with pytest.raises(NumericalError):
        compute_discriminant(D(1), too_precise, D(1))
