#!/usr/bin/env bash
# Démonstration CLI pas à pas sous Linux (plan B si l'interface graphique ne démarre pas).
# Usage : bash samples/demo_cli.sh      (Entrée entre chaque étape)
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=reports/demo
step() {
    local title=$1; shift
    printf '\n\033[36m=== %s ===\033[0m\n' "$title"
    printf '\033[90m> python -m quadratic_lab %s\033[0m\n' "$*"
    "$PY" -m quadratic_lab "$@"
    read -r -p "Entrée pour continuer" _
}
step "1. Équation simple (x-1)(x-2)"            solve --a 1 --b -3 --c 2
step "2. Delta positif : nombre d'or"           solve --a 1 --b -1 --c -1
step "3. Delta nul : racine double"             solve --a 1 --b 2 --c 1
step "4. Delta négatif (+ extension complexe)"  solve --a 1 --b 2 --c 5 --complexe
step "5. Cas a = 0 : premier degré"             solve --a 0 --b 2 --c -4
step "5b. Saisie invalide"                      solve --a abc --b 0 --c 1
step "6. Jenny réel"                            jenny
step "6b. Uniwise : jenny -n1 5 5 5"            test --method uniwise --output-dir "$OUT"
step "7. Pairwise : jenny -n2 5 5 5"            test --method pairwise --output-dir "$OUT"
step "8. Comparaison + mutation"                compare --output-dir "$OUT"
