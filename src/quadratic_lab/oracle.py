"""Oracle mathématique INDÉPENDANT du solveur (S-30 à S-33).

Le problème de l'oracle : pour décider si un résultat est correct, il faut
une source de vérité qui ne partage pas les erreurs du programme testé.
Cet oracle se distingue du solveur sur tous les points :

=====================  ==============================  ==========================
Aspect                 Solveur (solver.py)             Oracle (ce module)
=====================  ==============================  ==========================
Arithmétique           Decimal, 50 chiffres            Fraction (rationnels exacts)
Racine carrée          Decimal.sqrt                    math.isqrt sur entiers
Formule                stable q = -(b+sgn(b)√Δ)/2      scolaire (-b ± √Δ)/(2a)
Précision des racines  ~10⁻⁴⁸ relatif                  < 10⁻⁷⁰ relatif (120 chiffres)
Validation du domaine  validation.py (texte, Decimal)  dénominateurs des rationnels
=====================  ==============================  ==========================

Ce module n'importe ni ``solver`` ni ``validation`` (vérifié par un test).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import isqrt

from .models import Category, SolveResult

#: Chiffres significatifs garantis pour les racines irrationnelles.
ORACLE_DIGITS = 120
#: Tolérance relative de comparaison. Justification : le solveur travaille à
#: 50 chiffres et la formule stable ne cumule que quelques arrondis
#: (erreur relative ≲ 10⁻⁴⁸) ; l'oracle est exact à mieux que 10⁻⁷⁰.
#: 10⁻⁴⁰ laisse une marge de 8 ordres de grandeur tout en détectant toute
#: dégradation de précision (un calcul en double précision, ~10⁻¹⁶, échoue).
REL_TOL = Fraction(1, 10**40)
#: Plancher absolu minuscule pour comparer à zéro (les racines non nulles du
#: domaine valent au moins ~10⁻²⁵ en valeur absolue).
ABS_TOL = Fraction(1, 10**80)

_DOMAIN_MAX = 10**12
_DOMAIN_SCALE = 10**12  # au plus 12 décimales <=> x·10¹² entier


# ---------------------------------------------------------------------------
# Formes closes « calculées à la main »
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ClosedForm:
    """Nombre de la forme ``rational + sqrt_coeff·√radicand``."""

    rational: Fraction
    sqrt_coeff: Fraction = Fraction(0)
    radicand: Fraction = Fraction(0)

    @property
    def is_rational(self) -> bool:
        if self.sqrt_coeff == 0 or self.radicand == 0:
            return True
        num, den = self.radicand.numerator, self.radicand.denominator
        return isqrt(num) ** 2 == num and isqrt(den) ** 2 == den

    def to_fraction(self, digits: int = ORACLE_DIGITS) -> Fraction:
        if self.sqrt_coeff == 0 or self.radicand == 0:
            return self.rational
        root, _ = sqrt_fraction(self.radicand, digits)
        return self.rational + self.sqrt_coeff * root

    def __str__(self) -> str:
        if self.sqrt_coeff == 0 or self.radicand == 0:
            return str(self.rational)
        sign = "-" if self.sqrt_coeff < 0 else "+"
        coeff = abs(self.sqrt_coeff)
        coeff_text = "" if coeff == 1 else f"{coeff}·"
        head = "" if self.rational == 0 else f"{self.rational} "
        if not head:
            return f"{'-' if sign == '-' else ''}{coeff_text}√{self.radicand}"
        return f"{head}{sign} {coeff_text}√{self.radicand}"


def _q(text: str) -> Fraction:
    return Fraction(text)


def _cf(rational: str, sqrt_coeff: str = "0", radicand: str = "0") -> ClosedForm:
    return ClosedForm(_q(rational), _q(sqrt_coeff), _q(radicand))


@dataclass(frozen=True)
class ReferenceCase:
    """Cas de référence dont le résultat a été établi à la main."""

    case_id: str
    a: str
    b: str
    c: str
    category: Category
    roots: tuple[ClosedForm, ...]
    discriminant: str | None
    description: str


_T, _D, _N = Category.TWO_REAL_ROOTS, Category.DOUBLE_REAL_ROOT, Category.NO_REAL_ROOT
_L, _I, _S = Category.LINEAR_ROOT, Category.INFINITE_SOLUTIONS, Category.NO_SOLUTION

#: Cas ciblés : les 8 cas obligatoires de l'énoncé, puis les cas avancés.
#: Les racines sont des formes closes obtenues analytiquement (factorisation
#: ou formule résolvante appliquée à la main).
REFERENCE_CASES: tuple[ReferenceCase, ...] = (
    ReferenceCase("CIB-01", "1", "0", "-1", _T, (_cf("-1"), _cf("1")), "4", "CAS 1 : x² - 1 = (x-1)(x+1)"),
    ReferenceCase("CIB-02", "1", "2", "1", _D, (_cf("-1"),), "0", "CAS 2 : x² + 2x + 1 = (x+1)²"),
    ReferenceCase("CIB-03", "1", "0", "1", _N, (), "-4", "CAS 3 : x² + 1 > 0 pour tout réel"),
    ReferenceCase("CIB-04", "0", "2", "-4", _L, (_cf("2"),), None, "CAS 4 : 2x - 4 = 0"),
    ReferenceCase("CIB-05", "0", "0", "0", _I, (), None, "CAS 5 : 0 = 0"),
    ReferenceCase("CIB-06", "0", "0", "5", _S, (), None, "CAS 6 : 5 = 0 impossible"),
    ReferenceCase("CIB-07", "1", "-3", "2", _T, (_cf("1"), _cf("2")), "1", "CAS 7 : (x-1)(x-2)"),
    ReferenceCase("CIB-08", "-1", "0", "1", _T, (_cf("-1"), _cf("1")), "4", "CAS 8 : -(x-1)(x+1)"),
    ReferenceCase("CIB-09", "0.5", "-1.5", "1", _T, (_cf("1"), _cf("2")), "0.25", "Décimaux : 0.5(x-1)(x-2)"),
    ReferenceCase("CIB-10", "2.5", "0", "-10", _T, (_cf("-2"), _cf("2")), "100", "Décimaux : 2.5(x²-4)"),
    ReferenceCase("CIB-11", "-2", "-4", "6", _T, (_cf("-3"), _cf("1")), "64", "Négatifs : -2(x+3)(x-1)"),
    ReferenceCase(
        "CIB-12", "1", "0", "-2", _T, (_cf("0", "-1", "2"), _cf("0", "1", "2")), "8", "Irrationnel : ±√2"
    ),
    ReferenceCase(
        "CIB-13",
        "1",
        "-1",
        "-1",
        _T,
        (_cf("1/2", "-1/2", "5"), _cf("1/2", "1/2", "5")),
        "5",
        "Nombre d'or : (1 ± √5)/2",
    ),
    ReferenceCase(
        "CIB-14", "1e-12", "0", "-1e-12", _T, (_cf("-1"), _cf("1")), "4e-24", "Très petits : 10⁻¹²(x²-1)"
    ),
    ReferenceCase(
        "CIB-15", "1e11", "-3e11", "2e11", _T, (_cf("1"), _cf("2")), "1e22", "Très grands : 10¹¹(x-1)(x-2)"
    ),
    ReferenceCase(
        "CIB-16",
        "1e-12",
        "1e12",
        "1e-12",
        _T,
        (_cf("-500000000000000000000000", "-1/2", "999999999999999999999999999999999999999999999996"),
         _cf("-500000000000000000000000", "1/2", "999999999999999999999999999999999999999999999996")),
        "999999999999999999999999.999999999999999999999996",
        "Annulation catastrophique : racines ~ -10²⁴ et ~ -10⁻²⁴",
    ),
    ReferenceCase(
        "CIB-17",
        "1",
        "2",
        "0.999999999999",
        _T,
        (_cf("-1.000001"), _cf("-0.999999")),
        "4e-12",
        "Delta proche de zéro (positif) : -1 ± 10⁻⁶",
    ),
    ReferenceCase(
        "CIB-18",
        "1000000.000000000001",
        "2000000",
        "999999.999999999999",
        _T,
        (_cf("-1"), _cf("-999999999999999999/1000000000000000001")),
        "4e-24",
        "Delta = 4·10⁻²⁴ > 0 : NE DOIT PAS devenir une racine double",
    ),
    ReferenceCase(
        "CIB-19", "1", "2", "1.000000000001", _N, (), "-4e-12", "Delta proche de zéro (négatif)"
    ),
    ReferenceCase("CIB-20", "9", "-6", "1", _D, (_cf("1/3"),), "0", "Racine double 1/3 = (3x-1)²"),
    ReferenceCase(
        "CIB-21", "1", "-0.3", "0.02", _T, (_cf("0.1"), _cf("0.2")), "0.01", "Arrondi : (x-0.1)(x-0.2)"
    ),
    ReferenceCase("CIB-22", "1", "2", "0", _T, (_cf("-2"), _cf("0")), "4", "c = 0 : x(x+2), racine 0 sans signe"),
    ReferenceCase("CIB-23", "0", "3", "1", _L, (_cf("-1/3"),), None, "Linéaire non décimal : -1/3"),
    ReferenceCase("CIB-24", "4", "0", "-9", _T, (_cf("-3/2"), _cf("3/2")), "144", "b = 0 : (2x-3)(2x+3)"),
    ReferenceCase(
        "CIB-25",
        "1e12",
        "1e12",
        "-1e12",
        _T,
        (_cf("-1/2", "-1/2", "5"), _cf("-1/2", "1/2", "5")),
        "5e24",
        "Limites du domaine : 10¹²(x² + x - 1)",
    ),
    ReferenceCase(
        "CIB-26", "-1e12", "0", "1e-12", _T, (_cf("-1e-12"), _cf("1e-12")), "4", "Extrêmes : racines ±10⁻¹²"
    ),
    ReferenceCase("CIB-27", "0", "-4", "2", _L, (_cf("0.5"),), None, "Linéaire : -4x + 2 = 0"),
    ReferenceCase("CIB-28", "-5", "0", "0", _D, (_cf("0"),), "0", "Racine double nulle : -5x²"),
    ReferenceCase(
        "CIB-29", "1", "2", "5", _N, (), "-16", "Racines complexes -1 ± 2i (extension informative)"
    ),
)


# ---------------------------------------------------------------------------
# Calcul de l'attendu
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OracleExpectation:
    """Résultat attendu, en rationnels exacts (ou approchés à < 10⁻⁷⁰)."""

    category: Category
    discriminant: Fraction | None = None
    roots: tuple[Fraction, ...] = ()
    exact: bool = True
    error: str | None = None


def sqrt_fraction(value: Fraction, digits: int = ORACLE_DIGITS) -> tuple[Fraction, bool]:
    """Racine carrée d'un rationnel positif par ``math.isqrt``.

    Renvoie ``(approximation, exacte)``. Si la valeur n'est pas le carré d'un
    rationnel, l'erreur relative est < 10^-(digits+1).
    """
    if value < 0:
        raise ValueError("racine carrée d'un nombre négatif")
    num, den = value.numerator, value.denominator
    if num == 0:
        return Fraction(0), True
    rn, rd = isqrt(num), isqrt(den)
    if rn * rn == num and rd * rd == den:
        return Fraction(rn, rd), True
    # √(n/d) = √(n·d)/d ; mise à l'échelle par 10^(2k) avec n·d ≥ 1.
    k = digits + 1
    return Fraction(isqrt(num * den * 10 ** (2 * k)), den * 10**k), False


def _to_fraction(value: object) -> Fraction | None:
    """Conversion EXACTE ; None si le type est ambigu ou non numérique."""
    if isinstance(value, bool) or isinstance(value, float):
        return None  # un flottant n'a pas de valeur décimale non ambiguë
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Decimal):
        return Fraction(value) if value.is_finite() else None
    if isinstance(value, str):
        try:
            number = Decimal(value.strip())
        except ArithmeticError:
            return None
        return Fraction(number) if number.is_finite() else None
    return None


def _in_domain(value: Fraction) -> bool:
    return abs(value) <= _DOMAIN_MAX and (value * _DOMAIN_SCALE).denominator == 1


def expected_result(a: object, b: object, c: object) -> OracleExpectation:
    """Résultat attendu de a·x² + b·x + c = 0, par une méthode indépendante."""
    coefficients = [_to_fraction(v) for v in (a, b, c)]
    if any(v is None for v in coefficients):
        return OracleExpectation(Category.INVALID_INPUT, error="coefficient non numérique ou non fini")
    fa, fb, fc = coefficients  # type: ignore[misc]
    if not all(_in_domain(v) for v in (fa, fb, fc)):
        return OracleExpectation(Category.INVALID_INPUT, error="coefficient hors du domaine")

    if fa == 0:
        if fb == 0:
            return OracleExpectation(Category.INFINITE_SOLUTIONS if fc == 0 else Category.NO_SOLUTION)
        return OracleExpectation(Category.LINEAR_ROOT, roots=(-fc / fb,))

    delta = fb * fb - 4 * fa * fc
    if delta < 0:
        return OracleExpectation(Category.NO_REAL_ROOT, discriminant=delta)
    if delta == 0:
        return OracleExpectation(Category.DOUBLE_REAL_ROOT, discriminant=delta, roots=(-fb / (2 * fa),))
    root, exact = sqrt_fraction(delta)
    # Formule « scolaire » volontairement différente de celle du solveur ;
    # la précision de 120 chiffres absorbe l'annulation (voir docs).
    x1 = (-fb - root) / (2 * fa)
    x2 = (-fb + root) / (2 * fa)
    return OracleExpectation(Category.TWO_REAL_ROOTS, discriminant=delta, roots=tuple(sorted((x1, x2))), exact=exact)


# ---------------------------------------------------------------------------
# Contrôles : résidu, Viète, comparaison
# ---------------------------------------------------------------------------
def relative_residual(a: Fraction, b: Fraction, c: Fraction, x: Fraction) -> Fraction:
    """|a·x² + b·x + c| / (|a|x² + |b||x| + |c|), calculé exactement."""
    scale = abs(a) * x * x + abs(b) * abs(x) + abs(c)
    value = a * x * x + b * x + c
    if scale == 0:
        return Fraction(0) if value == 0 else Fraction(1)
    return abs(value) / scale


def vieta_errors(a: Fraction, b: Fraction, c: Fraction, x1: Fraction, x2: Fraction) -> tuple[Fraction, Fraction]:
    """Erreurs relatives sur x1 + x2 = -b/a et x1·x2 = c/a."""
    sum_scale = abs(x1) + abs(x2)
    prod_scale = abs(x1 * x2)
    sum_err = abs(x1 + x2 + b / a)
    prod_err = abs(x1 * x2 - c / a)
    sum_rel = sum_err / sum_scale if sum_scale else sum_err
    prod_rel = prod_err / prod_scale if prod_scale else prod_err
    return sum_rel, prod_rel


@dataclass(frozen=True)
class Verdict:
    """Décision de l'oracle sur un résultat obtenu."""

    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    max_root_error: Fraction | None = None
    max_residual: Fraction | None = None

    def summary(self) -> str:
        if self.passed:
            return "Conforme : " + ", ".join(self.checks)
        return "Non conforme : " + " ; ".join(self.failures)


def _relative_error(actual: Fraction, expected: Fraction) -> Fraction:
    if expected == 0:
        return abs(actual) / ABS_TOL if actual else Fraction(0)
    return abs(actual - expected) / abs(expected)


def _sci(value: Fraction) -> str:
    return f"{float(value):.1e}" if value else "0"


def compare(expected: OracleExpectation, actual: SolveResult, rel_tol: Fraction = REL_TOL) -> Verdict:
    """Compare un résultat du solveur à l'attendu de l'oracle."""
    checks: list[str] = []
    failures: list[str] = []

    if actual.category is not expected.category:
        failures.append(f"catégorie attendue {expected.category.value}, obtenue {actual.category.value}")
        return Verdict(False, tuple(checks), tuple(failures))
    checks.append("catégorie")

    if expected.discriminant is not None:
        if actual.discriminant is None or Fraction(actual.discriminant) != expected.discriminant:
            failures.append(f"discriminant attendu {expected.discriminant}, obtenu {actual.discriminant}")
        else:
            checks.append("discriminant exact")

    got = [Fraction(x) for x in actual.roots]
    if len(got) != len(expected.roots):
        failures.append(f"{len(expected.roots)} racine(s) attendue(s), {len(got)} obtenue(s)")
        return Verdict(False, tuple(checks), tuple(failures))
    if got != sorted(got):
        failures.append("racines non triées par ordre croissant (contrat S-03)")

    max_error = Fraction(0)
    for index, (value, reference) in enumerate(zip(sorted(got), expected.roots), start=1):
        error = _relative_error(value, reference)
        max_error = max(max_error, error)
        if error > rel_tol:
            failures.append(f"racine {index} : écart relatif {_sci(error)} > tolérance {_sci(rel_tol)}")
    if got:
        checks.append(f"racines (écart ≤ {_sci(max_error)})")

    max_residual: Fraction | None = None
    if got and actual.a is not None and actual.b is not None and actual.c is not None:
        fa, fb, fc = Fraction(actual.a), Fraction(actual.b), Fraction(actual.c)
        max_residual = max(relative_residual(fa, fb, fc, x) for x in got)
        if max_residual > rel_tol:
            failures.append(f"résidu relatif {_sci(max_residual)} > tolérance")
        else:
            checks.append("résidu")
        if expected.category is Category.TWO_REAL_ROOTS:
            sum_err, prod_err = vieta_errors(fa, fb, fc, got[0], got[1])
            if sum_err > rel_tol or prod_err > rel_tol:
                failures.append(f"relations de Viète non vérifiées (somme {_sci(sum_err)}, produit {_sci(prod_err)})")
            else:
                checks.append("Viète")

    return Verdict(not failures, tuple(checks), tuple(failures), max_error if got else None, max_residual)
