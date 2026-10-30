"""Tests de robustesse : validation des entrées (S-10 à S-14).

Une saisie invalide est rejetée avec un message explicite et n'est jamais
convertie silencieusement en zéro.
"""

from __future__ import annotations

import math
from decimal import Decimal
from fractions import Fraction

import pytest

from quadratic_lab.models import Category
from quadratic_lab.solver import solve
from quadratic_lab.validation import (
    MAX_ABS_COEFFICIENT,
    MAX_DECIMAL_PLACES,
    InvalidCoefficientError,
    parse_coefficient,
    parse_user_input,
    validate_coefficients,
)

D = Decimal

INVALID_VALUES = [
    ("", "vide"),
    ("   ", "vide"),
    (None, "manquant"),
    ("abc", "format"),
    ("1..2", "format"),
    ("1.2.3", "format"),
    ("--1", "format"),
    ("1e", "format"),
    ("e5", "format"),
    ("0x1F", "format"),
    ("1_000", "format"),
    ("١٢", "format"),  # chiffres arabo-indiens : non ASCII
    ("1,5", "format"),  # virgule refusée au niveau métier (acceptée par la saisie)
    ("nan", "nan"),
    ("NaN", "nan"),
    ("-inf", "infini"),
    ("Infinity", "infini"),
    ("sNaN", "nan"),
    (float("nan"), "nan"),
    (float("inf"), "infini"),
    (float("-inf"), "infini"),
    (D("NaN"), "nan"),
    (D("Infinity"), "infini"),
    (True, "booléen"),
    (False, "booléen"),
    ([1], "type"),
    (complex(1, 2), "type"),
    (Fraction(1, 3), "type"),
    ("1e13", "limite"),
    ("-1000000000000.5", "limite"),
    (10**13, "limite"),
    (1e300, "limite"),
    ("1e-13", "décimales"),
    ("0.0000000000001", "décimales"),
    (D("1.0000000000001"), "décimales"),
    ("1" * 101, "longueur"),
]


@pytest.mark.parametrize("value,reason", INVALID_VALUES, ids=[repr(v)[:30] for v, _ in INVALID_VALUES])
def test_parse_coefficient_rejects(value, reason):
    with pytest.raises(InvalidCoefficientError) as info:
        parse_coefficient(value, "b")
    message = str(info.value).lower()
    assert "b" in message
    assert reason in message


@pytest.mark.parametrize("value,reason", INVALID_VALUES, ids=[repr(v)[:30] for v, _ in INVALID_VALUES])
def test_solver_returns_invalid_input_category(value, reason):
    result = solve(1, value, 1)
    assert result.category is Category.INVALID_INPUT
    assert result.roots == ()
    assert result.discriminant is None
    assert result.error and reason in result.error.lower()
    assert not result.is_valid


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0"),
        (-7, "-7"),
        ("  42 ", "42"),
        ("+3.5", "3.5"),
        ("-.5", "-0.5"),
        ("5.", "5"),
        ("1e3", "1000"),
        ("1E-12", "1E-12"),
        ("1.000000000000000000", "1"),  # zéros finaux : 1 n'a pas trop de décimales
        (0.1, "0.1"),  # flottant converti via repr, pas 0.1000000000000000055…
        (D("2.50"), "2.5"),
        (MAX_ABS_COEFFICIENT, "1E+12"),
        (-MAX_ABS_COEFFICIENT, "-1E+12"),
        ("999999999999.999999999999", "999999999999.999999999999"),
    ],
)
def test_parse_coefficient_accepts(value, expected):
    assert parse_coefficient(value, "a") == D(expected)


def test_negative_zero_is_canonicalised():
    for value in ("-0", -0.0, D("-0.000"), "-0e10"):
        parsed = parse_coefficient(value)
        assert parsed == 0 and not parsed.is_signed()


def test_limits_are_documented_constants():
    assert MAX_ABS_COEFFICIENT == D("1e12")
    assert MAX_DECIMAL_PLACES == 12


def test_validate_coefficients_names_the_faulty_coefficient():
    with pytest.raises(InvalidCoefficientError) as info:
        validate_coefficients(1, 2, "trois")
    assert info.value.coefficient == "c"
    assert "c" in str(info.value)


def test_invalid_input_is_never_zero():
    """Régression de principe : une saisie vide ne devient pas 0."""
    result = solve("", "", "")
    assert result.category is Category.INVALID_INPUT
    assert result.category is not Category.INFINITE_SOLUTIONS


# ---------------------------------------------------------------------------
# Saisie utilisateur : virgule décimale française (S-14)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("1,5", "1.5"),
        ("-0,25", "-0.25"),
        (" 3,0 ", "3"),
        ("2.75", "2.75"),
        ("1e-3", "0.001"),
        ("−4", "-4"),  # signe moins typographique (U+2212)
    ],
)
def test_user_input_accepts_french_comma(text, expected):
    assert parse_user_input(text, "a") == D(expected)


@pytest.mark.parametrize("text", ["1,000.5", "1.000,5", "1,2,3", ",", "1,", ",5e"])
def test_user_input_rejects_ambiguous_separators(text):
    with pytest.raises(InvalidCoefficientError):
        parse_user_input(text, "a")


def test_user_input_comma_error_mentions_ambiguity():
    with pytest.raises(InvalidCoefficientError) as info:
        parse_user_input("1,000.5", "a")
    assert "ambigu" in str(info.value).lower()


def test_float_conversion_uses_shortest_repr():
    assert parse_coefficient(0.25) == D("0.25")
    assert parse_coefficient(-1e-12) == D("-1e-12")
    assert math.isclose(float(parse_coefficient(2.5e11)), 2.5e11)


def test_float_rounding_garbage_is_rejected_not_rounded():
    # 0.1 + 0.2 == 0.30000000000000004 (17 décimales) : le programme refuse
    # plutôt que d'arrondir silencieusement à 0.3.
    with pytest.raises(InvalidCoefficientError) as info:
        parse_coefficient(0.1 + 0.2, "a")
    assert "décimales" in str(info.value)
