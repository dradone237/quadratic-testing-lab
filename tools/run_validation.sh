#!/usr/bin/env bash
# Validation complète sous Linux : pytest + couverture, puis comparaison des stratégies.
# Usage : bash tools/run_validation.sh
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || { echo "Environnement .venv absent : bash tools/setup_ubuntu.sh" >&2; exit 1; }
[ -x tools/jenny/bin/jenny ] || sh tools/jenny/build_jenny.sh || exit 1
mkdir -p reports
echo "=== Suite de tests (pytest + couverture du code métier) ==="
"$PY" -m pytest --cov=quadratic_lab --cov-branch --cov-report=term-missing \
    --cov-report=json:reports/coverage.json --cov-report=html:reports/htmlcov \
    --junitxml=reports/pytest_junit.xml
PYTEST_CODE=$?
echo "=== Comparaison des stratégies et rapports ==="
"$PY" -m quadratic_lab compare
COMPARE_CODE=$?
echo "Code pytest : $PYTEST_CODE ; code compare : $COMPARE_CODE"
exit $(( PYTEST_CODE > COMPARE_CODE ? PYTEST_CODE : COMPARE_CODE ))
