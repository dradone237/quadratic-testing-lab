"""Validation des coefficients (S-10 à S-14).

Le domaine d'entrée est choisi pour que le discriminant soit toujours
calculable EXACTEMENT avec 50 chiffres significatifs (voir S-21) :

- |x| ≤ 10¹² ;
- au plus 12 chiffres après la virgule.

Aucune saisie invalide n'est convertie silencieusement en zéro.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation

#: Valeur absolue maximale d'un coefficient.
MAX_ABS_COEFFICIENT = Decimal("1e12")
#: Nombre maximal de chiffres après la virgule.
MAX_DECIMAL_PLACES = 12
#: Longueur maximale d'une saisie texte.
MAX_INPUT_LENGTH = 100
#: Précision interne des calculs (chiffres significatifs).
INTERNAL_PRECISION = 50
#: Précision d'affichage par défaut (chiffres significatifs).
DISPLAY_DIGITS = 15

# Chiffres ASCII uniquement ([0-9] et non \d, qui accepte les chiffres Unicode).
_NUMBER_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_FRENCH_COMMA_RE = re.compile(r"[+-]?[0-9]*,[0-9]+(?:[eE][+-]?[0-9]+)?")
_SPECIAL_WORDS = {"nan": "NaN", "snan": "NaN", "inf": "infini", "infinity": "infini"}


class InvalidCoefficientError(ValueError):
    """Coefficient rejeté ; ``coefficient`` est le nom (a, b ou c)."""

    def __init__(self, coefficient: str, value: object, reason: str) -> None:
        self.coefficient = coefficient
        self.value = value
        self.reason = reason
        shown = repr(value) if len(repr(value)) <= 40 else repr(value)[:37] + "..."
        super().__init__(f"Coefficient {coefficient} invalide ({shown}) : {reason}")


def _decimal_places(value: Decimal) -> int:
    """Nombre de décimales significatives, calculé sans arrondi."""
    _, digits, exponent = value.as_tuple()
    digits = list(digits)
    while exponent < 0 and len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    return max(0, -exponent)


def parse_coefficient(value: object, name: str = "coefficient") -> Decimal:
    """Convertit ``value`` en ``Decimal`` du domaine, ou lève une erreur explicite."""
    if value is None:
        raise InvalidCoefficientError(name, value, "valeur manquante")
    if isinstance(value, bool):
        raise InvalidCoefficientError(name, value, "un booléen n'est pas un coefficient numérique")

    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        if math.isnan(value):
            raise InvalidCoefficientError(name, value, "NaN n'est pas un nombre")
        if math.isinf(value):
            raise InvalidCoefficientError(name, value, "valeur infinie interdite")
        number = Decimal(repr(value))
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidCoefficientError(name, value, "saisie vide")
        if len(text) > MAX_INPUT_LENGTH:
            raise InvalidCoefficientError(name, value, f"longueur supérieure à {MAX_INPUT_LENGTH} caractères")
        special = _SPECIAL_WORDS.get(text.lstrip("+-").lower())
        if special == "NaN":
            raise InvalidCoefficientError(name, value, "NaN n'est pas un nombre")
        if special == "infini":
            raise InvalidCoefficientError(name, value, "valeur infinie interdite")
        if not _NUMBER_RE.fullmatch(text):
            raise InvalidCoefficientError(
                name, value, "format numérique invalide (attendu : chiffres, point décimal, exposant facultatif)"
            )
        try:
            number = Decimal(text)
        except InvalidOperation as exc:  # pragma: no cover - exclu par l'expression régulière
            raise InvalidCoefficientError(name, value, "format numérique invalide") from exc
    else:
        raise InvalidCoefficientError(name, value, f"type non pris en charge ({type(value).__name__})")

    if number.is_nan():
        raise InvalidCoefficientError(name, value, "NaN n'est pas un nombre")
    if number.is_infinite():
        raise InvalidCoefficientError(name, value, "valeur infinie interdite")
    if abs(number) > MAX_ABS_COEFFICIENT:
        raise InvalidCoefficientError(name, value, "valeur hors limites (|x| ≤ 10^12)")
    if number.is_zero():
        return Decimal(0)  # forme canonique : ni -0 ni 0E-5
    if _decimal_places(number) > MAX_DECIMAL_PLACES:
        raise InvalidCoefficientError(
            name, value, f"trop de décimales (au plus {MAX_DECIMAL_PLACES} chiffres après la virgule)"
        )
    return number


def normalize_user_text(text: str, name: str = "coefficient") -> str:
    """Prépare une saisie humaine (CLI, GUI) : virgule décimale française, signe moins typographique."""
    cleaned = text.strip().replace("−", "-")
    if "," in cleaned:
        if "." in cleaned or cleaned.count(",") > 1 or not _FRENCH_COMMA_RE.fullmatch(cleaned):
            raise InvalidCoefficientError(
                name, text, "séparateur décimal ambigu (utilisez une seule virgule OU un seul point)"
            )
        cleaned = cleaned.replace(",", ".")
    return cleaned


def parse_user_input(text: str, name: str = "coefficient") -> Decimal:
    """Analyse une saisie utilisateur en acceptant la virgule décimale."""
    if not isinstance(text, str):
        return parse_coefficient(text, name)
    return parse_coefficient(normalize_user_text(text, name), name)


def validate_coefficients(a: object, b: object, c: object) -> tuple[Decimal, Decimal, Decimal]:
    """Valide les trois coefficients ; l'erreur nomme le coefficient fautif."""
    return (parse_coefficient(a, "a"), parse_coefficient(b, "b"), parse_coefficient(c, "c"))
