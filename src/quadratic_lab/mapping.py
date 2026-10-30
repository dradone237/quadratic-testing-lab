"""Table de correspondance entre les étiquettes Jenny et les coefficients (S-40).

Jenny nomme les dimensions 1, 2, 3… et les valeurs de chaque dimension
a, b, c… (puis A…Z). Ces lettres sont des ÉTIQUETTES DE VALEURS : ``1c``
signifie « 3e valeur de la dimension 1 », c'est-à-dire a = 0 — et non
« coefficient c ». Le décodage passe uniquement par la table explicite
ci-dessous : aucune valeur n'est déduite du nom d'une lettre.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

#: Alphabet des valeurs de Jenny, dans l'ordre (52 valeurs au maximum).
JENNY_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_TOKEN_RE = re.compile(r"([1-9][0-9]*)([a-zA-Z])")


class MappingError(ValueError):
    """Étiquette ou combinaison Jenny incohérente avec la table."""


@dataclass(frozen=True)
class Dimension:
    """Une dimension Jenny = un coefficient et ses valeurs représentatives."""

    index: int
    name: str
    values: tuple[Decimal, ...]

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(JENNY_LETTERS[: len(self.values)])

    def value_of(self, letter: str) -> Decimal:
        try:
            return self.values[self.labels.index(letter)]
        except ValueError:
            raise MappingError(
                f"La valeur « {letter} » n'existe pas dans la dimension {self.index} "
                f"(coefficient {self.name}, étiquettes {''.join(self.labels)})."
            ) from None

    def letter_of(self, value: Decimal) -> str:
        for letter, candidate in zip(self.labels, self.values):
            if candidate == value:
                return letter
        raise MappingError(f"La valeur {value} n'appartient pas au domaine du coefficient {self.name}.")


def _dim(index: int, name: str, values: Sequence[int]) -> Dimension:
    return Dimension(index, name, tuple(Decimal(v) for v in values))


#: Matrice pédagogique : 3 dimensions × 5 valeurs (énoncé, section 7).
DEFAULT_DOMAIN: tuple[Dimension, ...] = (
    _dim(1, "a", (-10, -1, 0, 1, 10)),
    _dim(2, "b", (-10, -2, 0, 2, 10)),
    _dim(3, "c", (-10, -1, 0, 1, 10)),
)


def parse_token(token: str) -> tuple[int, str]:
    """``"1a"`` -> ``(1, "a")`` ; lève ``MappingError`` sinon."""
    match = _TOKEN_RE.fullmatch(token) if isinstance(token, str) else None
    if not match:
        raise MappingError(f"Étiquette Jenny mal formée : {token!r} (attendu : numéro de dimension + lettre).")
    return int(match.group(1)), match.group(2)


def decode_tokens(tokens: Sequence[str], domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> tuple[Decimal, ...]:
    """Convertit une combinaison Jenny (``("1a", "2c", "3d")``) en valeurs numériques."""
    if len(tokens) != len(domain):
        raise MappingError(f"Combinaison {' '.join(tokens)!r} : {len(domain)} dimensions attendues, {len(tokens)} reçues.")
    values = []
    for expected_dim, token in zip(domain, tokens):
        dim_number, letter = parse_token(token)
        if dim_number != expected_dim.index:
            raise MappingError(
                f"Combinaison {' '.join(tokens)!r} : dimension {expected_dim.index} attendue, {dim_number} trouvée."
            )
        values.append(expected_dim.value_of(letter))
    return tuple(values)


def encode_values(values: Sequence[Decimal], domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> tuple[str, ...]:
    """Opération inverse : valeurs numériques -> étiquettes Jenny."""
    if len(values) != len(domain):
        raise MappingError("Nombre de valeurs différent du nombre de dimensions.")
    return tuple(f"{dim.index}{dim.letter_of(value)}" for dim, value in zip(domain, values))


def mapping_rows(domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> list[dict]:
    """Table lisible pour la documentation, la CLI et la GUI."""
    return [
        {"etiquette": f"{dim.index}{letter}", "dimension": dim.index, "coefficient": dim.name, "valeur": str(value)}
        for dim in domain
        for letter, value in zip(dim.labels, dim.values)
    ]
