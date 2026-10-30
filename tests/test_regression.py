"""Tests de non-régression : un test permanent par défaut corrigé ou piège
identifié (voir reporting.ANOMALIES et docs/RAPPORT_VALIDATION.md)."""

from __future__ import annotations

from decimal import Context, Decimal
from fractions import Fraction

import pytest

from quadratic_lab.jenny_adapter import JennyExecutionError, parse_output
from quadratic_lab.models import Category
from quadratic_lab.reporting import ANOMALIES
from quadratic_lab.solver import format_number, solve

D = Decimal


def test_anomalies_journal_is_documented():
    assert [a["id"] for a in ANOMALIES] == [f"A{i}" for i in range(1, len(ANOMALIES) + 1)]
    for anomaly in ANOMALIES:
        assert anomaly["constat"] and anomaly["cause"] and anomaly["correction"] and anomaly["test"]


def test_a1_decimal_operators_round_to_the_current_context():
    """A1 : piège de la bibliothèque decimal à l'origine de deux faux échecs.
    La valeur de référence doit être calculée dans un contexte explicite."""
    sqrt2 = D(2).sqrt(Context(prec=60))
    assert len((-sqrt2).as_tuple().digits) == 28  # arrondi silencieux à 28 chiffres
    assert len(sqrt2.copy_negate().as_tuple().digits) == 60
    root = solve(1, 0, -2).roots[0]
    assert abs(Fraction(root) - Fraction(sqrt2.copy_negate())) < Fraction(1, 10**48)


def test_a2_out_of_domain_coefficient_is_invalid_not_computed():
    """A2 : b = -3·10¹² est hors domaine ; INVALID_INPUT est la bonne réponse."""
    result = solve("1e12", "-3e12", "2e12")
    assert result.category is Category.INVALID_INPUT
    assert "limites" in result.error


def test_a3_jenny_error_on_stdout_with_exit_code_zero_is_detected():
    """A3 : Jenny écrit ses erreurs sur stdout avec le code 0."""
    with pytest.raises(JennyExecutionError):
        parse_output("jenny: -n, 9-tuples are impossible with only 2 dimensions\n", [2, 2])


def test_a4_markdown_table_cells_are_escaped(tmp_path):
    """A4 : une barre verticale dans une cellule ne doit pas créer de colonne."""
    from quadratic_lab.combinatorial import generate_targeted
    from quadratic_lab.reporting import write_validation_report
    from quadratic_lab.runner import ComparisonResult, run_suite

    comparison = ComparisonResult(campaigns={})
    comparison.campaigns[generate_targeted().method] = run_suite(generate_targeted())
    text = write_validation_report(comparison, tmp_path / "r.md").read_text(encoding="utf-8")
    a2_line = next(line for line in text.splitlines() if line.startswith("| A2 |"))
    assert "\\|x\\|" in a2_line
    # 5 colonnes => 6 séparateurs non échappés.
    assert a2_line.replace("\\|", "").count("|") == 6


def test_design_negative_zero_root():
    """Défaut évité dès la conception : c/q donne -0 quand c = 0 et q < 0."""
    result = solve(1, 2, 0)
    assert result.roots[1] == 0 and not result.roots[1].is_signed()
    assert format_number(result.roots[1]) == "0"


def test_design_sign_of_zero_in_stable_formula():
    """Défaut évité dès la conception (cf. mutant M10) : signe(0) doit valoir
    +1, sinon q = 0 et x2 = c/q divise par zéro quand b = 0."""
    result = solve(1, 0, -1)
    assert result.roots == (D(-1), D(1))


def test_design_tiny_positive_delta_not_rounded_to_zero():
    """Défaut évité dès la conception : en double précision ce Delta vaut 0."""
    a, b, c = 1000000.000000000001, 2000000.0, 999999.999999999999
    assert b * b - 4 * a * c == 0.0  # le piège, constaté en flottants
    result = solve("1000000.000000000001", "2000000", "999999.999999999999")
    assert result.category is Category.TWO_REAL_ROOTS
