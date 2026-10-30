"""Tests des rapports (section 17) : formats, contenu et absence d'invention."""

from __future__ import annotations

import csv
import json

from quadratic_lab.combinatorial import Method, generate_exhaustive, generate_targeted
from quadratic_lab.reporting import (
    CSV_COLUMNS,
    read_code_coverage,
    read_pytest_summary,
    write_cases_csv,
    write_validation_report,
)
from quadratic_lab.runner import ComparisonResult, run_suite

EXPECTED_COLUMNS = [
    "id",
    "methode",
    "combinaison_jenny",
    "a",
    "b",
    "c",
    "discriminant",
    "categorie_attendue",
    "categorie_obtenue",
    "racines_attendues",
    "racines_calculees",
    "comparaison",
    "statut",
    "message_erreur",
]


def test_csv_columns_match_the_assignment():
    assert CSV_COLUMNS == EXPECTED_COLUMNS


def test_csv_for_generated_but_not_executed_cases(tmp_path):
    path = write_cases_csv(generate_exhaustive(), tmp_path / "x.csv")
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM UTF-8 pour Excel sous Windows
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert len(rows) == 125
    assert rows[0]["statut"] == "NON EXÉCUTÉ"
    assert rows[0]["categorie_obtenue"] == ""
    assert rows[0]["categorie_attendue"]  # l'oracle est connu avant exécution


def test_csv_for_executed_campaign(tmp_path):
    campaign = run_suite(generate_targeted())
    path = write_cases_csv(campaign, tmp_path / "t.csv")
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert rows[0]["id"] == "CIB-01"
    assert rows[0]["racines_calculees"] == "-1 | 1"
    assert rows[0]["statut"] == "RÉUSSI"
    assert rows[0]["comparaison"].startswith("Conforme")


def test_validation_report_with_unavailable_jenny(tmp_path):
    campaigns = {
        Method.EXHAUSTIVE: run_suite(generate_exhaustive()),
        Method.TARGETED: run_suite(generate_targeted()),
    }
    comparison = ComparisonResult(
        campaigns=campaigns,
        unavailable={Method.UNIWISE: "Jenny introuvable", Method.PAIRWISE: "Jenny introuvable"},
        mutation=None,
    )
    path = write_validation_report(comparison, tmp_path / "r.md")
    text = path.read_text(encoding="utf-8")
    for number, title in enumerate(
        [
            "Objectifs des tests",
            "Partitions des coefficients",
            "Commandes Jenny exécutées",
            "Combinaisons générées",
            "Cas réellement exécutés",
            "Résultats",
            "Couverture",
            "Écarts détectés",
            "Anomalies corrigées",
            "Limites de la stratégie",
        ],
        start=1,
    ):
        assert f"## {number}. {title}" in text
    assert "Jenny introuvable" in text
    assert "| Exhaustif | 125 |" in text
    # Résultats pytest non fournis : signalé, jamais inventé.
    assert "non disponible" in text.lower()


def test_read_pytest_summary(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<?xml version="1.0"?><testsuites><testsuite name="pytest" errors="0" failures="1" '
        'skipped="2" tests="10" time="1.5"></testsuite></testsuites>',
        encoding="utf-8",
    )
    summary = read_pytest_summary(junit)
    assert summary == {"tests": 10, "echecs": 1, "erreurs": 0, "ignores": 2, "reussis": 7, "duree_s": 1.5}
    assert read_pytest_summary(tmp_path / "absent.xml") is None


def test_read_code_coverage(tmp_path):
    cov = tmp_path / "coverage.json"
    cov.write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": 95,
                    "num_statements": 100,
                    "covered_branches": 45,
                    "num_branches": 50,
                    "percent_covered": 93.3,
                }
            }
        ),
        encoding="utf-8",
    )
    data = read_code_coverage(cov)
    assert data["lignes_pourcentage"] == 95.0
    assert data["branches_pourcentage"] == 90.0
    assert read_code_coverage(tmp_path / "absent.json") is None
