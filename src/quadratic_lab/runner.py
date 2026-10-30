"""Exécution des campagnes : cas -> solveur -> oracle -> verdict -> statistiques."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from .combinatorial import GeneratedSuite, Method, generate
from .coverage import CategoryCoverage, CoverageReport, category_coverage, interaction_coverage
from .jenny_adapter import JennyAdapter, JennyError
from .mapping import DEFAULT_DOMAIN
from .models import QuadraticCase, SolveResult, Status
from .mutation import MutationReport, run_mutation_analysis
from .oracle import OracleExpectation, Verdict, compare, expected_result
from .solver import solve

Solver = Callable[[object, object, object], SolveResult]

#: Ordre de présentation des stratégies dans les comparaisons.
COMPARISON_ORDER = (Method.UNIWISE, Method.PAIRWISE, Method.TRIPLEWISE, Method.EXHAUSTIVE, Method.TARGETED)


@dataclass(frozen=True)
class CaseOutcome:
    case: QuadraticCase
    expected: OracleExpectation
    actual: SolveResult | None
    verdict: Verdict | None
    status: Status
    duration_s: float
    error: str | None = None


@dataclass(frozen=True)
class CampaignResult:
    suite: GeneratedSuite
    outcomes: tuple[CaseOutcome, ...]
    duration_s: float
    coverage: dict[int, CoverageReport]
    categories: CategoryCoverage

    @property
    def method(self) -> Method:
        return self.suite.method

    @property
    def total(self) -> int:
        return len(self.outcomes)

    def _count(self, status: Status) -> int:
        return sum(1 for outcome in self.outcomes if outcome.status is status)

    @property
    def passed(self) -> int:
        return self._count(Status.PASS)

    @property
    def failed(self) -> int:
        return self._count(Status.FAIL)

    @property
    def errors(self) -> int:
        return self._count(Status.ERROR)

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.passed == self.total


def run_case(case: QuadraticCase, solver: Solver = solve) -> CaseOutcome:
    """Exécute un cas et le juge avec l'oracle indépendant."""
    expected = expected_result(case.a, case.b, case.c)
    start = time.perf_counter()
    try:
        actual = solver(case.a, case.b, case.c)
    except Exception as exc:  # noqa: BLE001 - toute exception est consignée comme ERREUR
        return CaseOutcome(case, expected, None, None, Status.ERROR, time.perf_counter() - start,
                           f"{type(exc).__name__}: {exc}")
    duration = time.perf_counter() - start
    verdict = compare(expected, actual)
    status = Status.PASS if verdict.passed else Status.FAIL
    return CaseOutcome(case, expected, actual, verdict, status, duration, None if verdict.passed else verdict.summary())


def run_suite(suite: GeneratedSuite, solver: Solver = solve) -> CampaignResult:
    start = time.perf_counter()
    outcomes = tuple(run_case(case, solver) for case in suite.cases)
    duration = time.perf_counter() - start
    coverage = {t: interaction_coverage(suite.cases, DEFAULT_DOMAIN, t) for t in (1, 2, 3)}
    categories = category_coverage(outcome.expected.category for outcome in outcomes)
    return CampaignResult(suite, outcomes, duration, coverage, categories)


def run_campaign(method: Method | str, adapter: JennyAdapter | None = None, seed: int | None = None) -> CampaignResult:
    return run_suite(generate(method, adapter=adapter, seed=seed))


@dataclass
class ComparisonResult:
    campaigns: dict[Method, CampaignResult]
    unavailable: dict[Method, str] = field(default_factory=dict)
    mutation: MutationReport | None = None


def compare_strategies(adapter: JennyAdapter | None = None, include_mutation: bool = True) -> ComparisonResult:
    """Exécute toutes les stratégies. Si Jenny manque, les méthodes Jenny sont
    déclarées indisponibles (avec la raison) et les autres restent exécutées."""
    reason = ""
    if adapter is None:
        try:
            adapter = JennyAdapter()
            adapter.verify()
        except JennyError as exc:
            adapter, reason = None, str(exc)
    campaigns: dict[Method, CampaignResult] = {}
    unavailable: dict[Method, str] = {}
    for method in COMPARISON_ORDER:
        if method.uses_jenny and adapter is None:
            unavailable[method] = reason
            continue
        try:
            campaigns[method] = run_campaign(method, adapter=adapter)
        except JennyError as exc:
            unavailable[method] = str(exc)
    mutation = run_mutation_analysis({m: c.suite for m, c in campaigns.items()}) if include_mutation else None
    return ComparisonResult(campaigns, unavailable, mutation)
