# CLAUDE.md — QUADRATIC TESTING LAB

Projet universitaire (cours Vérification, Validation et Tests) : solveur robuste
de `a·x² + b·x + c = 0` et démonstration de sa vérification avec Jenny
(Uniwise `-n1`, Pairwise `-n2`), exhaustif, cas ciblés, oracle indépendant,
Hypothesis et analyse de mutation.

**Ne jamais modifier le projet voisin `../huffman-python`.** Pas de `git init`
ni d'opération sur un dépôt distant sans autorisation explicite.

## Commandes

```powershell
.\.venv\Scripts\python.exe -m pytest                       # suite complète
$env:HYPOTHESIS_PROFILE="rapide"; .\.venv\Scripts\python.exe -m pytest   # plus rapide
.\.venv\Scripts\python.exe -m pytest -m jenny              # tests du vrai Jenny
powershell -ExecutionPolicy Bypass -File tools\run_validation.ps1   # pytest + couverture + rapports
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1 -Force   # recompiler Jenny
.\.venv\Scripts\python.exe -m quadratic_lab --help
.\.venv\Scripts\python.exe launch_gui.py
```

Ubuntu : `bash tools/setup_ubuntu.sh --apt`, `bash tools/run_validation.sh`,
`sh tools/jenny/build_jenny.sh` (correctif de portabilité ub4/sb4 32 bits
appliqué à une copie quand `unsigned long` fait 64 bits — voir tools/jenny/SOURCE.md).

## Architecture (src/quadratic_lab)

- `validation.py` domaine d'entrée (|x| ≤ 1e12, ≤ 12 décimales) et virgule française
- `solver.py` solveur Decimal 50 chiffres, Δ exact (Inexact piégé), formule stable
- `oracle.py` oracle INDÉPENDANT (Fraction + isqrt) ; ne doit importer ni solver ni validation (test AST)
- `mapping.py` étiquettes Jenny (1a…) ↔ valeurs ; `jenny_adapter.py` exécution réelle de Jenny
- `combinatorial.py` génération ; `coverage.py` couverture t-wise indépendante de Jenny
- `runner.py` campagnes ; `mutation.py` mutants ; `reporting.py` CSV/JSON/Markdown ; `cli.py`
- `gui/` Tkinter : appelle les mêmes modules, jamais de copie d'algorithme

## Conventions

- Sorties utilisateur en français ; code et identifiants en anglais.
- Jenny n'est jamais simulé : sans exécutable, lever une `JennyError` (code CLI 3).
- Piège `decimal` : les opérateurs (`-x`, `+`, `/`) arrondissent au contexte
  courant (28 chiffres par défaut). Calculer les références dans un `Context`
  explicite (anomalie A1).
- Tout défaut corrigé : ajouter une entrée à `reporting.ANOMALIES` et un test
  dans `tests/test_regression.py`.
- Statistiques des rapports : toujours calculées depuis les résultats exécutés.
