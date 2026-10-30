"""Tests d'intégration : Jenny -> décodage -> solveur -> oracle -> rapport."""

from __future__ import annotations

import csv
import json

import pytest

from quadratic_lab.combinatorial import Method, generate, generate_exhaustive, generate_targeted
from quadratic_lab.models import Status
from quadratic_lab.mutation import MUTANTS
from quadratic_lab.reporting import CSV_COLUMNS, export_campaign, export_comparison
from quadratic_lab.runner import compare_strategies, run_campaign, run_suite


def test_exhaustive_125_cases_all_pass():
    suite = generate_exhaustive()
    assert len(suite.cases) == 125
    assert len({(c.a, c.b, c.c) for c in suite.cases}) == 125
    assert suite.generator == "itertools.product"
    assert suite.command is None
    campaign = run_suite(suite)
    assert campaign.passed == 125
    assert campaign.coverage[3].is_complete
    assert campaign.categories.missing == ()  # les 6 catégories mathématiques


def test_targeted_suite_all_pass_and_covers_every_branch():
    campaign = run_suite(generate_targeted())
    assert campaign.total >= 20
    assert campaign.failed == 0 and campaign.errors == 0
    assert campaign.categories.missing == ()
    assert [c.case_id for c in campaign.suite.cases][:8] == [f"CIB-{i:02d}" for i in range(1, 9)]


@pytest.mark.jenny
def test_full_pipeline_uniwise_to_report(jenny_adapter, tmp_path):
    campaign = run_campaign(Method.UNIWISE, adapter=jenny_adapter)
    files = export_campaign(campaign, tmp_path)
    names = {path.name for path in files}
    assert {"uniwise_cases.csv", "uniwise_results.json", "jenny_uniwise_raw.txt"} <= names

    with open(tmp_path / "uniwise_cases.csv", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert list(rows[0].keys()) == CSV_COLUMNS
    assert len(rows) == campaign.total
    assert all(row["statut"] == "RÉUSSI" for row in rows)
    assert rows[0]["combinaison_jenny"] == campaign.suite.cases[0].jenny_combination

    data = json.loads((tmp_path / "uniwise_results.json").read_text(encoding="utf-8"))
    assert data["methode"] == "uniwise"
    assert data["commande_jenny"] == "jenny -n1 5 5 5"
    assert data["statistiques"]["reussis"] == campaign.passed
    assert data["couverture"]["1-way"]["pourcentage"] == 100.0
    assert len(data["cas"]) == campaign.total

    raw = (tmp_path / "jenny_uniwise_raw.txt").read_text(encoding="utf-8")
    assert "jenny -n1 5 5 5" in raw
    assert campaign.suite.raw_output.strip().splitlines()[0].strip() in raw


@pytest.mark.jenny
def test_pairwise_output_extends_uniwise_output(jenny_adapter):
    """Constat sur Jenny : il couvre d'abord les valeurs seules, puis les
    paires. Les premières lignes de -n2 sont donc celles de -n1."""
    uni = generate(Method.UNIWISE, adapter=jenny_adapter)
    pair = generate(Method.PAIRWISE, adapter=jenny_adapter)
    assert [c.jenny_combination for c in pair.cases[: len(uni.cases)]] == [c.jenny_combination for c in uni.cases]


@pytest.mark.jenny
def test_compare_strategies_and_export(jenny_adapter, tmp_path):
    comparison = compare_strategies(adapter=jenny_adapter)
    assert comparison.unavailable == {}
    uni = comparison.campaigns[Method.UNIWISE]
    pair = comparison.campaigns[Method.PAIRWISE]
    exh = comparison.campaigns[Method.EXHAUSTIVE]
    assert uni.total < pair.total < exh.total == 125
    assert pair.coverage[2].is_complete and not uni.coverage[2].is_complete
    for campaign in comparison.campaigns.values():
        assert campaign.failed == 0 and campaign.errors == 0

    # Analyse de mutation : l'exhaustif et les cas ciblés détectent tous les mutants.
    mutation = comparison.mutation
    assert mutation is not None
    assert mutation.killed(Method.EXHAUSTIVE) == {m.mutant_id for m in MUTANTS}
    assert mutation.killed(Method.TARGETED) == {m.mutant_id for m in MUTANTS}
    assert mutation.killed(Method.UNIWISE) <= mutation.killed(Method.PAIRWISE)

    files = export_comparison(comparison, tmp_path)
    names = {path.name for path in files}
    assert {"comparison.json", "rapport_validation.md", "exhaustive_cases.csv", "pairwise_results.json"} <= names
    data = json.loads((tmp_path / "comparison.json").read_text(encoding="utf-8"))
    assert data["methodes"]["pairwise"]["nombre_cas"] == pair.total
    assert data["methodes"]["exhaustive"]["couverture"]["3-way"]["pourcentage"] == 100.0
    report = (tmp_path / "rapport_validation.md").read_text(encoding="utf-8")
    assert "jenny -n2 5 5 5" in report
    assert f"| Pairwise | {pair.total} |" in report


def test_runner_records_solver_exceptions_as_errors():
    def crashing_solver(a, b, c):
        raise ZeroDivisionError("division par zéro simulée")

    campaign = run_suite(generate_targeted(), solver=crashing_solver)
    assert campaign.errors == campaign.total
    outcome = campaign.outcomes[0]
    assert outcome.status is Status.ERROR
    assert "ZeroDivisionError" in outcome.error
