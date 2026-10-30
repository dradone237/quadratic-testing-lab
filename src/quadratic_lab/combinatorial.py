"""Génération des jeux de tests (S-41, S-44).

- Uniwise / Pairwise / 3-way : exécution du VRAI Jenny (``-n1``, ``-n2``, ``-n3``).
- Exhaustif : ``itertools.product`` (125 combinaisons de référence).
- Ciblés : cas de référence calculés à la main (``oracle.REFERENCE_CASES``).
"""

from __future__ import annotations

import itertools
import time
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .jenny_adapter import JennyAdapter, JennyCombinationError, JennyRun
from .mapping import DEFAULT_DOMAIN, Dimension, MappingError, decode_tokens, encode_values
from .models import QuadraticCase
from .oracle import REFERENCE_CASES


class Method(str, Enum):
    UNIWISE = "uniwise"
    PAIRWISE = "pairwise"
    TRIPLEWISE = "triplewise"
    EXHAUSTIVE = "exhaustive"
    TARGETED = "targeted"

    @property
    def strength(self) -> int | None:
        """Force d'interaction demandée à Jenny (None si Jenny n'est pas utilisé)."""
        return {Method.UNIWISE: 1, Method.PAIRWISE: 2, Method.TRIPLEWISE: 3}.get(self)

    @property
    def uses_jenny(self) -> bool:
        return self.strength is not None

    @property
    def label(self) -> str:
        return {
            Method.UNIWISE: "Uniwise",
            Method.PAIRWISE: "Pairwise",
            Method.TRIPLEWISE: "3-way (Jenny -n3)",
            Method.EXHAUSTIVE: "Exhaustif",
            Method.TARGETED: "Ciblés",
        }[self]

    @property
    def prefix(self) -> str:
        return {
            Method.UNIWISE: "UNI",
            Method.PAIRWISE: "PAIR",
            Method.TRIPLEWISE: "TRI",
            Method.EXHAUSTIVE: "EXH",
            Method.TARGETED: "CIB",
        }[self]


@dataclass(frozen=True)
class GeneratedSuite:
    """Jeu de cas généré, avec la preuve de sa provenance."""

    method: Method
    cases: tuple[QuadraticCase, ...]
    generator: str
    command: str | None
    raw_output: str | None
    duration_s: float
    executable: str | None = None
    jenny_run: JennyRun | None = None


def generate(
    method: Method | str,
    adapter: JennyAdapter | None = None,
    domain: Sequence[Dimension] = DEFAULT_DOMAIN,
    seed: int | None = None,
) -> GeneratedSuite:
    """Génère le jeu de cas d'une méthode. Pour les méthodes Jenny, lève une
    ``JennyError`` si Jenny est indisponible (aucune simulation)."""
    method = Method(method)
    if method is Method.EXHAUSTIVE:
        return generate_exhaustive(domain)
    if method is Method.TARGETED:
        return generate_targeted()
    return _generate_with_jenny(method, adapter, domain, seed)


def _generate_with_jenny(
    method: Method, adapter: JennyAdapter | None, domain: Sequence[Dimension], seed: int | None
) -> GeneratedSuite:
    start = time.perf_counter()
    adapter = adapter or JennyAdapter()
    adapter.verify()
    run = adapter.run([len(dim.values) for dim in domain], method.strength, seed)
    cases = []
    for line_no, tokens in enumerate(run.rows, start=1):
        try:
            a, b, c = decode_tokens(tokens, domain)
        except MappingError as exc:
            raise JennyCombinationError(f"Combinaison Jenny n°{line_no} indécodable : {exc}") from exc
        cases.append(
            QuadraticCase(
                case_id=f"{method.prefix}-{line_no:03d}",
                method=method.value,
                a=a,
                b=b,
                c=c,
                jenny_combination=" ".join(tokens),
                jenny_line=line_no,
                generator=run.command_line,
                labels=tuple(tokens),
            )
        )
    return GeneratedSuite(
        method=method,
        cases=tuple(cases),
        generator="jenny",
        command=run.command_line,
        raw_output=run.stdout,
        duration_s=time.perf_counter() - start,
        executable=str(adapter.executable),
        jenny_run=run,
    )


def generate_exhaustive(domain: Sequence[Dimension] = DEFAULT_DOMAIN) -> GeneratedSuite:
    """Produit cartésien complet : 5 × 5 × 5 = 125 cas."""
    start = time.perf_counter()
    cases = []
    for index, values in enumerate(itertools.product(*(dim.values for dim in domain)), start=1):
        a, b, c = values
        cases.append(
            QuadraticCase(
                case_id=f"EXH-{index:03d}",
                method=Method.EXHAUSTIVE.value,
                a=a,
                b=b,
                c=c,
                generator="itertools.product",
                labels=encode_values(values, domain),
            )
        )
    return GeneratedSuite(
        method=Method.EXHAUSTIVE,
        cases=tuple(cases),
        generator="itertools.product",
        command=None,
        raw_output=None,
        duration_s=time.perf_counter() - start,
    )


def generate_targeted() -> GeneratedSuite:
    """Cas ciblés des branches mathématiques, établis à la main."""
    start = time.perf_counter()
    cases = tuple(
        QuadraticCase(
            case_id=ref.case_id,
            method=Method.TARGETED.value,
            a=Decimal(ref.a),
            b=Decimal(ref.b),
            c=Decimal(ref.c),
            generator="manuel (calcul analytique)",
            description=ref.description,
        )
        for ref in REFERENCE_CASES
    )
    return GeneratedSuite(
        method=Method.TARGETED,
        cases=cases,
        generator="manuel (calcul analytique)",
        command=None,
        raw_output=None,
        duration_s=time.perf_counter() - start,
    )
