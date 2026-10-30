"""Tests de robustesse : erreurs d'exécution, paramètres invalides, fichiers
de sortie, chemins défensifs (section 14 de l'énoncé)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from quadratic_lab import cli, jenny_adapter
from quadratic_lab.cli import EXIT_INVALID, EXIT_JENNY_UNAVAILABLE, EXIT_OK, EXIT_TEST_FAILURE, main
from quadratic_lab.combinatorial import Method, generate, generate_exhaustive, generate_targeted
from quadratic_lab.coverage import covering_cases
from quadratic_lab.jenny_adapter import (
    ENV_VAR,
    JennyCombinationError,
    JennyRun,
    JennyTimeoutError,
    find_jenny,
)
from quadratic_lab.mapping import MappingError, encode_values
from quadratic_lab.models import Category, QuadraticCase, Status
from quadratic_lab.mutation import MUTANTS
from quadratic_lab.oracle import ClosedForm, compare, expected_result, sqrt_fraction
from quadratic_lab.reporting import write_cases_csv, write_validation_report
from quadratic_lab.runner import compare_strategies, run_suite
from quadratic_lab.solver import solve
from quadratic_lab.validation import parse_user_input

D = Decimal


def crashing_solver(a, b, c):
    raise ZeroDivisionError("panne simulée")


class StubAdapter:
    """Doublure de test d'adaptateur (utilisée uniquement dans les tests)."""

    def __init__(self, rows=None, exc=None):
        self.executable = Path(sys.executable)
        self.rows = rows
        self.exc = exc

    def verify(self):
        pass

    def run(self, dimensions, strength, seed=None):
        if self.exc:
            raise self.exc
        return JennyRun(("jenny", f"-n{strength}", "5", "5", "5"), tuple(dimensions), strength, seed,
                        "", "", 0, self.rows, 0.0)


# ---------------------------------------------------------------------------
# Jenny : localisation et sorties incohérentes
# ---------------------------------------------------------------------------
def test_env_var_pointing_to_existing_file_is_used(monkeypatch):
    monkeypatch.setenv(ENV_VAR, sys.executable)
    assert find_jenny() == Path(sys.executable).resolve()


def test_jenny_found_on_path_when_not_in_project(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(jenny_adapter, "default_locations", lambda: [tmp_path / "absent.exe"])
    monkeypatch.setattr(shutil, "which", lambda name: sys.executable if name == "jenny" else None)
    assert find_jenny() == Path(sys.executable).resolve()


def test_jenny_not_found_anywhere(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(jenny_adapter, "default_locations", lambda: [tmp_path / "absent.exe"])
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(jenny_adapter.JennyNotFoundError, match="indisponible"):
        find_jenny()


def test_undecodable_combination_is_reported():
    """Défense en profondeur : une combinaison incohérente avec la table de
    correspondance n'est jamais interprétée de façon ambiguë."""
    with pytest.raises(JennyCombinationError, match="indécodable"):
        generate(Method.PAIRWISE, adapter=StubAdapter(rows=(("1a", "2z", "3a"),)))


def test_compare_strategies_reports_jenny_failure_and_keeps_offline_methods():
    comparison = compare_strategies(adapter=StubAdapter(exc=JennyTimeoutError("trop long")), include_mutation=False)
    assert set(comparison.unavailable) == {Method.UNIWISE, Method.PAIRWISE, Method.TRIPLEWISE}
    assert "trop long" in comparison.unavailable[Method.PAIRWISE]
    assert set(comparison.campaigns) == {Method.EXHAUSTIVE, Method.TARGETED}
    assert comparison.mutation is None


def test_jenny_run_timeout_with_real_slow_process(tmp_path):
    """Délai dépassé sur un vrai processus (l'interpréteur Python qui dort)."""
    adapter = jenny_adapter.JennyAdapter(executable=sys.executable, timeout=0.5)
    with pytest.raises(JennyTimeoutError):
        adapter.run_raw(["-c", "import time; time.sleep(5)"])


# ---------------------------------------------------------------------------
# Oracle, mapping, couverture : cas limites
# ---------------------------------------------------------------------------
def test_closed_form_text():
    assert str(ClosedForm(Fraction(-3))) == "-3"
    assert str(ClosedForm(Fraction(0), Fraction(-1), Fraction(2))) == "-√2"
    assert str(ClosedForm(Fraction(1), Fraction(-2), Fraction(3))) == "1 - 2·√3"
    assert ClosedForm(Fraction(0), Fraction(1), Fraction(9, 4)).is_rational


def test_sqrt_fraction_edge_cases():
    assert sqrt_fraction(Fraction(0)) == (Fraction(0), True)
    assert sqrt_fraction(Fraction(9, 4)) == (Fraction(3, 2), True)
    with pytest.raises(ValueError):
        sqrt_fraction(Fraction(-1))


def test_verdict_summary_for_failure():
    wrong = solve(1, 0, 1)
    verdict = compare(expected_result(D(1), D(0), D(-1)), wrong)
    assert verdict.summary().startswith("Non conforme")


def test_encode_values_wrong_length():
    with pytest.raises(MappingError):
        encode_values((D(1), D(0)))


def test_covering_cases_ignores_out_of_domain_values():
    case = QuadraticCase(case_id="X", method="test", a=D(3), b=D(0), c=D(0))
    mapping = covering_cases([case], strength=1)
    assert mapping[(("b", D(0)),)] == ("X",)
    assert all(ids == () for element, ids in mapping.items() if element[0][0] == "a")


def test_user_input_accepts_non_text_values():
    assert parse_user_input(D("2.5"), "a") == D("2.5")
    assert parse_user_input(3, "a") == D(3)


def test_mutants_reject_invalid_input_like_the_solver():
    for mutant in MUTANTS:
        assert mutant.solve("abc", 1, 1).category is Category.INVALID_INPUT


# ---------------------------------------------------------------------------
# Fichiers de sortie et rapports
# ---------------------------------------------------------------------------
def test_csv_records_solver_crash(tmp_path):
    campaign = run_suite(generate_targeted(), solver=crashing_solver)
    path = write_cases_csv(campaign, tmp_path / "crash.csv")
    text = path.read_text(encoding="utf-8-sig")
    assert Status.ERROR.label in text
    assert "ZeroDivisionError" in text


def test_report_lists_deviations_and_reads_pytest_and_coverage(tmp_path):
    from quadratic_lab.runner import ComparisonResult

    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuite tests="3" failures="0" errors="0" skipped="1" time="0.5"/>', encoding="utf-8")
    cov = tmp_path / "coverage.json"
    cov.write_text(
        json.dumps({"totals": {"covered_lines": 9, "num_statements": 10, "covered_branches": 4,
                               "num_branches": 5, "percent_covered": 86.7}}),
        encoding="utf-8",
    )
    comparison = ComparisonResult(campaigns={Method.TARGETED: run_suite(generate_targeted(), solver=crashing_solver)})
    text = write_validation_report(comparison, tmp_path / "r.md", junit, cov).read_text(encoding="utf-8")
    assert "| Ciblés | CIB-01 | ERREUR |" in text
    assert "3 tests — 2 réussis" in text
    assert "lignes 90.0 %" in text and "branches 80.0 %" in text


def test_output_directory_is_created(tmp_path):
    target = tmp_path / "a" / "b" / "c.csv"
    write_cases_csv(generate_exhaustive(), target)
    assert target.is_file()


# ---------------------------------------------------------------------------
# CLI : paramètres et chemins d'erreur
# ---------------------------------------------------------------------------
def test_cli_rejects_display_digits_out_of_range(capsys):
    assert main(["solve", "--a", "1", "--b", "0", "--c", "-1", "--chiffres", "0"]) == EXIT_INVALID
    assert "--chiffres" in capsys.readouterr().err


def test_cli_test_command_exit_code_on_failures(capsys, monkeypatch, tmp_path):
    real_run_suite = cli.run_suite
    monkeypatch.setattr(cli, "run_suite", lambda suite: real_run_suite(suite, solver=crashing_solver))
    code = main(["test", "--method", "targeted", "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == EXIT_TEST_FAILURE
    assert "ERREUR CIB-01" in out


def test_cli_test_command_without_jenny(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    assert main(["test", "--method", "uniwise", "--output-dir", str(tmp_path)]) == EXIT_JENNY_UNAVAILABLE


def test_cli_mutation_without_jenny_uses_offline_strategies(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    assert main(["mutation"]) == EXIT_OK
    captured = capsys.readouterr()
    assert "Exhaustif" in captured.out and "Uniwise" not in captured.out
    assert "ignoré" in captured.err


def test_cli_compare_without_mutation(capsys, tmp_path, jenny_adapter):
    assert main(["compare", "--sans-mutation", "--output-dir", str(tmp_path)]) == EXIT_OK
    data = json.loads((tmp_path / "comparison.json").read_text(encoding="utf-8"))
    assert "mutation" not in data


def test_cli_jenny_info_without_source_file(capsys, monkeypatch, tmp_path, jenny_adapter):
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    assert main(["jenny"]) == EXIT_OK
    assert "Source" not in capsys.readouterr().out


def test_cli_in_subprocess_with_invalid_input_returns_code_2():
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"), PYTHONIOENCODING="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "quadratic_lab", "solve", "--a", "nan", "--b", "0", "--c", "0"],
        capture_output=True, text=True, encoding="utf-8", env=env, timeout=60, check=False,
    )
    assert completed.returncode == EXIT_INVALID
    assert "NaN" in completed.stderr
