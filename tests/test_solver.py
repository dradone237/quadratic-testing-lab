"""Tests en boîte noire du solveur : cas obligatoires et cas avancés.

Chaque attendu est établi analytiquement (à la main), sans appeler le solveur.
"""

from __future__ import annotations

from decimal import Context, Decimal
from fractions import Fraction

import pytest

from quadratic_lab.models import Category, SolveResult
from quadratic_lab.solver import format_number, format_roots, solve

D = Decimal


def roots_as_fractions(result: SolveResult) -> list[Fraction]:
    return [Fraction(x) for x in result.roots]


def assert_roots_close(result: SolveResult, expected: list[str], rel: str = "1e-45") -> None:
    assert len(result.roots) == len(expected)
    tol = Fraction(D(rel))
    for got, want in zip(result.roots, expected):
        want_f = Fraction(D(want)) if "/" not in want else Fraction(want)
        got_f = Fraction(got)
        if want_f == 0:
            assert got_f == 0
        else:
            assert abs(got_f - want_f) / abs(want_f) <= tol, (got, want)


# ---------------------------------------------------------------------------
# Les 8 cas obligatoires de l'énoncé (section 11)
# ---------------------------------------------------------------------------
MANDATORY = [
    # (id, a, b, c, catégorie, racines exactes, discriminant)
    ("CAS1", 1, 0, -1, Category.TWO_REAL_ROOTS, ["-1", "1"], "4"),
    ("CAS2", 1, 2, 1, Category.DOUBLE_REAL_ROOT, ["-1"], "0"),
    ("CAS3", 1, 0, 1, Category.NO_REAL_ROOT, [], "-4"),
    ("CAS4", 0, 2, -4, Category.LINEAR_ROOT, ["2"], None),
    ("CAS5", 0, 0, 0, Category.INFINITE_SOLUTIONS, [], None),
    ("CAS6", 0, 0, 5, Category.NO_SOLUTION, [], None),
    ("CAS7", 1, -3, 2, Category.TWO_REAL_ROOTS, ["1", "2"], "1"),
    ("CAS8", -1, 0, 1, Category.TWO_REAL_ROOTS, ["-1", "1"], "4"),
]


@pytest.mark.parametrize("case_id,a,b,c,category,roots,delta", MANDATORY, ids=[m[0] for m in MANDATORY])
def test_mandatory_cases_exact(case_id, a, b, c, category, roots, delta):
    result = solve(a, b, c)
    assert result.category is category
    # Les racines de ces cas sont des entiers : on exige l'égalité EXACTE.
    assert result.roots == tuple(D(r) for r in roots)
    if delta is None:
        assert result.discriminant is None
    else:
        assert result.discriminant == D(delta)
    assert result.error is None
    assert result.is_valid


# ---------------------------------------------------------------------------
# Coefficients décimaux, négatifs, petits, grands
# ---------------------------------------------------------------------------
def test_decimal_coefficients():
    # 0.5x² - 1.5x + 1 = 0.5(x-1)(x-2)
    result = solve("0.5", "-1.5", "1")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.roots == (D(1), D(2))
    assert result.discriminant == D("0.25")


def test_classic_float_rounding_trap_is_exact():
    # x² - 0.3x + 0.02 = (x - 0.1)(x - 0.2) : piège classique des flottants.
    result = solve("1", "-0.3", "0.02")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.roots == (D("0.1"), D("0.2"))
    assert result.discriminant == D("0.01")


def test_negative_coefficients():
    # -2x² - 4x + 6 = -2(x+3)(x-1)
    result = solve(-2, -4, 6)
    assert result.roots == (D(-3), D(1))
    assert result.discriminant == D(64)


def test_very_small_coefficients():
    # 1e-12 x² - 1e-12 = 0  <=>  x² = 1
    result = solve("1e-12", "0", "-1e-12")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.roots == (D(-1), D(1))
    assert result.discriminant == D("4e-24")


def test_very_large_coefficients():
    # Anomalie de test corrigée : la première version utilisait b = -3e12,
    # HORS domaine (|x| ≤ 1e12) ; le solveur avait correctement répondu
    # INVALID_INPUT.
    result = solve("1e11", "-3e11", "2e11")
    assert result.roots == (D(1), D(2))
    assert result.discriminant == D("1e22")


def test_coefficients_at_the_domain_limit():
    # 1e12 (x² + x - 1) : racines (-1 ± √5)/2, limites exactes du domaine.
    result = solve("1e12", "1e12", "-1e12")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.discriminant == D("5e24")
    # Toutes les opérations dans un contexte à 60 chiffres (cf. anomalie A1).
    ctx = Context(prec=60)
    golden = ctx.divide(ctx.subtract(ctx.sqrt(D(5)), D(1)), D(2))
    assert abs(Fraction(result.roots[1]) - Fraction(golden)) < Fraction(1, 10**48)


def test_coefficient_just_outside_the_domain_is_rejected():
    assert solve("1e12", "-3e12", "2e12").category is Category.INVALID_INPUT


def test_extreme_magnitudes_no_catastrophic_cancellation():
    # x² + 1e24 x + 1 (mis à l'échelle) : racines ~ -1e24 et ~ -1e-24.
    # La formule naïve en flottants donne 0 pour la petite racine.
    result = solve("1e-12", "1e12", "1e-12")
    assert result.category is Category.TWO_REAL_ROOTS
    small = result.roots[1]
    assert small != 0
    # Produit des racines = c/a = 1 (Viète), à 1e-45 près en relatif.
    product = Fraction(result.roots[0]) * Fraction(result.roots[1])
    assert abs(product - 1) <= Fraction(1, 10**45)
    assert abs(Fraction(small) + Fraction(1, 10**24)) / Fraction(1, 10**24) <= Fraction(1, 10**45)


def test_irrational_roots_sqrt2():
    result = solve(1, 0, -2)
    sqrt2 = D(2).sqrt(context=Context(prec=60))
    # Anomalie de test corrigée : « -sqrt2 » arrondit au contexte courant
    # (28 chiffres) ; copy_negate() change le signe sans arrondir.
    assert_roots_close(result, [str(sqrt2.copy_negate()), str(sqrt2)])


def test_double_root_non_terminating_decimal():
    # 9x² - 6x + 1 = (3x - 1)² : racine double 1/3 (développement infini).
    result = solve(9, -6, 1)
    assert result.category is Category.DOUBLE_REAL_ROOT
    assert_roots_close(result, ["1/3"])


def test_linear_non_terminating():
    result = solve(0, 3, 1)
    assert result.category is Category.LINEAR_ROOT
    assert_roots_close(result, ["-1/3"])


# ---------------------------------------------------------------------------
# Discriminant proche de zéro : aucune tolérance sur le signe de Delta
# ---------------------------------------------------------------------------
def test_tiny_positive_discriminant_gives_two_roots():
    result = solve("1", "2", "0.999999999999")
    assert result.discriminant == D("4E-12")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.roots == (D("-1.000001"), D("-0.999999"))


def test_extremely_tiny_positive_discriminant_is_not_rounded_to_zero():
    # a·c = 10¹² − 10⁻²⁴ et b² = 4·10¹²  =>  Delta = 4·10⁻²⁴ > 0 (exact).
    # En double précision, Delta vaudrait 0 et l'on conclurait à tort à une
    # racine double.
    result = solve("1000000.000000000001", "2000000", "999999.999999999999")
    assert result.discriminant == D("4E-24")
    assert result.category is Category.TWO_REAL_ROOTS
    assert result.roots[0] < result.roots[1]
    assert result.roots[0] == D(-1)


def test_tiny_negative_discriminant_gives_no_real_root():
    result = solve("1", "2", "1.000000000001")
    assert result.discriminant == D("-4E-12")
    assert result.category is Category.NO_REAL_ROOT
    assert result.roots == ()


# ---------------------------------------------------------------------------
# Contrat de structure (S-02, S-03, S-04, S-26)
# ---------------------------------------------------------------------------
def test_roots_sorted_even_when_a_negative():
    result = solve(-1, 3, -2)  # -(x-1)(x-2)
    assert result.roots == (D(1), D(2))


def test_zero_root_has_no_negative_sign():
    # q = -2 et x2 = c/q = 0/-2 = -0 sans normalisation (défaut potentiel).
    result = solve(1, 2, 0)
    assert result.roots == (D(-2), D(0))
    assert not result.roots[1].is_signed()
    assert format_number(result.roots[1]) == "0"


def test_double_root_zero_has_no_negative_sign():
    result = solve(-5, 0, 0)
    assert result.category is Category.DOUBLE_REAL_ROOT
    assert result.roots == (D(0),)
    assert not result.roots[0].is_signed()


def test_complex_roots_extension_does_not_change_category():
    result = solve(1, 2, 5)  # x = -1 ± 2i
    assert result.category is Category.NO_REAL_ROOT
    assert result.roots == ()
    assert result.complex_roots == ((D(-1), D(-2)), (D(-1), D(2)))


def test_complex_roots_absent_for_real_cases():
    assert solve(1, 0, -1).complex_roots == ()


def test_result_is_immutable():
    result = solve(1, 0, -1)
    with pytest.raises(AttributeError):
        result.category = Category.NO_SOLUTION  # type: ignore[misc]


def test_coefficients_are_stored_as_validated_decimals():
    result = solve("1.5", 0, -6)
    assert (result.a, result.b, result.c) == (D("1.5"), D(0), D(-6))
    assert result.roots == (D(-2), D(2))


@pytest.mark.parametrize(
    "a,b,c,needle",
    [
        (1, 0, -1, "deux racines réelles distinctes"),
        (1, 2, 1, "racine double"),
        (1, 0, 1, "aucune racine réelle"),
        (0, 2, -4, "premier degré"),
        (0, 0, 0, "infinité"),
        (0, 0, 5, "aucune solution"),
        ("x", 0, 0, "invalide"),
    ],
)
def test_explanations_are_in_french(a, b, c, needle):
    assert needle in solve(a, b, c).explanation().lower()


def test_to_dict_is_serialisable():
    import json

    data = solve(1, -3, 2).to_dict()
    text = json.dumps(data)
    assert data["category"] == "TWO_REAL_ROOTS"
    assert data["roots"] == ["1", "2"]
    assert "TWO_REAL_ROOTS" in text


# ---------------------------------------------------------------------------
# Affichage (S-25)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value,digits,expected",
    [
        (D(0), 15, "0"),
        (D("-0"), 15, "0"),
        (D(2), 15, "2"),
        (D("-1.5"), 15, "-1.5"),
        (D(1) / D(3), 15, "0.333333333333333"),
        (D(2) / D(3), 5, "0.66667"),
        (D("1e24"), 15, "1E+24"),
        (D("-1e-24"), 15, "-1E-24"),
        (D("123456789"), 15, "123456789"),
    ],
)
def test_format_number(value, digits, expected):
    assert format_number(value, digits) == expected


def test_format_roots_increases_digits_to_distinguish_close_roots():
    result = solve("1000000.000000000001", "2000000", "999999.999999999999")
    shown = format_roots(result.roots)
    assert len(set(shown)) == 2, shown
    # Les deux racines sont distinctes à 1e-18 près : 15 chiffres ne suffisent pas.
    assert format_number(result.roots[0]) == format_number(result.roots[1])


def test_format_roots_default_digits_when_distinct():
    assert format_roots((D(1), D(2))) == ["1", "2"]
