"""Campagne Pairwise réelle : ``jenny -n2 5 5 5`` (section 9 de l'énoncé)."""

from __future__ import annotations

import pytest

from quadratic_lab.combinatorial import Method, generate
from quadratic_lab.coverage import pairwise_coverage, triplewise_coverage, uniwise_coverage
from quadratic_lab.models import Category
from quadratic_lab.runner import run_suite

pytestmark = pytest.mark.jenny


@pytest.fixture(scope="module")
def suite(jenny_adapter):
    return generate(Method.PAIRWISE, adapter=jenny_adapter)


@pytest.fixture(scope="module")
def campaign(suite):
    return run_suite(suite)


def test_generated_by_real_jenny_with_n2(suite):
    assert suite.command == "jenny -n2 5 5 5"
    assert suite.cases[0].case_id == "PAIR-001"


def test_all_75_pairs_are_covered(suite):
    report = pairwise_coverage(suite.cases)
    assert report.total == 75
    assert report.covered_count == 75
    assert report.missing == ()
    assert report.is_complete
    assert report.by_dimensions() == {("a", "b"): (25, 25), ("a", "c"): (25, 25), ("b", "c"): (25, 25)}


def test_size_between_lower_bound_and_exhaustive(suite):
    # Borne inférieure : 5 × 5 = 25 (les deux plus grandes dimensions).
    assert 25 <= len(suite.cases) < 125


def test_pairwise_implies_uniwise(suite):
    assert uniwise_coverage(suite.cases).is_complete


def test_pairwise_does_not_cover_all_triples(suite):
    triples = triplewise_coverage(suite.cases)
    assert not triples.is_complete
    assert triples.covered_count <= len(suite.cases)


def test_all_pairwise_cases_pass_the_oracle(campaign, suite):
    assert campaign.total == len(suite.cases)
    assert campaign.failed == 0 and campaign.errors == 0
    assert campaign.coverage[2].is_complete


def test_category_coverage_is_consistent_with_cases(campaign, suite):
    """100 % Pairwise ne garantit PAS toutes les branches du solveur :
    0 = 0 (infinité de solutions) n'est atteint que par le triplet (0, 0, 0)."""
    has_triple_zero = any(case.a == 0 and case.b == 0 and case.c == 0 for case in suite.cases)
    covered = campaign.categories.covered
    assert (Category.INFINITE_SOLUTIONS in covered) == has_triple_zero
