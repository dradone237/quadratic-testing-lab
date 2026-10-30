"""Structures de données du projet (contrat des résultats, S-01 à S-04)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class Category(str, Enum):
    """Catégories de résultat mutuellement exclusives."""

    TWO_REAL_ROOTS = "TWO_REAL_ROOTS"
    DOUBLE_REAL_ROOT = "DOUBLE_REAL_ROOT"
    NO_REAL_ROOT = "NO_REAL_ROOT"
    LINEAR_ROOT = "LINEAR_ROOT"
    INFINITE_SOLUTIONS = "INFINITE_SOLUTIONS"
    NO_SOLUTION = "NO_SOLUTION"
    INVALID_INPUT = "INVALID_INPUT"

    @property
    def label(self) -> str:
        return CATEGORY_LABELS[self]


CATEGORY_LABELS = {
    Category.TWO_REAL_ROOTS: "Deux racines réelles distinctes",
    Category.DOUBLE_REAL_ROOT: "Une racine réelle double",
    Category.NO_REAL_ROOT: "Aucune racine réelle",
    Category.LINEAR_ROOT: "Équation du premier degré (une solution)",
    Category.INFINITE_SOLUTIONS: "Infinité de solutions",
    Category.NO_SOLUTION: "Aucune solution (équation impossible)",
    Category.INVALID_INPUT: "Saisie invalide",
}

#: Les six catégories mathématiques (toutes sauf la saisie invalide).
MATH_CATEGORIES = tuple(c for c in Category if c is not Category.INVALID_INPUT)


class Status(str, Enum):
    """Statut d'exécution d'un cas de test."""

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    NOT_RUN = "NOT_RUN"

    @property
    def label(self) -> str:
        return {
            Status.PASS: "RÉUSSI",
            Status.FAIL: "ÉCHEC",
            Status.ERROR: "ERREUR",
            Status.NOT_RUN: "NON EXÉCUTÉ",
        }[self]


def _fmt(value: Decimal | None) -> str:
    return "?" if value is None else format(value.normalize() if value != 0 else Decimal(0), "f")


@dataclass(frozen=True)
class SolveResult:
    """Résultat structuré et immuable d'une résolution."""

    category: Category
    a: Decimal | None
    b: Decimal | None
    c: Decimal | None
    discriminant: Decimal | None = None
    roots: tuple[Decimal, ...] = ()
    #: Extension facultative (Delta < 0) : paires (partie réelle, partie imaginaire).
    complex_roots: tuple[tuple[Decimal, Decimal], ...] = ()
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.category is not Category.INVALID_INPUT

    def explanation(self) -> str:
        """Explication pédagogique du cas mathématique, en français."""
        cat = self.category
        delta = _fmt(self.discriminant)
        if cat is Category.INVALID_INPUT:
            return f"Saisie invalide : {self.error}. Aucun calcul n'est effectué."
        if cat is Category.INFINITE_SOLUTIONS:
            return (
                "a = 0, b = 0 et c = 0 : l'équation devient 0 = 0, toujours vraie. "
                "Elle admet une infinité de solutions réelles."
            )
        if cat is Category.NO_SOLUTION:
            return (
                f"a = 0 et b = 0 mais c = {_fmt(self.c)} ≠ 0 : l'équation devient "
                f"{_fmt(self.c)} = 0, ce qui est impossible. Aucune solution."
            )
        if cat is Category.LINEAR_ROOT:
            return (
                f"a = 0 et b ≠ 0 : c'est une équation du premier degré b·x + c = 0, "
                f"dont l'unique solution est x = -c/b."
            )
        if cat is Category.TWO_REAL_ROOTS:
            return (
                f"a ≠ 0 et Delta = b² - 4ac = {delta} > 0 : l'équation admet deux racines "
                "réelles distinctes, calculées par la formule stable q = -(b + signe(b)·√Delta)/2, "
                "x1 = q/a, x2 = c/q."
            )
        if cat is Category.DOUBLE_REAL_ROOT:
            return f"a ≠ 0 et Delta = 0 : l'équation admet une racine double x = -b/(2a)."
        return (
            f"a ≠ 0 et Delta = {delta} < 0 : l'équation n'admet aucune racine réelle "
            "(deux racines complexes conjuguées)."
        )

    def to_dict(self) -> dict:
        """Représentation JSON exacte (les décimaux sont écrits en texte)."""

        def text(value: Decimal | None) -> str | None:
            return None if value is None else str(value)

        return {
            "category": self.category.value,
            "label": self.category.label,
            "a": text(self.a),
            "b": text(self.b),
            "c": text(self.c),
            "discriminant": text(self.discriminant),
            "roots": [str(r) for r in self.roots],
            "complex_roots": [[str(re), str(im)] for re, im in self.complex_roots],
            "error": self.error,
        }


@dataclass(frozen=True)
class QuadraticCase:
    """Un cas de test exécutable, avec sa traçabilité de génération (S-44)."""

    case_id: str
    method: str
    a: Decimal
    b: Decimal
    c: Decimal
    jenny_combination: str | None = None
    jenny_line: int | None = None
    generator: str = ""
    description: str = ""
    labels: tuple[str, ...] = field(default=())

    @property
    def coefficients(self) -> tuple[Decimal, Decimal, Decimal]:
        return (self.a, self.b, self.c)
