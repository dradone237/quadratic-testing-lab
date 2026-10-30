"""Analyse de mutation : mesurer la capacité des stratégies à détecter
des défauts réalistes injectés dans des copies du solveur (mutants).

Ces mutants ne servent qu'à ÉVALUER les jeux de tests ; le solveur réel
n'est jamais modifié.
"""

from __future__ import annotations

import pytest

from quadratic_lab.combinatorial import Method, generate_exhaustive, generate_targeted
from quadratic_lab.models import Category
from quadratic_lab.mutation import MUTANTS, run_mutation_analysis
from quadratic_lab.oracle import compare, expected_result
from quadratic_lab.solver import solve


def test_mutant_catalogue():
    ids = [m.mutant_id for m in MUTANTS]
    assert ids == [f"M{i:02d}" for i in range(1, len(MUTANTS) + 1)]
    assert len(MUTANTS) >= 8
    for mutant in MUTANTS:
        assert mutant.title and mutant.description and mutant.trigger


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.mutant_id)
def test_each_mutant_is_not_equivalent(mutant):
    """Chaque mutant doit être faux sur au moins un cas exhaustif ou ciblé,
    sinon ce ne serait pas un défaut mesurable."""
    cases = generate_exhaustive().cases + generate_targeted().cases
    detected = False
    for case in cases:
        try:
            verdict = compare(expected_result(case.a, case.b, case.c), mutant.solve(case.a, case.b, case.c))
        except Exception:  # noqa: BLE001 - un plantage est une détection
            detected = True
            break
        if not verdict.passed:
            detected = True
            break
    assert detected


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.mutant_id)
def test_mutants_agree_with_solver_on_a_neutral_case(mutant):
    """Un mutant reste « proche » du solveur : sur x² - 3x + 2 il peut avoir
    raison ou tort, mais il renvoie bien un résultat structuré."""
    try:
        result = mutant.solve(1, -3, 2)
    except Exception:  # noqa: BLE001
        return
    assert result.category in Category


def test_analysis_on_offline_strategies():
    suites = {Method.EXHAUSTIVE: generate_exhaustive(), Method.TARGETED: generate_targeted()}
    report = run_mutation_analysis(suites)
    every = {m.mutant_id for m in MUTANTS}
    assert report.killed(Method.EXHAUSTIVE) == every
    assert report.killed(Method.TARGETED) == every
    assert report.score(Method.EXHAUSTIVE) == pytest.approx(100.0)
    assert set(report.methods) == {Method.EXHAUSTIVE, Method.TARGETED}
    detail = report.detail(Method.TARGETED, "M05")
    assert detail.killed and detail.killing_cases


def test_real_solver_survives_every_strategy():
    """Témoin : le solveur non muté passe tous les cas (aucun faux positif)."""
    for case in generate_exhaustive().cases + generate_targeted().cases:
        assert compare(expected_result(case.a, case.b, case.c), solve(case.a, case.b, case.c)).passed
