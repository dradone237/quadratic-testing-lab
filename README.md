# QUADRATIC TESTING LAB

**Résolution et vérification robuste des équations du second degré avec Jenny,
Uniwise et Pairwise Testing.**

Projet du cours *Vérification, Validation et Tests Logiciels*. Il répond à
deux questions :

1. **Mathématique** : le programme calcule-t-il correctement les solutions de
   `a·x² + b·x + c = 0` ?
2. **Génie logiciel** : comment le démontrer par une stratégie de tests
   rigoureuse, y compris pour les situations anormales ?

## Résultats mesurés (validation finale du 30/10/2026)

| Stratégie | Générateur | Cas | 1-way | 2-way | 3-way | Catégories | Réussis | Mutants tués |
|---|---|---|---|---|---|---|---|---|
| Uniwise | `jenny -n1 5 5 5` | 5 | 100 % | 20 % | 4 % | 4/6 | 5/5 | 6/10 |
| Pairwise | `jenny -n2 5 5 5` | 28 | 100 % | **100 % (75/75)** | 22,4 % | 5/6 | 28/28 | 8/10 |
| 3-way | `jenny -n3 5 5 5` | 125 | 100 % | 100 % | 100 % | 6/6 | 125/125 | 10/10 |
| Exhaustif | `itertools.product` | 125 | 100 % | 100 % | 100 % | 6/6 | 125/125 | 10/10 |
| Ciblés | calcul à la main | 29 | — | — | — | 6/6 | 29/29 | 10/10 |

- **Suite pytest** : 478 tests, 478 réussis, 0 échec, 0 ignoré, sous Windows 11 **et** sous Ubuntu 24.04 (clone frais).
- **Couverture du code métier** (GUI exclue) : 100 % des lignes (1424/1424)
  et 100 % des branches (396/396). GUI mesurée à part : 90 %.
- **Constat clé** : Pairwise couvre les 75 paires, mais n'atteint jamais
  « 0 = 0 » (seul le triplet (0, 0, 0) y mène) et laisse survivre deux défauts
  injectés qui dépendent de trois valeurs à la fois (M05, M10). D'où les cas
  ciblés et les tests par propriétés.

Détails : [docs/RAPPORT_VALIDATION.md](docs/RAPPORT_VALIDATION.md) et
`reports/rapport_validation.md` (généré automatiquement).

## Installation sous Ubuntu (machine de soutenance)

```bash
git clone https://github.com/dradone237/quadratic-testing-lab.git
cd quadratic-testing-lab
bash tools/setup_ubuntu.sh --apt     # paquets système + .venv + Jenny + contrôles + tests
source .venv/bin/activate
python launch_gui.py                 # démonstration
```

`setup_ubuntu.sh` affiche une ligne `[OK]`/`[KO]` par contrôle et se termine
par « ENVIRONNEMENT PRÊT » : python3 ≥ 3.10, python3-venv, python3-tk, gcc,
git, création du `.venv`, compilation et vérification de Jenny
(reproductibilité avec Windows), résolution d'une équation, campagne Pairwise
réelle (75/75), affichage graphique, suite pytest. `--check` vérifie sans rien
modifier. Validé sur un clone frais sous Ubuntu 24.04.5 (WSL).

Le programme lui-même n'utilise **que la bibliothèque standard** : sans
Internet, il fonctionne avec `PYTHONPATH=src python3 -m quadratic_lab …` ;
seuls les tests ont besoin de pytest et Hypothesis (`pip`).

## Installation (Windows, PowerShell)

```powershell
cd quadratic-testing-lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build-jenny]"

# Compiler Jenny (source officielle vérifiée par SHA-256, compilateur zig cc du .venv)
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1
.\.venv\Scripts\python.exe -m quadratic_lab jenny        # vérification
```

GCC (MSYS2) peut remplacer `zig cc` : voir [docs/GUIDE_JENNY.md](docs/GUIDE_JENNY.md).
Dans la suite, `python` désigne `.\.venv\Scripts\python.exe` (ou activez le
venv avec `.\.venv\Scripts\Activate.ps1`).

## Utilisation

```powershell
python -m quadratic_lab --help
python -m quadratic_lab solve --a 1 --b -3 --c 2
python -m quadratic_lab solve --a 1,5 --b 0 --c -6          # virgule décimale acceptée
python -m quadratic_lab solve --a 1 --b 2 --c 5 --complexe  # extension complexe
python -m quadratic_lab mapping                             # étiquettes Jenny -> valeurs
python -m quadratic_lab generate --method uniwise           # jenny -n1 5 5 5
python -m quadratic_lab generate --method pairwise          # jenny -n2 5 5 5
python -m quadratic_lab generate --method exhaustive        # 125 cas
python -m quadratic_lab test --method uniwise
python -m quadratic_lab test --method pairwise
python -m quadratic_lab compare                             # tout + rapports dans reports/
python -m quadratic_lab mutation                            # score de mutation par stratégie
python launch_gui.py                                        # interface graphique
```

Méthodes : `uniwise`, `pairwise`, `triplewise`, `exhaustive`, `targeted`.
Codes de sortie : 0 succès, 1 échec de tests, 2 saisie invalide,
3 Jenny indisponible (aucune simulation n'est faite).

## Validation complète

```powershell
powershell -ExecutionPolicy Bypass -File tools\run_validation.ps1
```

Produit dans `reports/` : `pytest_junit.xml`, `coverage.json`, `htmlcov/`,
`uniwise_cases.csv`, `pairwise_cases.csv`, `exhaustive_cases.csv`,
`*_results.json`, `comparison.json`, `jenny_*_raw.txt` (sortie brute de Jenny)
et `rapport_validation.md`. Les CSV utilisent le séparateur `;` et l'UTF-8
avec BOM (ouverture directe dans Excel).

## Choix techniques essentiels

- **Domaine d'entrée** : `|x| ≤ 10¹²`, au plus 12 décimales. Dans ce domaine,
  le discriminant est calculé **exactement** avec 50 chiffres (`Inexact`
  piégé) : son signe est certain, sans tolérance.
- **Formule stable** `q = -(b + signe(b)·√Δ)/2`, `x1 = q/a`, `x2 = c/q`, avec
  `signe(0) = +1`.
- **Oracle indépendant** : rationnels exacts (`Fraction`) et `math.isqrt` à
  120 chiffres, formule différente, 29 cas calculés à la main, résidus et
  relations de Viète. Tolérance relative 10⁻⁴⁰ justifiée.
- **Jenny réel** : compilé depuis la source officielle (domaine public),
  exécuté par `subprocess.run` sans shell, avec délai maximal. Sa sortie brute
  est conservée.
- **Couverture combinatoire recalculée indépendamment** de Jenny, à partir des
  valeurs décodées.

## Architecture

```
src/quadratic_lab/
  models.py         catégories, SolveResult, QuadraticCase
  validation.py     domaine d'entrée, virgule française
  solver.py         solveur Decimal robuste
  oracle.py         oracle indépendant + 29 cas de référence
  mapping.py        étiquettes Jenny <-> coefficients
  jenny_adapter.py  exécution réelle de Jenny
  combinatorial.py  uniwise / pairwise / 3-way / exhaustif / ciblés
  coverage.py       couverture t-wise et catégories
  runner.py         campagnes et comparaison
  mutation.py       10 mutants pour évaluer les stratégies
  reporting.py      CSV, JSON, Markdown
  cli.py            interface en ligne de commande
  gui/              Tkinter : Résolution, Uniwise, Pairwise, Comparaison, Démonstration
tests/              18 fichiers de tests (unitaires, intégration, propriétés, GUI, …)
tools/jenny/        source officielle, scripts de compilation, provenance
docs/               cours, équation, Jenny, stratégies, plan de tests, rapport, soutenance
samples/            traces de référence et démonstration CLI
```

## Documentation

| Document | Contenu |
|---|---|
| [docs/SPECIFICATIONS.md](docs/SPECIFICATIONS.md) | Contrat du programme (règles S-xx) |
| [docs/EXPLICATION_EQUATION.md](docs/EXPLICATION_EQUATION.md) | Mathématiques et précision numérique |
| [docs/COURS_RESUME.md](docs/COURS_RESUME.md) | Résumé de cours VVT relié au projet |
| [docs/GUIDE_JENNY.md](docs/GUIDE_JENNY.md) | Jenny : installation, compilation, usage |
| [docs/UNIWISE_PAIRWISE.md](docs/UNIWISE_PAIRWISE.md) | Uniwise, Pairwise, exhaustif, ciblés, exemple manuel |
| [docs/PLAN_DE_TESTS.md](docs/PLAN_DE_TESTS.md) | Plan de tests et traçabilité |
| [docs/RAPPORT_VALIDATION.md](docs/RAPPORT_VALIDATION.md) | Rapport de validation commenté |
| [docs/GUIDE_SOUTENANCE.md](docs/GUIDE_SOUTENANCE.md) | Présentation orale de 5 minutes |

## Limites

Pairwise ne couvre pas tous les triplets. Aucune stratégie de test ne prouve
l'absence de défauts. La validation des racines irrationnelles repose sur
une tolérance (10⁻⁴⁰). Compilé tel quel sous Linux 64 bits, Jenny produirait
d'autres combinaisons (taille de `unsigned long`) : `build_jenny.sh` applique
un correctif de portabilité documenté qui rend les sorties identiques à Windows.
