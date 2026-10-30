#!/usr/bin/env bash
# Prépare et vérifie QUADRATIC TESTING LAB sous Ubuntu.
#
#   bash tools/setup_ubuntu.sh --apt    installe d'abord les paquets système manquants (sudo)
#   bash tools/setup_ubuntu.sh          vérifie, crée .venv, compile Jenny, lance les contrôles
#   bash tools/setup_ubuntu.sh --check  vérification seule (ne modifie rien)
set -u
cd "$(dirname "$0")/.."
ROOT=$(pwd)
MODE=${1:-}
ERRORS=0
ok()   { printf '  [OK]  %s\n' "$1"; }
ko()   { printf '  [KO]  %s\n' "$1"; ERRORS=$((ERRORS + 1)); }
info() { printf '\n=== %s ===\n' "$1"; }

info "1. Paquets système"
MISSING=""
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    ok "python3 $(python3 -c 'import platform; print(platform.python_version())') (>= 3.10 requis)"
else
    ko "python3 >= 3.10 absent"; MISSING="$MISSING python3"
fi
python3 -c 'import ensurepip, venv' 2>/dev/null && ok "python3-venv" || { ko "python3-venv absent"; MISSING="$MISSING python3-venv"; }
python3 -c 'import tkinter' 2>/dev/null && ok "python3-tk (interface graphique)" || { ko "python3-tk absent"; MISSING="$MISSING python3-tk"; }
command -v gcc >/dev/null 2>&1 && ok "gcc $(gcc -dumpversion)" || { ko "gcc absent (nécessaire pour compiler Jenny)"; MISSING="$MISSING gcc"; }
command -v git >/dev/null 2>&1 && ok "git" || { ko "git absent"; MISSING="$MISSING git"; }

if [ -n "$MISSING" ]; then
    if [ "$MODE" = "--apt" ]; then
        echo "Installation :$MISSING"
        sudo apt-get update && sudo apt-get install -y $MISSING || exit 1
        exec bash "$0"
    fi
    echo
    echo "Paquets manquants. Installez-les puis relancez ce script :"
    echo "  sudo apt update && sudo apt install -y$MISSING"
    echo "(ou : bash tools/setup_ubuntu.sh --apt)"
    exit 1
fi

if [ "$MODE" = "--check" ]; then
    info "2. Projet (vérification seule)"
    [ -x .venv/bin/python ] && ok ".venv présent" || ko ".venv absent (lancer sans --check)"
    [ -x tools/jenny/bin/jenny ] && ok "Jenny compilé" || ko "Jenny non compilé (lancer sans --check)"
    exit $((ERRORS > 0))
fi

info "2. Environnement Python (.venv)"
[ -x .venv/bin/python ] || python3 -m venv .venv || { ko "création du .venv impossible"; exit 1; }
ok ".venv : $(.venv/bin/python --version)"
if .venv/bin/python -m pip install --quiet --upgrade pip && .venv/bin/python -m pip install --quiet -e ".[dev]"; then
    ok "dépendances de test installées (pytest, pytest-cov, hypothesis)"
    PYTEST_OK=1
else
    ko "pip install a échoué (pas d'Internet ?). Le programme fonctionne quand même : il n'utilise que la bibliothèque standard."
    PYTEST_OK=0
fi

info "3. Jenny"
if sh tools/jenny/build_jenny.sh; then ok "Jenny compilé et vérifié"; else ko "compilation de Jenny"; fi

info "4. Contrôles du programme"
export PYTHONPATH="$ROOT/src"
.venv/bin/python -m quadratic_lab jenny >/dev/null 2>&1 && ok "python -m quadratic_lab jenny" || ko "Jenny inutilisable par le programme"
.venv/bin/python -m quadratic_lab solve --a 1 --b -3 --c 2 | grep -q "x2 = 2" && ok "résolution x² - 3x + 2 = 0 -> 1 et 2" || ko "résolution"
.venv/bin/python -m quadratic_lab test --method pairwise --output-dir /tmp/qtl_check | grep -q "75/75" \
    && ok "campagne Pairwise réelle : 75/75 paires" || ko "campagne Pairwise"
if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && .venv/bin/python -c 'import tkinter; r = tkinter.Tk(); r.destroy()' 2>/dev/null; then
    ok "affichage graphique disponible (python launch_gui.py)"
else
    ko "affichage graphique indisponible : utiliser la CLI (bash samples/demo_cli.sh)"
fi

if [ "$PYTEST_OK" = "1" ]; then
    info "5. Suite de tests (profil rapide)"
    HYPOTHESIS_PROFILE=rapide .venv/bin/python -m pytest -q -p no:cacheprovider > /tmp/qtl_pytest.log 2>&1
    PYTEST_CODE=$?
    tail -3 /tmp/qtl_pytest.log
    [ "$PYTEST_CODE" -eq 0 ] && ok "tous les tests passent" || ko "des tests échouent (détail : /tmp/qtl_pytest.log)"
fi

echo
if [ "$ERRORS" -eq 0 ]; then
    echo "ENVIRONNEMENT PRÊT. Démonstration : source .venv/bin/activate && python launch_gui.py"
else
    echo "$ERRORS contrôle(s) en échec : voir les lignes [KO] ci-dessus."
fi
exit $((ERRORS > 0))
