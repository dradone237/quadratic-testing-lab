"""Campagne Uniwise réelle : ``jenny -n1 5 5 5`` (section 8 de l'énoncé)."""

from __future__ import annotations

import pytest

from quadratic_lab.combinatorial import Method, generate
from quadratic_lab.coverage import uniwise_coverage
from quadratic_lab.mapping import decode_tokens
from quadratic_lab.models import Status
from quadratic_lab.runner import run_suite

pytestmark = pytest.mark.jenny


@pytest.fixture(scope="module")
def suite(jenny_adapter):
    return generate(Method.UNIWISE, adapter=jenny_adapter)


def test_generated_by_real_jenny_with_n1(suite):
    assert suite.method is Method.UNIWISE
    assert suite.command == "jenny -n1 5 5 5"
    assert suite.generator == "jenny"
    assert suite.executable and suite.executable.endswith(("jenny.exe", "jenny"))
    assert suite.raw_output.strip()


def test_every_raw_line_becomes_exactly_one_case(suite):
    raw_lines = [line for line in suite.raw_output.splitlines() if line.strip()]
    assert len(raw_lines) == len(suite.cases)
    for line_no, (line, case) in enumerate(zip(raw_lines, suite.cases), start=1):
        assert case.jenny_line == line_no
        assert case.jenny_combination == " ".join(line.split())
        # Décodage indépendant depuis la ligne brute.
        assert decode_tokens(tuple(line.split())) == (case.a, case.b, case.c)


def test_case_identifiers(suite):
    assert [case.case_id for case in suite.cases] == [f"UNI-{i:03d}" for i in range(1, len(suite.cases) + 1)]
    assert all(case.method == "uniwise" for case in suite.cases)


def test_minimum_size_and_full_1way_coverage(suite):
    assert len(suite.cases) >= 5  # borne inférieure : 5 valeurs par dimension
    report = uniwise_coverage(suite.cases)
    assert report.is_complete, report.missing
    assert report.percent == 100.0


def test_all_uniwise_cases_pass_the_oracle(suite):
    campaign = run_suite(suite)
    assert campaign.total == len(suite.cases)
    assert campaign.failed == 0 and campaign.errors == 0
    assert all(outcome.status is Status.PASS for outcome in campaign.outcomes)
    assert campaign.coverage[1].is_complete


def test_other_seed_still_covers_all_values(jenny_adapter):
    other = generate(Method.UNIWISE, adapter=jenny_adapter, seed=12345)
    assert other.command == "jenny -n1 5 5 5 -s12345"
    assert uniwise_coverage(other.cases).is_complete
