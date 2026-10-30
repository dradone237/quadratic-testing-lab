# Rapport de validation — QUADRATIC TESTING LAB

*Généré automatiquement le 30/10/2026 à 18:17:00 à partir des résultats réellement exécutés. Aucune valeur n'est saisie à la main.*

## 1. Objectifs des tests

- **Question mathématique** : le programme calcule-t-il correctement les solutions de a·x² + b·x + c = 0 ?
- **Question de génie logiciel** : comment démontrer, par une stratégie de tests rigoureuse, qu'il fonctionne dans les scénarios prévus et gère correctement les situations anormales ?
- Moyens : génération combinatoire réelle par Jenny (Uniwise `-n1`, Pairwise `-n2`, 3-way `-n3`), référence exhaustive (125 cas), cas ciblés calculés à la main, oracle indépendant (rationnels exacts), tests par propriétés (Hypothesis) et analyse de mutation.
- Critère de conformité d'un cas : même catégorie, discriminant identique (exact), racines à moins de 10⁻⁴⁰ en relatif, résidu relatif ≤ 10⁻⁴⁰, relations de Viète vérifiées.

## 2. Partitions des coefficients

Chaque coefficient est partitionné en classes d'équivalence : grand négatif, petit négatif, zéro, petit positif, grand positif. Pour b, ±2 remplace ±1 afin de pouvoir produire Δ = 0 (b² = 4ac avec a = c = ±1).

| Étiquette Jenny | Dimension | Coefficient | Valeur |
|---|---|---|---|
| 1a | 1 | a | -10 |
| 1b | 1 | a | -1 |
| 1c | 1 | a | 0 |
| 1d | 1 | a | 1 |
| 1e | 1 | a | 10 |
| 2a | 2 | b | -10 |
| 2b | 2 | b | -2 |
| 2c | 2 | b | 0 |
| 2d | 2 | b | 2 |
| 2e | 2 | b | 10 |
| 3a | 3 | c | -10 |
| 3b | 3 | c | -1 |
| 3c | 3 | c | 0 |
| 3d | 3 | c | 1 |
| 3e | 3 | c | 10 |

Les lettres a…e sont des **étiquettes de valeurs** Jenny, sans rapport avec les noms des coefficients.

## 3. Commandes Jenny exécutées

- `jenny -n1 5 5 5` — 5 combinaisons, code retour 0, 13.2 ms — exécutable `C:\Users\SmartCamp PC1\Desktop\ProjetM2\quadratic-testing-lab\tools\jenny\bin\jenny.exe`
- `jenny -n2 5 5 5` — 28 combinaisons, code retour 0, 12.7 ms — exécutable `C:\Users\SmartCamp PC1\Desktop\ProjetM2\quadratic-testing-lab\tools\jenny\bin\jenny.exe`
- `jenny -n3 5 5 5` — 125 combinaisons, code retour 0, 13.5 ms — exécutable `C:\Users\SmartCamp PC1\Desktop\ProjetM2\quadratic-testing-lab\tools\jenny\bin\jenny.exe`

Les sorties brutes sont conservées dans `reports/jenny_<méthode>_raw.txt`.

## 4. Combinaisons générées

### Uniwise — `jenny -n1 5 5 5`

| ID | Combinaison | a | b | c |
|---|---|---|---|---|
| UNI-001 | `1a 2d 3a` | -10 | 2 | -10 |
| UNI-002 | `1b 2b 3e` | -1 | -2 | 10 |
| UNI-003 | `1c 2e 3b` | 0 | 10 | -1 |
| UNI-004 | `1d 2c 3c` | 1 | 0 | 0 |
| UNI-005 | `1e 2a 3d` | 10 | -10 | 1 |

### Pairwise — `jenny -n2 5 5 5`

| ID | Combinaison | a | b | c |
|---|---|---|---|---|
| PAIR-001 | `1a 2d 3a` | -10 | 2 | -10 |
| PAIR-002 | `1b 2b 3e` | -1 | -2 | 10 |
| PAIR-003 | `1c 2e 3b` | 0 | 10 | -1 |
| PAIR-004 | `1d 2c 3c` | 1 | 0 | 0 |
| PAIR-005 | `1e 2a 3d` | 10 | -10 | 1 |
| PAIR-006 | `1a 2a 3e` | -10 | -10 | 10 |
| PAIR-007 | `1b 2a 3b` | -1 | -10 | -1 |
| PAIR-008 | `1c 2a 3c` | 0 | -10 | 0 |
| PAIR-009 | `1d 2a 3a` | 1 | -10 | -10 |
| PAIR-010 | `1e 2b 3c` | 10 | -2 | 0 |
| PAIR-011 | `1a 2c 3b` | -10 | 0 | -1 |
| PAIR-012 | `1b 2d 3c` | -1 | 2 | 0 |
| PAIR-013 | `1a 2e 3d` | -10 | 10 | 1 |
| PAIR-014 | `1c 2d 3e` | 0 | 2 | 10 |
| PAIR-015 | `1d 2e 3e` | 1 | 10 | 10 |
| PAIR-016 | `1e 2c 3e` | 10 | 0 | 10 |
| PAIR-017 | `1a 2b 3a` | -10 | -2 | -10 |
| PAIR-018 | `1d 2d 3d` | 1 | 2 | 1 |
| PAIR-019 | `1b 2c 3a` | -1 | 0 | -10 |
| PAIR-020 | `1c 2c 3d` | 0 | 0 | 1 |
| PAIR-021 | `1e 2d 3b` | 10 | 2 | -1 |
| PAIR-022 | `1d 2b 3b` | 1 | -2 | -1 |
| PAIR-023 | `1e 2e 3c` | 10 | 10 | 0 |
| PAIR-024 | `1e 2e 3a` | 10 | 10 | -10 |
| PAIR-025 | `1b 2e 3d` | -1 | 10 | 1 |
| PAIR-026 | `1c 2b 3a` | 0 | -2 | -10 |
| PAIR-027 | `1a 2d 3c` | -10 | 2 | 0 |
| PAIR-028 | `1e 2b 3d` | 10 | -2 | 1 |

### 3-way (Jenny -n3) — `jenny -n3 5 5 5`

125 combinaisons (liste complète dans `triplewise_cases.csv`).

## 5. Cas réellement exécutés

| Méthode | Générateur | Cas exécutés | TWO_REAL_ROOTS | DOUBLE_REAL_ROOT | NO_REAL_ROOT | LINEAR_ROOT | INFINITE_SOLUTIONS | NO_SOLUTION |
|---|---|---|---|---|---|---|---|---|
| Uniwise | jenny | 5 | 2 | 1 | 1 | 1 | 0 | 0 |
| Pairwise | jenny | 28 | 15 | 2 | 6 | 4 | 0 | 1 |
| 3-way (Jenny -n3) | jenny | 125 | 68 | 8 | 24 | 20 | 1 | 4 |
| Exhaustif | itertools.product | 125 | 68 | 8 | 24 | 20 | 1 | 4 |
| Ciblés | manuel (calcul analytique) | 29 | 18 | 3 | 3 | 3 | 1 | 1 |

## 6. Résultats

| Méthode | Cas | Réussis | Échecs | Erreurs | 1-way | 2-way | 3-way | Catégories | Exécution (ms) |
|---|---|---|---|---|---|---|---|---|---|
| Uniwise | 5 | 5 | 0 | 0 | 100.0 % | 20.0 % | 4.0 % | 4/6 | 0.8 |
| Pairwise | 28 | 28 | 0 | 0 | 100.0 % | 100.0 % | 22.4 % | 5/6 | 3.0 |
| 3-way (Jenny -n3) | 125 | 125 | 0 | 0 | 100.0 % | 100.0 % | 100.0 % | 6/6 | 9.3 |
| Exhaustif | 125 | 125 | 0 | 0 | 100.0 % | 100.0 % | 100.0 % | 6/6 | 9.6 |
| Ciblés | 29 | 29 | 0 | 0 | 60.0 % | 22.7 % | 4.8 % | 6/6 | 2.1 |

**Suite pytest** : 478 tests — 478 réussis, 0 échecs, 0 erreurs, 0 ignorés (19.7 s).

## 7. Couverture

- **Uniwise** : 1-way 15/15 (100.0 %) ; 2-way 15/75 (20.0 %) ; 3-way 5/125 (4.0 %) ; catégories non atteintes : INFINITE_SOLUTIONS, NO_SOLUTION.
- **Pairwise** : 1-way 15/15 (100.0 %) ; 2-way 75/75 (100.0 %) ; 3-way 28/125 (22.4 %) ; catégories non atteintes : INFINITE_SOLUTIONS.
- **3-way (Jenny -n3)** : 1-way 15/15 (100.0 %) ; 2-way 75/75 (100.0 %) ; 3-way 125/125 (100.0 %) ; catégories non atteintes : aucune.
- **Exhaustif** : 1-way 15/15 (100.0 %) ; 2-way 75/75 (100.0 %) ; 3-way 125/125 (100.0 %) ; catégories non atteintes : aucune.
- **Ciblés** : 1-way 9/15 (60.0 %) ; 2-way 17/75 (22.7 %) ; 3-way 6/125 (4.8 %) ; catégories non atteintes : aucune.
  (cas hors matrice pédagogique : la couverture t-wise n'y est pas l'objectif)

**Couverture du code métier** (pytest-cov, GUI exclue) : lignes 100.0 % (1424/1424), branches 100.0 % (396/396). Six blocs sont exclus par `# pragma: no cover` : cinq gardes défensives inatteignables dans le domaine validé et la commande interactive `gui` (voir docs/RAPPORT_VALIDATION.md).

## 8. Écarts détectés

Aucun écart : les 312 cas exécutés sont conformes à l'oracle indépendant.

**Analyse de mutation** — capacité de chaque stratégie à détecter des défauts injectés :

| Mutant | Défaut injecté | Déclencheur | Uniwise | Pairwise | 3-way (Jenny -n3) | Exhaustif | Ciblés |
|---|---|---|---|---|---|---|---|
| M01 | Signe du discriminant inversé | a ≠ 0 et c ≠ 0 (paire a × c) | tué | tué | tué | tué | tué |
| M02 | Delta nul traité comme négatif | Δ = 0 : b² = 4ac | tué | tué | tué | tué | tué |
| M03 | Cas a = 0 non traité | a = 0 (valeur seule, 1-way) | tué | tué | tué | tué | tué |
| M04 | a = 0 et b = 0 non distingués | paire (a = 0, b = 0) (2-way) | **survit** | tué | tué | tué | tué |
| M05 | 0 = 0 déclaré sans solution | triplet (0, 0, 0) (3-way) | **survit** | **survit** | tué | tué | tué |
| M06 | Racine double -b/a | Δ = 0 avec b ≠ 0 (triplet précis) | **survit** | tué | tué | tué | tué |
| M07 | Formule scolaire en double précision | racine non représentable exactement en binaire | tué | tué | tué | tué | tué |
| M08 | Signe de la solution linéaire | a = 0, b ≠ 0, c ≠ 0 | tué | tué | tué | tué | tué |
| M09 | Delta négatif ignoré | Δ < 0 | tué | tué | tué | tué | tué |
| M10 | Formule stable avec signe(0) = 0 | b = 0 et a·c < 0 (triplet : signes de a et c opposés) | **survit** | **survit** | tué | tué | tué |
| **Score** | | | **60 %** | **80 %** | **100 %** | **100 %** | **100 %** |

## 9. Anomalies corrigées

| ID | Constat | Cause | Correction | Test de non-régression |
|---|---|---|---|---|
| A1 | Deux tests comparaient le solveur à une valeur de référence calculée avec les opérateurs Decimal (-x, (√5 - 1)/2) : ces opérateurs arrondissent au contexte par défaut (28 chiffres). | Défaut dans les TESTS, pas dans le solveur (qui était juste à 50 chiffres). | Calculs de référence faits dans un contexte explicite à 60 chiffres (copy_negate, Context). | `tests/test_solver.py::test_irrational_roots_sqrt2, ::test_coefficients_at_the_domain_limit` |
| A2 | Un test « très grands coefficients » utilisait b = -3·10¹², hors du domaine \|x\| ≤ 10¹². | Défaut dans le TEST ; le solveur avait correctement répondu INVALID_INPUT. | Cas remplacé par 10¹¹(x-1)(x-2) ; test explicite du rejet juste hors limites ajouté. | `tests/test_solver.py::test_coefficient_just_outside_the_domain_is_rejected` |
| A3 | Jenny signale ses erreurs (ex. « dimensions must be smaller than 52 ») sur la sortie standard avec un code de retour 0. | Comportement de l'outil tiers : le code de retour seul ne suffit pas. | L'adaptateur rejette toute ligne commençant par « jenny: » (JennyExecutionError). | `tests/test_jenny_adapter.py::test_real_jenny_reports_errors_on_stdout_with_exit_code_zero` |
| A4 | Dans rapport_validation.md, le texte « \|x\| ≤ 10¹² » de l'anomalie A2 cassait le tableau Markdown (la barre verticale était lue comme un séparateur de colonnes). | Défaut du générateur de rapport : contenu des cellules non échappé. | Échappement systématique de « \| » en « \\| » dans toutes les cellules de tableau. | `tests/test_regression.py::test_a4_markdown_table_cells_are_escaped` |
| A5 | Lors d'une exécution complète, un test GUI a été ignoré : Tk() n'a pas pu lire init.tcl (« couldn't read file … init.tcl: No error »), alors que le fichier existe. | Environnement Windows : échec intermittent de lecture lors de créations répétées de Tk() dans le même processus (machine chargée). | Une seule instance Tk par module de test (fenêtres Toplevel par test) et 5 tentatives avant de déclarer l'affichage indisponible. | `tests/test_gui.py (fixtures tk_root et app)` |
| A6 | Sous Ubuntu (clone frais), test_build_command_uniwise_and_pairwise échouait : chemin « /usr/bin/python3.12 » obtenu au lieu de « .venv/bin/python ». | Défaut du TEST : sous Linux, le python d'un venv est un lien symbolique que find_jenny() résout ; le test supposait un chemin inchangé (vrai seulement sous Windows). | Le test compare au chemin résolu par l'adaptateur. | `tests/test_jenny_adapter.py::test_build_command_uniwise_and_pairwise` |
| A7 | Jenny compilé tel quel sous Ubuntu 64 bits produit d'autres combinaisons (29 cas Pairwise au lieu de 28), incohérentes avec la documentation. | jenny.c déclare ub4 (« 4 octets ») comme unsigned long, qui fait 8 octets sous Linux 64 bits : le générateur pseudo-aléatoire change. | build_jenny.sh compile une copie où ub4/sb4 passent sur 32 bits (2 lignes) ; sorties -n1/-n2/-n3 vérifiées identiques octet par octet à Windows. | `tests/test_jenny_adapter.py::test_real_jenny_matches_reference_outputs` |

## 10. Limites de la stratégie

- **Pairwise ≠ exhaustif** : 100 % des paires ne signifie pas 100 % des triplets ; un défaut qui ne se déclenche que pour une combinaison précise de trois valeurs peut échapper à Pairwise.
- **Branches non garanties** : la campagne Pairwise réelle (28 cas) n'atteint pas les catégories suivantes : INFINITE_SOLUTIONS. D'où les cas ciblés.
- **Matrice réduite** : 5 valeurs par coefficient ne représentent pas les décimaux, les très petites ou très grandes valeurs ; ceux-ci sont couverts par les cas ciblés et les tests par propriétés.
- **Oracle numérique** : pour les racines irrationnelles, la validation repose sur une tolérance (10⁻⁴⁰) ; elle prouve la proximité, pas l'égalité. Le discriminant et la catégorie sont, eux, vérifiés exactement.
- **Moins de tests ≠ meilleure méthode** : le nombre de cas doit être mis en regard de la couverture et du score de mutation.
- **Aucune stratégie de test ne prouve l'absence de défauts** ; elle augmente la confiance.
