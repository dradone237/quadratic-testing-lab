"""Tests de l'interface en ligne de commande (section 15)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from quadratic_lab.cli import EXIT_INVALID, EXIT_JENNY_UNAVAILABLE, EXIT_OK, main
from quadratic_lab.jenny_adapter import ENV_VAR

ROOT = Path(__file__).resolve().parents[1]


def run(capsys, *argv):
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ---------------------------------------------------------------------------
# solve
# ---------------------------------------------------------------------------
def test_solve_two_roots(capsys):
    code, out, _ = run(capsys, "solve", "--a", "1", "--b", "-3", "--c", "2")
    assert code == EXIT_OK
    assert "TWO_REAL_ROOTS" in out
    assert "Delta = 1" in out
    assert "x1 = 1" in out and "x2 = 2" in out


@pytest.mark.parametrize(
    "a,b,c,needle",
    [
        ("1", "2", "1", "x = -1"),
        ("1", "0", "1", "Aucune racine réelle"),
        ("0", "2", "-4", "x = 2"),
        ("0", "0", "0", "infinité"),
        ("0", "0", "5", "Aucune solution"),
    ],
)
def test_solve_each_category(capsys, a, b, c, needle):
    code, out, _ = run(capsys, "solve", "--a", a, "--b", b, "--c", c)
    assert code == EXIT_OK
    assert needle in out


def test_solve_accepts_french_decimal_comma(capsys):
    code, out, _ = run(capsys, "solve", "--a", "1,5", "--b", "0", "--c", "-6")
    assert code == EXIT_OK
    assert "x1 = -2" in out and "x2 = 2" in out


def test_solve_invalid_input_exit_code_and_message(capsys):
    code, out, err = run(capsys, "solve", "--a", "abc", "--b", "0", "--c", "1")
    assert code == EXIT_INVALID
    assert "invalide" in err.lower()
    assert "coefficient a" in err.lower()


def test_solve_complex_extension(capsys):
    code, out, _ = run(capsys, "solve", "--a", "1", "--b", "2", "--c", "5", "--complexe")
    assert code == EXIT_OK
    assert "-1 - 2i" in out and "-1 + 2i" in out


def test_solve_precision_option(capsys):
    code, out, _ = run(capsys, "solve", "--a", "3", "--b", "0", "--c", "-1", "--chiffres", "30")
    assert code == EXIT_OK
    assert "0.577350269189625764509148780502" in out


def test_solve_missing_argument_is_usage_error(capsys):
    with pytest.raises(SystemExit) as info:
        main(["solve", "--a", "1", "--b", "2"])
    assert info.value.code == 2


def test_help_is_french(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == 0
    out = capsys.readouterr().out
    assert "QUADRATIC TESTING LAB" in out
    for command in ("solve", "generate", "test", "compare", "mutation", "mapping", "jenny", "gui"):
        assert command in out


def test_no_command_prints_help_and_fails(capsys):
    code, out, _ = run(capsys)
    assert code == EXIT_INVALID
    assert "usage" in out.lower()


def test_module_entry_point_runs_in_a_real_process():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "quadratic_lab", "solve", "--a", "1", "--b", "0", "--c", "-1"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "x1 = -1" in completed.stdout


# ---------------------------------------------------------------------------
# mapping, generate, test, compare, mutation, jenny
# ---------------------------------------------------------------------------
def test_mapping_table(capsys):
    code, out, _ = run(capsys, "mapping")
    assert code == EXIT_OK
    assert "1a" in out and "-10" in out and "3e" in out


def test_generate_exhaustive_writes_csv(capsys, tmp_path):
    code, out, _ = run(capsys, "generate", "--method", "exhaustive", "--output-dir", str(tmp_path))
    assert code == EXIT_OK
    assert "125" in out
    assert (tmp_path / "exhaustive_cases.csv").is_file()


def test_test_targeted(capsys, tmp_path):
    code, out, _ = run(capsys, "test", "--method", "targeted", "--output-dir", str(tmp_path))
    assert code == EXIT_OK
    assert "ÉCHEC" not in out
    assert (tmp_path / "targeted_results.json").is_file()


@pytest.mark.jenny
def test_generate_uniwise_shows_real_jenny_command(capsys, tmp_path, jenny_adapter):
    code, out, _ = run(capsys, "generate", "--method", "uniwise", "--output-dir", str(tmp_path))
    assert code == EXIT_OK
    assert "jenny -n1 5 5 5" in out
    assert "1a" in out
    assert (tmp_path / "uniwise_cases.csv").is_file()
    assert (tmp_path / "jenny_uniwise_raw.txt").is_file()


@pytest.mark.jenny
def test_test_pairwise_reports_full_coverage(capsys, tmp_path, jenny_adapter):
    code, out, _ = run(capsys, "test", "--method", "pairwise", "--output-dir", str(tmp_path))
    assert code == EXIT_OK
    assert "75/75" in out
    assert (tmp_path / "pairwise_results.json").is_file()


@pytest.mark.jenny
def test_compare_writes_all_reports(capsys, tmp_path, jenny_adapter):
    code, out, _ = run(capsys, "compare", "--output-dir", str(tmp_path))
    assert code == EXIT_OK
    for name in (
        "uniwise_cases.csv",
        "pairwise_cases.csv",
        "exhaustive_cases.csv",
        "uniwise_results.json",
        "pairwise_results.json",
        "comparison.json",
        "rapport_validation.md",
    ):
        assert (tmp_path / name).is_file(), name
    assert "Uniwise" in out and "Pairwise" in out and "Exhaustif" in out


@pytest.mark.jenny
def test_mutation_command(capsys, jenny_adapter):
    code, out, _ = run(capsys, "mutation")
    assert code == EXIT_OK
    assert "M01" in out and "Score" in out


@pytest.mark.jenny
def test_jenny_info(capsys, jenny_adapter):
    code, out, _ = run(capsys, "jenny")
    assert code == EXIT_OK
    assert "opérationnel" in out


def test_jenny_unavailable_is_declared_not_simulated(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    code, out, err = run(capsys, "generate", "--method", "pairwise", "--output-dir", str(tmp_path))
    assert code == EXIT_JENNY_UNAVAILABLE
    assert "indisponible" in err.lower()
    assert not (tmp_path / "pairwise_cases.csv").exists()


def test_jenny_info_unavailable(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    code, _, err = run(capsys, "jenny")
    assert code == EXIT_JENNY_UNAVAILABLE
    assert "build_jenny" in err


def test_compare_without_jenny_still_reports_offline_methods(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    code, out, err = run(capsys, "compare", "--output-dir", str(tmp_path))
    assert code == EXIT_JENNY_UNAVAILABLE
    assert (tmp_path / "exhaustive_cases.csv").is_file()
    report = (tmp_path / "rapport_validation.md").read_text(encoding="utf-8")
    assert "indisponible" in report.lower()
