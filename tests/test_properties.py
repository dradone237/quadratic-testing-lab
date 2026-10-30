"""Tests par propriétés (Hypothesis) — section 13 de l'énoncé.

Hypothèses explicites :
- coefficients générés dans le domaine S-10 (|x| ≤ 10¹², ≤ 12 décimales) ;
- profil reproductible ``derandomize=True`` (voir conftest.py) ;
- comparaisons TOLÉRANTES (10⁻⁴⁰ en relatif) pour les racines irrationnelles,
  EXACTES pour les catégories et le discriminant.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from hypothesis import assume, example, given
from hypothesis import strategies as st

from quadratic_lab.models import MATH_CATEGORIES, Category
from quadratic_lab.oracle import REL_TOL, compare, expected_result
from quadratic_lab.solver import solve
from quadratic_lab.validation import MAX_ABS_COEFFICIENT

D = Decimal
LIMIT = int(MAX_ABS_COEFFICIENT)


def decimals_with(places: int, bound: int):
    return st.decimals(min_value=-bound, max_value=bound, places=places, allow_nan=False, allow_infinity=False)


# Mélange de petites valeurs (beaucoup de cas dégénérés et de Delta = 0),
# de décimaux moyens et de valeurs extrêmes du domaine.
coefficient = st.one_of(
    st.integers(-12, 12).map(D),
    decimals_with(2, 1000),
    decimals_with(6, 10**6),
    decimals_with(12, 1),
    st.integers(-LIMIT, LIMIT).map(D),
    st.sampled_from([D(0), D("1e-12"), D("-1e-12"), D("1e12"), D("-1e12")]),
)
nonzero = coefficient.filter(lambda x: x != 0)


def close(x: Fraction, y: Fraction, tol: Fraction = REL_TOL) -> bool:
    if y == 0:
        return x == 0
    return abs(x - y) <= tol * abs(y)


@given(coefficient, coefficient, coefficient)
@example(D(0), D(0), D(0))
@example(D(1), D(2), D(1))
def test_never_raises_and_always_valid_category(a, b, c):
    result = solve(a, b, c)
    assert result.category in MATH_CATEGORIES
    assert result.error is None


@given(coefficient, coefficient, coefficient)
def test_matches_independent_oracle(a, b, c):
    verdict = compare(expected_result(a, b, c), solve(a, b, c))
    assert verdict.passed, verdict.failures


@given(nonzero, coefficient, coefficient)
def test_category_consistent_with_exact_discriminant(a, b, c):
    result = solve(a, b, c)
    delta = Fraction(b) ** 2 - 4 * Fraction(a) * Fraction(c)
    assert Fraction(result.discriminant) == delta
    expected = (
        Category.TWO_REAL_ROOTS if delta > 0 else Category.DOUBLE_REAL_ROOT if delta == 0 else Category.NO_REAL_ROOT
    )
    assert result.category is expected
    assert len(result.roots) == {Category.TWO_REAL_ROOTS: 2, Category.DOUBLE_REAL_ROOT: 1}.get(expected, 0)


@given(nonzero, coefficient, coefficient)
def test_vieta_relations(a, b, c):
    result = solve(a, b, c)
    assume(result.category is Category.TWO_REAL_ROOTS)
    x1, x2 = (Fraction(r) for r in result.roots)
    fa, fb, fc = Fraction(a), Fraction(b), Fraction(c)
    assert x1 < x2
    assert abs((x1 + x2) + fb / fa) <= REL_TOL * (abs(x1) + abs(x2))
    assert abs(x1 * x2 - fc / fa) <= REL_TOL * abs(x1 * x2) or (fc == 0 and x1 * x2 == 0)


# Racines construites : a(x - r1)(x - r2) = a x² - a(r1 + r2) x + a r1 r2.
small_root = decimals_with(2, 1000)
small_lead = st.one_of(st.integers(-50, 50).map(D), decimals_with(1, 50)).filter(lambda x: x != 0)


@given(small_lead, small_root, small_root)
def test_permutation_of_roots_gives_the_same_solution(a, r1, r2):
    b1, c1 = -a * (r1 + r2), a * r1 * r2
    b2, c2 = -a * (r2 + r1), a * r2 * r1
    first, second = solve(a, b1, c1), solve(a, b2, c2)
    assert first == second
    if r1 == r2:
        assert first.category is Category.DOUBLE_REAL_ROOT
        assert first.roots == (r1,)
    else:
        assert first.category is Category.TWO_REAL_ROOTS
        assert [Fraction(x) for x in first.roots] == sorted([Fraction(r1), Fraction(r2)])


@given(nonzero, coefficient, coefficient, st.sampled_from([D(-3), D(-1), D(2), D("0.5"), D(10), D("-0.25")]))
def test_scaling_all_coefficients_preserves_solutions(a, b, c, k):
    ka, kb, kc = k * a, k * b, k * c
    # Hypothèse : les coefficients mis à l'échelle restent dans le domaine.
    assume(all(abs(v) <= MAX_ABS_COEFFICIENT for v in (ka, kb, kc)))
    assume(all(v.normalize().as_tuple().exponent >= -12 for v in (ka, kb, kc) if v != 0))
    original, scaled = solve(a, b, c), solve(ka, kb, kc)
    assert scaled.category is original.category
    assert len(scaled.roots) == len(original.roots)
    for x, y in zip(scaled.roots, original.roots):
        assert close(Fraction(x), Fraction(y))


@given(small_lead, small_root)
def test_double_root_is_exact(a, r):
    result = solve(a, -2 * a * r, a * r * r)
    assert result.category is Category.DOUBLE_REAL_ROOT
    assert result.roots == (r,) or (r == 0 and result.roots == (D(0),))


@given(nonzero, coefficient)
def test_linear_equations(b, c):
    result = solve(0, b, c)
    assert result.category is Category.LINEAR_ROOT
    assert close(Fraction(result.roots[0]), -Fraction(c) / Fraction(b))


# ---------------------------------------------------------------------------
# Données invalides : testées séparément
# ---------------------------------------------------------------------------
NUMERIC_CHARS = set("0123456789+-.eE")


@given(st.text(min_size=0, max_size=12))
def test_arbitrary_text_is_parsed_or_cleanly_rejected(text):
    result = solve(text, 1, 1)
    if result.category is Category.INVALID_INPUT:
        assert result.error
    else:
        assert set(text.strip()) <= NUMERIC_CHARS
        assert result.a == D(text.strip())


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_floats_never_crash(x):
    result = solve(x, 1, 1)
    assert result.category in (*MATH_CATEGORIES, Category.INVALID_INPUT)


@given(st.integers().filter(lambda n: abs(n) > LIMIT))
def test_out_of_range_integers_are_rejected(n):
    result = solve(1, n, 1)
    assert result.category is Category.INVALID_INPUT
    assert "limite" in result.error
