"""Tests de l'adaptateur Jenny (S-42, S-43).

Deux familles :
- tests unitaires de l'analyse et de la gestion d'erreurs, avec un
  « exécuteur » injecté (doublure de test) pour provoquer délai dépassé,
  code de retour non nul, etc. Ces doublures ne sont utilisées QUE dans les
  tests ; le programme n'a aucun mode de simulation ;
- tests marqués ``jenny`` exécutant le VRAI binaire compilé.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from quadratic_lab.jenny_adapter import (
    ENV_VAR,
    JennyAdapter,
    JennyCombinationError,
    JennyError,
    JennyExecutionError,
    JennyInvalidExecutableError,
    JennyNotFoundError,
    JennyOutputError,
    JennyTimeoutError,
    find_jenny,
    is_jenny_available,
    parse_output,
)

SAMPLE = " 1a 2d 3a \r\n 1b 2b 3e \r\n 1c 2e 3b \r\n 1d 2c 3c \r\n 1e 2a 3d \r\n"


def fake_runner(stdout="", stderr="", returncode=0, exc=None, record=None):
    def run(cmd, **kwargs):
        if record is not None:
            record.append((cmd, kwargs))
        if exc is not None:
            raise exc
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)

    return run


def adapter_with(runner):
    # sys.executable est un fichier existant : il sert uniquement de chemin.
    return JennyAdapter(executable=Path(sys.executable), runner=runner)


# ---------------------------------------------------------------------------
# Analyse de la sortie
# ---------------------------------------------------------------------------
def test_parse_valid_output_with_crlf():
    rows = parse_output(SAMPLE, [5, 5, 5])
    assert rows[0] == ("1a", "2d", "3a")
    assert len(rows) == 5


def test_parse_ignores_blank_lines():
    assert parse_output("\n 1a 2b \n\n 1b 2a \n\n", [2, 2]) == (("1a", "2b"), ("1b", "2a"))


def test_parse_empty_output_is_an_error():
    with pytest.raises(JennyOutputError):
        parse_output("  \r\n", [5, 5, 5])


def test_parse_detects_jenny_error_message_despite_exit_code_zero():
    with pytest.raises(JennyExecutionError, match="99 is too big"):
        parse_output("jenny: dimensions must be smaller than 52.  99 is too big.\n", [5, 99, 5])


def test_parse_detects_uncoverable_tuples():
    with pytest.raises(JennyCombinationError):
        parse_output("Could not cover tuple 1a 2b \n 1a 2a \n", [2, 2])


@pytest.mark.parametrize(
    "line",
    [
        " 1a 2b hello ",
        " 1a 2b 3 ",
        " 1a 2b 3cc ",
        " a1 2b 3c ",
    ],
)
def test_parse_malformed_token(line):
    with pytest.raises(JennyOutputError):
        parse_output(line, [5, 5, 5])


@pytest.mark.parametrize(
    "line",
    [
        " 1a 2b ",  # dimension manquante
        " 1a 2b 3c 4d ",  # dimension en trop
        " 2a 1b 3c ",  # ordre incorrect
        " 1a 2f 3c ",  # f n'existe pas pour une dimension de 5 valeurs
        " 1a 2b 0c ",
    ],
)
def test_parse_incorrect_combination(line):
    with pytest.raises(JennyCombinationError):
        parse_output(line, [5, 5, 5])


# ---------------------------------------------------------------------------
# Construction sûre des arguments
# ---------------------------------------------------------------------------
def test_build_command_uniwise_and_pairwise():
    adapter = adapter_with(fake_runner())
    assert adapter.build_command([5, 5, 5], 1)[1:] == ["-n1", "5", "5", "5"]
    assert adapter.build_command([5, 5, 5], 2, seed=7)[1:] == ["-n2", "5", "5", "5", "-s7"]
    # Anomalie A6 : comparer au chemin résolu par l'adaptateur. Sous Linux, le
    # python d'un venv est un lien symbolique que find_jenny() résout.
    assert adapter.build_command([5, 5, 5], 2)[0] == str(adapter.executable)
    assert adapter.executable == Path(sys.executable).resolve()


@pytest.mark.parametrize(
    "dims,strength,seed",
    [
        ([5, 5, 5], 0, None),
        ([5, 5, 5], 4, None),
        ([5, 1, 5], 2, None),
        ([5, 53, 5], 2, None),
        ([], 1, None),
        ([5, 5, 5], 2, -1),
        ([5, 5, 5], 2, 2**32),
        ([5, True, 5], 2, None),
        ([5, "5; rm -rf /", 5], 2, None),
        ([5, 5, 5], True, None),
    ],
)
def test_build_command_rejects_invalid_parameters(dims, strength, seed):
    with pytest.raises(ValueError):
        adapter_with(fake_runner()).build_command(dims, strength, seed=seed)


def test_run_uses_no_shell_and_a_timeout():
    calls = []
    adapter = adapter_with(fake_runner(stdout=SAMPLE, record=calls))
    run = adapter.run([5, 5, 5], 1)
    cmd, kwargs = calls[0]
    assert isinstance(cmd, list)
    assert kwargs.get("shell", False) is False
    assert kwargs["timeout"] == adapter.timeout
    assert run.rows[0] == ("1a", "2d", "3a")
    assert run.stdout == SAMPLE  # sortie brute conservée telle quelle
    assert run.command_line == "jenny -n1 5 5 5"
    assert run.duration_s >= 0


# ---------------------------------------------------------------------------
# Gestion des erreurs d'exécution
# ---------------------------------------------------------------------------
def test_timeout_is_reported():
    adapter = adapter_with(fake_runner(exc=subprocess.TimeoutExpired(["jenny"], 0.1)))
    with pytest.raises(JennyTimeoutError, match="délai"):
        adapter.run([5, 5, 5], 2)


def test_nonzero_exit_code_is_reported_with_stderr():
    adapter = adapter_with(fake_runner(stdout="", stderr="segfault", returncode=139))
    with pytest.raises(JennyExecutionError) as info:
        adapter.run([5, 5, 5], 2)
    assert "139" in str(info.value)
    assert "segfault" in str(info.value)


def test_os_error_means_invalid_executable():
    adapter = adapter_with(fake_runner(exc=OSError("[WinError 193] not a valid Win32 application")))
    with pytest.raises(JennyInvalidExecutableError):
        adapter.run([5, 5, 5], 2)


def test_verify_accepts_jenny_like_behaviour():
    adapter_with(fake_runner(stdout=" 1a \n 1b \n")).verify()


def test_verify_rejects_other_programs():
    with pytest.raises(JennyInvalidExecutableError):
        adapter_with(fake_runner(stdout="Python 3.12\n")).verify()


def test_verify_rejects_real_non_jenny_executable():
    """Un vrai programme qui n'est pas Jenny (l'interpréteur Python)."""
    with pytest.raises(JennyInvalidExecutableError):
        JennyAdapter(executable=Path(sys.executable)).verify()


def test_all_errors_share_a_base_class():
    for cls in (
        JennyNotFoundError,
        JennyInvalidExecutableError,
        JennyExecutionError,
        JennyTimeoutError,
        JennyOutputError,
        JennyCombinationError,
    ):
        assert issubclass(cls, JennyError)


# ---------------------------------------------------------------------------
# Localisation de l'exécutable
# ---------------------------------------------------------------------------
def test_find_jenny_explicit_missing_path(tmp_path):
    with pytest.raises(JennyNotFoundError):
        find_jenny(tmp_path / "absent.exe")


def test_find_jenny_rejects_directory(tmp_path):
    with pytest.raises(JennyInvalidExecutableError):
        find_jenny(tmp_path)


def test_env_var_pointing_to_missing_file_is_an_error(monkeypatch, tmp_path):
    """Pas de repli silencieux : une configuration explicite fausse est signalée."""
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "nope.exe"))
    with pytest.raises(JennyNotFoundError, match=ENV_VAR):
        find_jenny()
    assert is_jenny_available() is False


def test_adapter_rejects_non_positive_timeout():
    with pytest.raises(ValueError):
        JennyAdapter(executable=Path(sys.executable), timeout=0)


# ---------------------------------------------------------------------------
# Vrai Jenny
# ---------------------------------------------------------------------------
@pytest.mark.jenny
def test_real_jenny_self_test(jenny_adapter):
    jenny_adapter.verify()
    assert jenny_adapter.executable.is_file()
    assert is_jenny_available()


@pytest.mark.jenny
def test_real_jenny_uniwise_rows(jenny_adapter):
    run = jenny_adapter.run([5, 5, 5], 1)
    assert run.returncode == 0
    assert len(run.rows) >= 5
    assert all(len(row) == 3 for row in run.rows)


@pytest.mark.jenny
def test_real_jenny_is_deterministic(jenny_adapter):
    first = jenny_adapter.run([5, 5, 5], 2)
    second = jenny_adapter.run([5, 5, 5], 2)
    assert first.rows == second.rows
    assert first.stdout == second.stdout


@pytest.mark.jenny
def test_real_jenny_reports_errors_on_stdout_with_exit_code_zero(jenny_adapter):
    """Constat S-43 sur le binaire réel : d'où l'analyse du contenu."""
    completed = jenny_adapter.run_raw(["-n2", "5", "99", "5"])
    assert completed.returncode == 0
    assert completed.stdout.startswith("jenny:")
    with pytest.raises(JennyExecutionError):
        parse_output(completed.stdout, [5, 99, 5])


@pytest.mark.jenny
@pytest.mark.parametrize("method,strength", [("uniwise", 1), ("pairwise", 2)])
def test_real_jenny_matches_reference_outputs(jenny_adapter, method, strength):
    """Anomalie A7 : les combinaisons doivent être identiques sous Windows et
    sous Ubuntu (référence figée dans samples/), sinon les chiffres de la
    documentation et de la soutenance ne correspondraient plus."""
    reference = Path(__file__).resolve().parents[1] / "samples" / f"jenny_{method}_raw.txt"
    lines = [line for line in reference.read_text(encoding="utf-8").splitlines() if not line.startswith("#")]
    expected = parse_output("\n".join(lines), [5, 5, 5])
    assert jenny_adapter.run([5, 5, 5], strength).rows == expected


@pytest.mark.jenny
def test_real_jenny_triplewise_is_exhaustive_for_three_dimensions(jenny_adapter):
    run = jenny_adapter.run([5, 5, 5], 3)
    assert len(set(run.rows)) == 125
