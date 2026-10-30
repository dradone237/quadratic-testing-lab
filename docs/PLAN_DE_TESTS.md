# Plan de tests — QUADRATIC TESTING LAB

Ce plan décrit **ce qui est testé, avec quelles données, comment et avec quel
résultat attendu**. Il s'appuie sur les règles numérotées `S-xx` de
[SPECIFICATIONS.md](SPECIFICATIONS.md).

## 1. Objectifs

1. **Vérification** (« construit-on le produit correctement ? ») : chaque
   fonction respecte sa spécification (discriminant exact, formule stable,
   validation des entrées, décodage Jenny, calcul de couverture).
2. **Validation** (« construit-on le bon produit ? ») : le programme résout
   correctement l'équation dans tous les cas mathématiques (Δ > 0, Δ = 0,
   Δ < 0, a = 0) et rejette proprement les saisies invalides.
3. **Évaluation des stratégies de test** : comparer Uniwise, Pairwise, 3-way,
   exhaustif et cas ciblés par la couverture, les catégories atteintes et la
   capacité à détecter des défauts injectés (analyse de mutation).

## 2. Périmètre

| Inclus | Exclu |
|---|---|
| Solveur, validation, oracle, adaptateur Jenny, table de correspondance, générateurs, couverture, exécution des campagnes, mutation, rapports, CLI, GUI | Correction interne de Jenny lui-même (outil tiers : seules sa sortie et sa couverture sont vérifiées) ; racines complexes (extension informative, hors critère de validation) |

## 3. Environnement de test

| Élément | Version |
|---|---|
| Système | Windows 11 Pro |
| Python | 3.12.10 (environnement virtuel `.venv`) |
| pytest | 9.2.0 |
| pytest-cov | 7.1.0 |
| hypothesis | 6.170.14 |
| Compilateur de Jenny | zig cc 0.16.0 (paquet PyPI `ziglang`) |
| Jenny | source officielle, SHA-256 `b93222…cb23`, compilée en `-O3` |

Hypothesis utilise un profil **reproductible** (`derandomize=True`,
200 exemples par propriété) défini dans `tests/conftest.py`. Le profil
`rapide` (30 exemples) sert pendant le développement.

## 4. Données de test

### 4.1 Matrice pédagogique (génération combinatoire)

Trois dimensions de cinq valeurs (classes d'équivalence : grand négatif,
petit négatif, zéro, petit positif, grand positif) :

| Coefficient | Valeurs (étiquettes Jenny a…e) |
|---|---|
| a | -10, -1, 0, 1, 10 |
| b | -10, -2, 0, 2, 10 |
| c | -10, -1, 0, 1, 10 |

Pour b, ±2 remplace ±1 afin de pouvoir produire Δ = 0 (b² = 4ac avec a = c = ±1).

Jeux dérivés : Uniwise (`jenny -n1 5 5 5`), Pairwise (`jenny -n2 5 5 5`),
3-way (`jenny -n3 5 5 5`), exhaustif (`itertools.product`, 125 cas).

### 4.2 Cas ciblés calculés à la main (CIB-01 à CIB-29)

Définis dans `src/quadratic_lab/oracle.py` (`REFERENCE_CASES`). Les attendus
sont obtenus par factorisation ou par la formule résolvante appliquée à la
main, et écrits sous forme close `p + q·√r`.

| ID | a | b | c | Catégorie attendue | Racines attendues | Δ | Objet |
|---|---|---|---|---|---|---|---|
| CIB-01 | 1 | 0 | -1 | TWO_REAL_ROOTS | -1 ; 1 | 4 | CAS 1 de l'énoncé |
| CIB-02 | 1 | 2 | 1 | DOUBLE_REAL_ROOT | -1 | 0 | CAS 2 |
| CIB-03 | 1 | 0 | 1 | NO_REAL_ROOT | — | -4 | CAS 3 |
| CIB-04 | 0 | 2 | -4 | LINEAR_ROOT | 2 | — | CAS 4 |
| CIB-05 | 0 | 0 | 0 | INFINITE_SOLUTIONS | — | — | CAS 5 |
| CIB-06 | 0 | 0 | 5 | NO_SOLUTION | — | — | CAS 6 |
| CIB-07 | 1 | -3 | 2 | TWO_REAL_ROOTS | 1 ; 2 | 1 | CAS 7 |
| CIB-08 | -1 | 0 | 1 | TWO_REAL_ROOTS | -1 ; 1 | 4 | CAS 8 |
| CIB-09 | 0.5 | -1.5 | 1 | TWO_REAL_ROOTS | 1 ; 2 | 0.25 | décimaux |
| CIB-10 | 2.5 | 0 | -10 | TWO_REAL_ROOTS | -2 ; 2 | 100 | décimaux |
| CIB-11 | -2 | -4 | 6 | TWO_REAL_ROOTS | -3 ; 1 | 64 | négatifs |
| CIB-12 | 1 | 0 | -2 | TWO_REAL_ROOTS | -√2 ; √2 | 8 | irrationnel |
| CIB-13 | 1 | -1 | -1 | TWO_REAL_ROOTS | (1 - √5)/2 ; (1 + √5)/2 | 5 | nombre d'or |
| CIB-14 | 1e-12 | 0 | -1e-12 | TWO_REAL_ROOTS | -1 ; 1 | 4e-24 | très petits |
| CIB-15 | 1e11 | -3e11 | 2e11 | TWO_REAL_ROOTS | 1 ; 2 | 1e22 | très grands |
| CIB-16 | 1e-12 | 1e12 | 1e-12 | TWO_REAL_ROOTS | -5·10²³ ∓ ½·√(10⁴⁸ - 4) | 10²⁴ - 4·10⁻²⁴ | annulation catastrophique |
| CIB-17 | 1 | 2 | 0.999999999999 | TWO_REAL_ROOTS | -1.000001 ; -0.999999 | 4e-12 | Δ proche de 0 (positif) |
| CIB-18 | 1000000.000000000001 | 2000000 | 999999.999999999999 | TWO_REAL_ROOTS | -1 ; -999999999999999999/1000000000000000001 | 4e-24 | Δ minuscule, ne doit pas devenir 0 |
| CIB-19 | 1 | 2 | 1.000000000001 | NO_REAL_ROOT | — | -4e-12 | Δ proche de 0 (négatif) |
| CIB-20 | 9 | -6 | 1 | DOUBLE_REAL_ROOT | 1/3 | 0 | racine double non décimale |
| CIB-21 | 1 | -0.3 | 0.02 | TWO_REAL_ROOTS | 0.1 ; 0.2 | 0.01 | piège d'arrondi des flottants |
| CIB-22 | 1 | 2 | 0 | TWO_REAL_ROOTS | -2 ; 0 | 4 | racine nulle sans signe « - » |
| CIB-23 | 0 | 3 | 1 | LINEAR_ROOT | -1/3 | — | linéaire non décimal |
| CIB-24 | 4 | 0 | -9 | TWO_REAL_ROOTS | -3/2 ; 3/2 | 144 | b = 0 |
| CIB-25 | 1e12 | 1e12 | -1e12 | TWO_REAL_ROOTS | (-1 ∓ √5)/2 | 5e24 | limites du domaine |
| CIB-26 | -1e12 | 0 | 1e-12 | TWO_REAL_ROOTS | -1e-12 ; 1e-12 | 4 | valeurs extrêmes |
| CIB-27 | 0 | -4 | 2 | LINEAR_ROOT | 0.5 | — | linéaire |
| CIB-28 | -5 | 0 | 0 | DOUBLE_REAL_ROOT | 0 | 0 | racine double nulle |
| CIB-29 | 1 | 2 | 5 | NO_REAL_ROOT | — (-1 ± 2i dans ℂ) | -16 | extension complexe |

Les calculs à la main sont eux-mêmes vérifiés : pour chaque cas, les racines
sont substituées dans l'équation à 150 chiffres (résidu ≤ 10⁻¹⁰⁰) et Δ est
recalculé exactement (`test_oracle.py::test_hand_computed_roots_satisfy_their_equation`).

### 4.3 Données invalides

Saisie vide, espaces, `None`, texte (`abc`), formats mal formés (`1..2`,
`--1`, `1e`, `0x1F`, `1_000`), chiffres non ASCII (`١٢`), `NaN`, `sNaN`,
infinis (texte, `float`, `Decimal`), booléens, listes, complexes, fractions,
valeurs hors limites (`1e13`, `10**13`, `1e300`), trop de décimales (`1e-13`),
chaînes de plus de 100 caractères, séparateurs ambigus (`1,000.5`, `1,2,3`).

## 5. Organisation des tests

| Fichier | Niveau / type | Ce qui est vérifié | Nombre de tests |
|---|---|---|---|
| `test_solver.py` | boîte noire, unitaire | 8 cas obligatoires (égalité exacte), décimaux, négatifs, petits, grands, irrationnels, Δ proche de 0, tri des racines, absence de `-0`, extension complexe, affichage | 48 |
| `test_discriminant.py` | boîte blanche | Δ exact, y compris aux coins du domaine ; exception si le calcul ne peut pas être exact | 13 |
| `test_linear_cases.py` | boîte blanche (branches a = 0) | premier degré, 0 = 0, c = 0, toutes les écritures de zéro | 23 |
| `test_invalid_inputs.py` | robustesse | rejet explicite de chaque donnée invalide, message nommant le coefficient, virgule française | 105 |
| `test_oracle.py` | unitaire (oracle) | indépendance (analyse des imports), formes closes, accord avec les calculs à la main, **détection** de résultats faux | 83 |
| `test_mapping.py` | unitaire | table de correspondance, décodage, 125 allers-retours encodage/décodage | 25 |
| `test_jenny_adapter.py` | unitaire + vrai Jenny | analyse de la sortie, arguments sûrs, délai, code retour, exécutable invalide, auto-test, constat A3, reproductibilité avec la référence Windows (A7) | 44 |
| `test_coverage.py` | unitaire | totaux 15/75/125, jeux construits à la main (diagonale, carré latin), éléments manquants | 14 |
| `test_uniwise.py` | campagne réelle | `jenny -n1 5 5 5`, décodage ligne à ligne, 100 % 1-way, tous les cas conformes | 6 |
| `test_pairwise.py` | campagne réelle | `jenny -n2 5 5 5`, 75/75 paires, 3-way incomplet, cohérence des catégories | 7 |
| `test_integration.py` | intégration | Jenny → décodage → solveur → oracle → rapports ; exhaustif 125 cas ; comparaison | 6 |
| `test_properties.py` | propriétés (Hypothesis) | accord avec l'oracle, cohérence catégorie / Δ, Viète, permutation des racines, invariance d'échelle, racines doubles, texte arbitraire | 11 |
| `test_mutation.py` | évaluation des tests | catalogue de 10 mutants, chaque mutant non équivalent, scores | 23 |
| `test_robustness.py` | robustesse | PATH, variable d'environnement, délai réel, combinaison indécodable, fichiers de sortie, codes de sortie CLI | 23 |
| `test_regression.py` | non-régression | un test par anomalie du journal (`reporting.ANOMALIES`) et par piège de conception | 8 |
| `test_reporting.py` | unitaire | colonnes CSV, BOM, sections du rapport, lecture JUnit et couverture | 6 |
| `test_cli.py` | système (CLI) | chaque commande, codes de sortie, aide en français, Jenny absent | 25 |
| `test_gui.py` | système (GUI) | chaque bouton déclenché par `invoke()`, mode Démonstration en 8 étapes | 8 |

Les nombres de tests sont ceux de l'exécution de validation du 30/10/2026
(`reports/pytest_junit.xml`, 478 tests au total). Les tests marqués `jenny`
nécessitent le binaire compilé ; ceux marqués `gui` nécessitent Tkinter.

## 6. Fiches des principaux cas

### TC-01 — Cas obligatoires de l'énoncé
- **Préconditions** : aucune.
- **Actions** : `solve(a, b, c)` pour les 8 cas CAS1 à CAS8.
- **Résultats attendus** : catégorie et racines **exactement** égales aux
  valeurs calculées à la main (par exemple CAS 7 : `TWO_REAL_ROOTS`, racines
  1 et 2, Δ = 1) ; aucune erreur.

### TC-02 — Δ minuscule non arrondi à zéro
- **Préconditions** : aucune.
- **Actions** : `solve("1000000.000000000001", "2000000", "999999.999999999999")`.
- **Résultats attendus** : Δ = 4·10⁻²⁴ exactement, catégorie `TWO_REAL_ROOTS`
  (en double précision, Δ vaudrait 0 et on conclurait à tort à une racine
  double) ; l'affichage augmente le nombre de chiffres pour distinguer les
  deux racines.

### TC-03 — Annulation catastrophique
- **Actions** : `solve("1e-12", "1e12", "1e-12")`.
- **Résultats attendus** : petite racine ≈ -10⁻²⁴ non nulle ; produit des
  racines = c/a = 1 à 10⁻⁴⁵ près.

### TC-04 — Saisies invalides
- **Actions** : `solve(1, valeur, 1)` pour chaque donnée invalide du § 4.3.
- **Résultats attendus** : catégorie `INVALID_INPUT`, aucune racine, aucun
  discriminant, message contenant le nom du coefficient et la raison (vide,
  format, NaN, infini, booléen, type, limite, décimales, longueur). Jamais de
  conversion silencieuse en zéro.

### TC-05 — Campagne Uniwise réelle
- **Préconditions** : Jenny compilé et auto-test réussi.
- **Actions** : `python -m quadratic_lab test --method uniwise`.
- **Résultats attendus** : commande `jenny -n1 5 5 5` réellement exécutée,
  une ligne brute = un cas, couverture 1-way 15/15, tous les cas conformes à
  l'oracle, code de sortie 0.

### TC-06 — Campagne Pairwise réelle
- **Préconditions** : Jenny compilé.
- **Actions** : `python -m quadratic_lab test --method pairwise`.
- **Résultats attendus** : 75/75 paires couvertes (25 par couple de
  dimensions), 25 ≤ nombre de cas < 125, couverture 3-way incomplète, tous les
  cas conformes.

### TC-07 — Exhaustif
- **Actions** : `python -m quadratic_lab test --method exhaustive`.
- **Résultats attendus** : 125 cas distincts, 125 conformes, couverture 3-way
  complète, les 6 catégories mathématiques atteintes.

### TC-08 — Jenny indisponible
- **Préconditions** : `QUADRATIC_LAB_JENNY` pointe vers un fichier absent.
- **Actions** : `python -m quadratic_lab generate --method pairwise`.
- **Résultats attendus** : message « Jenny indisponible », code de sortie 3,
  aucun fichier CSV produit (aucune simulation).

### TC-09 — L'oracle détecte un résultat faux
- **Actions** : comparer à l'oracle des résultats volontairement faux
  (mauvaise catégorie, racine décalée de 10⁻²⁸, racine manquante, Δ faux,
  racines non triées, formule naïve en flottants sur x² + 10⁸x + 1).
- **Résultats attendus** : verdict « Non conforme » à chaque fois, alors que le
  vrai solveur est « Conforme ».

### TC-10 — Mode Démonstration de la GUI
- **Préconditions** : Tkinter disponible, Jenny compilé.
- **Actions** : déclencher 8 fois « Étape suivante ».
- **Résultats attendus** : 8 étapes exécutées, la dernière affiche l'onglet
  Comparaison avec les résultats ; « Recommencer » réinitialise.

## 7. Critère de conformité (oracle)

Un cas est **RÉUSSI** si, en comparant le résultat du solveur à l'attendu de
l'oracle indépendant (`oracle.compare`) :

1. la **catégorie** est identique ;
2. le **discriminant** est identique **exactement** ;
3. le **nombre de racines** est le même et elles sont **triées** ;
4. chaque racine a un **écart relatif ≤ 10⁻⁴⁰** ;
5. le **résidu relatif** `|a·x² + b·x + c| / (|a|x² + |b||x| + |c|)` est ≤ 10⁻⁴⁰ ;
6. pour deux racines, les **relations de Viète** (somme = -b/a,
   produit = c/a) sont vérifiées à 10⁻⁴⁰ près.

Sinon le cas est **ÉCHEC** ; si le solveur lève une exception, il est
**ERREUR**.

## 8. Critères d'entrée et de sortie

**Entrée** : environnement `.venv` installé (`pip install -e ".[dev]"`),
Jenny compilé et auto-test réussi (sinon les tests `jenny` sont ignorés et
signalés).

**Sortie** : aucun échec ni erreur ; couverture Uniwise et Pairwise complètes
sur la matrice ; tous les cas ciblés conformes ; objectifs de couverture du
code atteints.

| Indicateur | Objectif | Résultat mesuré (30/10/2026) |
|---|---|---|
| Tests pytest | 0 échec | **478 réussis, 0 échec, 0 erreur, 0 ignoré** (Windows 11 et Ubuntu 24.04) |
| Lignes du code métier (hors GUI) | ≥ 95 % | **100 %** (1424/1424) |
| Branches du code métier (hors GUI) | ≥ 90 % | **100 %** (396/396) |
| Couverture de la GUI (mesurée à part) | — | 90 % |
| Uniwise sur la matrice | 100 % | 15/15 (100 %) |
| Pairwise sur la matrice | 100 % | 75/75 (100 %) |
| Cas ciblés | tous conformes | 29/29 |

Six blocs défensifs inatteignables (exceptions impossibles dans le domaine
validé, commande `gui` interactive) sont exclus de la mesure par
`# pragma: no cover` ; ils sont listés dans le rapport de validation.

## 9. Traçabilité spécifications → tests

| Règle | Contenu | Tests |
|---|---|---|
| S-01 | 7 catégories exclusives | `test_linear_cases.py::test_no_solution_differs_from_no_real_root_and_invalid_input`, `test_oracle.py::test_reference_cases_cover_every_mathematical_category` |
| S-02 | résultat structuré, immuable | `test_solver.py::test_result_is_immutable`, `::test_to_dict_is_serialisable` |
| S-03 | racines triées | `test_solver.py::test_roots_sorted_even_when_a_negative`, `test_oracle.py::test_compare_detects_signed_zero_and_order_issues` |
| S-04 | pas de `-0` | `test_solver.py::test_zero_root_has_no_negative_sign`, `test_regression.py::test_design_negative_zero_root` |
| S-10 à S-13 | domaine et rejet des entrées | `test_invalid_inputs.py` (tout le fichier), `test_properties.py::test_arbitrary_text_is_parsed_or_cleanly_rejected` |
| S-14 | virgule française | `test_invalid_inputs.py::test_user_input_accepts_french_comma`, `test_cli.py::test_solve_accepts_french_decimal_comma` |
| S-20, S-21 | Δ exact à 50 chiffres | `test_discriminant.py`, `test_properties.py::test_category_consistent_with_exact_discriminant` |
| S-22 | aucune tolérance sur le signe de Δ | `test_solver.py::test_extremely_tiny_positive_discriminant_is_not_rounded_to_zero`, `::test_tiny_negative_discriminant_gives_no_real_root` |
| S-23 | formule stable, signe(0) = +1 | `test_solver.py::test_extreme_magnitudes_no_catastrophic_cancellation`, `test_regression.py::test_design_sign_of_zero_in_stable_formula` |
| S-25 | affichage | `test_solver.py::test_format_number`, `::test_format_roots_increases_digits_to_distinguish_close_roots` |
| S-26 | extension complexe | `test_solver.py::test_complex_roots_extension_does_not_change_category`, `test_cli.py::test_solve_complex_extension` |
| S-30 à S-33 | oracle indépendant | `test_oracle.py` (tout le fichier) |
| S-40 | table de correspondance | `test_mapping.py` |
| S-41, S-42 | Jenny réel, pas de simulation | `test_uniwise.py`, `test_pairwise.py`, `test_cli.py::test_jenny_unavailable_is_declared_not_simulated` |
| S-43 | erreurs Jenny sur stdout | `test_jenny_adapter.py::test_real_jenny_reports_errors_on_stdout_with_exit_code_zero`, `test_regression.py::test_a3_…` |
| S-44 | traçabilité des cas | `test_uniwise.py::test_every_raw_line_becomes_exactly_one_case` |
| S-50, S-51 | couverture indépendante | `test_coverage.py`, `test_pairwise.py::test_all_75_pairs_are_covered` |
| S-52 | catégories atteintes | `test_pairwise.py::test_category_coverage_is_consistent_with_cases`, `test_integration.py::test_exhaustive_125_cases_all_pass` |
| S-60 | CLI et codes de sortie | `test_cli.py`, `test_robustness.py` (partie CLI) |
| S-61 | GUI | `test_gui.py` |
| S-62 | rapports | `test_reporting.py`, `test_integration.py::test_full_pipeline_uniwise_to_report` |

## 10. Exécution

```powershell
# Validation complète : pytest + couverture + comparaison + rapports
powershell -ExecutionPolicy Bypass -File tools\run_validation.ps1

# Suite seule
.\.venv\Scripts\python.exe -m pytest

# Seulement les tests qui exécutent le vrai Jenny
.\.venv\Scripts\python.exe -m pytest -m jenny

# Seulement l'interface graphique
.\.venv\Scripts\python.exe -m pytest -m gui

# Tests par propriétés plus rapides (30 exemples au lieu de 200)
$env:HYPOTHESIS_PROFILE = "rapide"; .\.venv\Scripts\python.exe -m pytest
```

Les résultats sont écrits dans `reports/` : `pytest_junit.xml`,
`coverage.json`, `htmlcov/`, les fichiers de campagne et
`rapport_validation.md`.
