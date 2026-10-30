"""Solveur robuste de a·x² + b·x + c = 0 (S-20 à S-26).

Politique numérique :
- arithmétique ``Decimal`` à 50 chiffres significatifs, arrondi au plus proche pair ;
- discriminant EXACT (signal ``Inexact`` piégé) : son signe est donc certain ;
- formule stable ``q = -(b + signe(b)·√Δ)/2``, ``x1 = q/a``, ``x2 = c/q``.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    localcontext,
)

from .models import Category, SolveResult
from .validation import DISPLAY_DIGITS, INTERNAL_PRECISION, InvalidCoefficientError, validate_coefficients

#: Contexte du discriminant : toute perte d'exactitude lève une exception.
EXACT_CONTEXT = Context(
    prec=INTERNAL_PRECISION,
    rounding=ROUND_HALF_EVEN,
    traps=[Inexact, InvalidOperation, DivisionByZero, Overflow],
)
#: Contexte de calcul des racines : arrondi autorisé, opérations invalides piégées.
WORK_CONTEXT = Context(
    prec=INTERNAL_PRECISION,
    rounding=ROUND_HALF_EVEN,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)


class NumericalError(ArithmeticError):
    """Erreur numérique explicite (jamais masquée par un arrondi silencieux)."""


def compute_discriminant(a: Decimal, b: Decimal, c: Decimal) -> Decimal:
    """Calcule Δ = b² - 4ac exactement, ou lève ``NumericalError``."""
    try:
        with localcontext(EXACT_CONTEXT):
            return b * b - 4 * a * c
    except Inexact as exc:
        raise NumericalError(
            f"Le discriminant ne peut pas être calculé exactement avec {INTERNAL_PRECISION} chiffres : "
            "coefficients hors du domaine validé."
        ) from exc
    except DecimalException as exc:  # pragma: no cover - impossible pour des décimaux finis
        raise NumericalError(f"Erreur numérique dans le calcul du discriminant : {exc!r}") from exc


def _canonical(value: Decimal) -> Decimal:
    """Supprime le zéro négatif (S-04)."""
    return Decimal(0) if value.is_zero() else value


def _solve_degenerate(a: Decimal, b: Decimal, c: Decimal) -> SolveResult:
    """Cas a = 0 : premier degré, 0 = 0 ou c = 0."""
    if b.is_zero():
        category = Category.INFINITE_SOLUTIONS if c.is_zero() else Category.NO_SOLUTION
        return SolveResult(category, a, b, c)
    with localcontext(WORK_CONTEXT):
        root = -c / b
    return SolveResult(Category.LINEAR_ROOT, a, b, c, roots=(_canonical(root),))


def _solve_quadratic(a: Decimal, b: Decimal, c: Decimal) -> SolveResult:
    """Cas a ≠ 0 : discriminant exact puis formule stable."""
    delta = compute_discriminant(a, b, c)
    with localcontext(WORK_CONTEXT):
        two_a = 2 * a
        if delta < 0:
            real = _canonical(-b / two_a)
            imaginary = abs((-delta).sqrt() / two_a)
            return SolveResult(
                Category.NO_REAL_ROOT,
                a,
                b,
                c,
                discriminant=delta,
                complex_roots=((real, -imaginary), (real, imaginary)),
            )
        if delta == 0:
            return SolveResult(Category.DOUBLE_REAL_ROOT, a, b, c, discriminant=delta, roots=(_canonical(-b / two_a),))
        # Delta > 0 : |b| + √Δ > 0, donc q ≠ 0 et les deux divisions sont sûres.
        # signe(0) = +1 : avec signe(0) = 0, q serait nul quand b = 0.
        sign = Decimal(1) if b >= 0 else Decimal(-1)
        q = -(b + sign * delta.sqrt()) / 2
        x1 = q / a
        x2 = c / q
    roots = tuple(sorted((_canonical(x1), _canonical(x2))))
    return SolveResult(Category.TWO_REAL_ROOTS, a, b, c, discriminant=delta, roots=roots)


def solve(a: object, b: object, c: object) -> SolveResult:
    """Résout a·x² + b·x + c = 0.

    Les saisies invalides donnent la catégorie ``INVALID_INPUT`` avec un
    message ; aucune exception n'est levée pour une entrée invalide.
    """
    try:
        a_dec, b_dec, c_dec = validate_coefficients(a, b, c)
    except InvalidCoefficientError as exc:
        return SolveResult(Category.INVALID_INPUT, None, None, None, error=str(exc))
    try:
        if a_dec.is_zero():
            return _solve_degenerate(a_dec, b_dec, c_dec)
        return _solve_quadratic(a_dec, b_dec, c_dec)
    except DecimalException as exc:  # pragma: no cover - exclu par la validation (S-24)
        raise NumericalError(f"Erreur numérique inattendue : {exc!r}") from exc


# ---------------------------------------------------------------------------
# Affichage (S-25)
# ---------------------------------------------------------------------------
def format_number(value: Decimal, digits: int = DISPLAY_DIGITS) -> str:
    """Arrondit à ``digits`` chiffres significatifs (au plus proche pair)."""
    if value.is_zero():
        return "0"
    ctx = Context(prec=digits, rounding=ROUND_HALF_EVEN)
    rounded = ctx.plus(value).normalize(ctx)
    exponent = rounded.adjusted()
    if -7 < exponent < digits:
        return format(rounded, "f")
    return format(rounded, "E")


def format_exact(value: Decimal) -> str:
    """Écriture exacte (sans arrondi) d'un décimal, par exemple le discriminant."""
    if value.is_zero():
        return "0"
    ctx = Context(prec=max(len(value.as_tuple().digits), 1))
    normalized = value.normalize(ctx)
    exponent = normalized.adjusted()
    if -7 < exponent < 30:
        return format(normalized, "f")
    return format(normalized, "E")


def format_roots(roots: Sequence[Decimal], digits: int = DISPLAY_DIGITS) -> list[str]:
    """Formate des racines en augmentant la précision si deux racines
    distinctes s'afficheraient identiquement."""
    for current in range(digits, INTERNAL_PRECISION + 1):
        shown = [format_number(root, current) for root in roots]
        if len(set(shown)) == len(shown):
            return shown
    return [format_number(root, INTERNAL_PRECISION) for root in roots]  # pragma: no cover


def format_complex(real: Decimal, imaginary: Decimal, digits: int = DISPLAY_DIGITS) -> str:
    """Écrit ``re ± im·i`` (extension complexe, informative)."""
    sign = "-" if imaginary < 0 else "+"
    return f"{format_number(real, digits)} {sign} {format_number(abs(imaginary), digits)}i"
