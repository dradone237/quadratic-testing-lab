# Rapport de validation commenté — QUADRATIC TESTING LAB

> Ce document commente les résultats de la **validation finale du 30/10/2026**.
> Les tableaux chiffrés proviennent de `reports/` (générés par
> `tools/run_validation.ps1`) ; une copie figée du rapport automatique se
> trouve dans `samples/rapport_validation_reference.md`. Aucun chiffre n'a été
> saisi à la main sans avoir été mesuré.

## 1. Objectifs

| Question | Réponse apportée par le projet |
|---|---|
| Le programme calcule-t-il correctement les solutions ? | Oui sur les 312 cas exécutés par les campagnes (0 écart), sur 29 cas calculés à la main et sur des entrées aléatoires (11 tests Hypothesis, jusqu'à 200 exemples chacun, reproductibles), jugés par un oracle indépendant. |
| Comment le démontrer rigoureusement ? | Spécification écrite d'abord (S-01 à S-62), tests écrits avant le code, génération combinatoire réelle par Jenny, couverture recalculée indépendamment, oracle indépendant, mutation, couverture de code. |

## 2. Environnement réellement utilisé

| Élément | Version |
|---|---|
| Système | Windows 11 Pro (10.0.26200) |
| Python | 3.12.10 (`.venv` du projet) |
| pytest / pytest-cov / Hypothesis | 9.2.0 / 7.1.0 / 6.170.14 |
| Jenny | source officielle burtleburtle.net (SHA-256 `b9322208…5dcb23`), compilée avec `zig cc` 0.16.0 (`-O3 -std=c99`) |
| Binaire Jenny | `tools/jenny/bin/jenny.exe`, SHA-256 `3b3c41f4…6d96a37` |
| Vérification Linux | Ubuntu 24.04.5 LTS (WSL), Python 3.12.3, gcc 13, clone Git frais, `tools/setup_ubuntu.sh` puis `tools/run_validation.sh` |

GCC n'était pas installé. Plutôt que de modifier le système, le compilateur C
`zig cc` (paquet PyPI officiel `ziglang`) a été installé dans le `.venv`.
La procédure MSYS2/GCC est documentée comme alternative (docs/GUIDE_JENNY.md).

## 3. Démarche suivie (TDD) et historique réel

| Étape | Résultat observé |
|---|---|
| Spécifications | `docs/SPECIFICATIONS.md` : catégories, domaine d'entrée, politique numérique, oracle, Jenny, couverture. |
| Tests écrits avant le code | Première exécution : **15 erreurs de collecte** (`ModuleNotFoundError`) : phase « rouge » attendue. |
| Solveur implémenté | 185 réussis, **2 échecs**, tous deux dus aux tests (anomalies A1 et A2). |
| Oracle, Jenny, couverture | 257 réussis, 1 échec (seconde occurrence de A1, dans un test). |
| Suite complète + couverture | 445 réussis ; couverture 97 % ; chemins défensifs non testés identifiés. |
| Tests de robustesse ajoutés | 475 réussis ; 100 % lignes et branches du code métier. |
| Validation par le script officiel | 475 réussis, **1 ignoré** (anomalie A5, Tk) : corrigé. |
| Validation par le script officiel (Windows) | 476 réussis, 0 ignoré. |
| Premier essai sous Ubuntu (clone frais) | 475 réussis, **1 échec** (anomalie A6) ; Jenny brut : 29 cas Pairwise au lieu de 28 (anomalie A7) : corrigés. |
| **Validation finale** | **478 réussis, 0 échec, 0 erreur, 0 ignoré**, sous Windows 11 **et** sous Ubuntu 24.04 ; comparaison des stratégies identique sur les deux systèmes. |

## 4. Intégration réelle de Jenny

Commandes exécutées par l'adaptateur (`subprocess.run`, liste d'arguments,
sans shell, délai maximal 20 s), sortie brute conservée dans
`reports/jenny_*_raw.txt` :

| Commande | Lignes | Code retour |
|---|---|---|
| `jenny -n1 5 5 5` | 5 | 0 |
| `jenny -n2 5 5 5` | 28 | 0 |
| `jenny -n3 5 5 5` | 125 | 0 |

Sortie réelle de `jenny -n1 5 5 5` :

```
 1a 2d 3a
 1b 2b 3e
 1c 2e 3b
 1d 2c 3c
 1e 2a 3d
```

Constats sur l'outil :

- Jenny est **déterministe** (graine fixe par défaut) : deux exécutions donnent
  une sortie identique (test `test_real_jenny_is_deterministic`).
- Les 5 premières lignes de `-n2` sont exactement celles de `-n1` : Jenny
  couvre d'abord les valeurs seules, puis complète les paires.
- 28 cas pour Pairwise alors que la borne inférieure est 25 (5 × 5) : un
  tableau orthogonal (carré latin) atteint 25 (démontré dans
  `tests/test_coverage.py`). L'algorithme glouton de Jenny n'est pas optimal,
  mais garantit la couverture.
- **Jenny écrit ses erreurs sur la sortie standard avec le code de retour 0**
  (anomalie A3). L'adaptateur analyse donc aussi le contenu.

Si Jenny est absent, la génération lève une `JennyError` et la CLI renvoie le
code 3 : **aucune simulation** (tests `test_jenny_unavailable_is_declared_not_simulated`
et `test_compare_without_jenny_still_reports_offline_methods`).

## 5. Résultats par stratégie

| Stratégie | Cas | Réussis | 1-way | 2-way | 3-way | Catégories atteintes | Score de mutation |
|---|---|---|---|---|---|---|---|
| Uniwise | 5 | 5 | 15/15 | 15/75 | 5/125 | 4/6 | 60 % |
| Pairwise | 28 | 28 | 15/15 | **75/75** | 28/125 | 5/6 | 80 % |
| 3-way (Jenny -n3) | 125 | 125 | 15/15 | 75/75 | 125/125 | 6/6 | 100 % |
| Exhaustif | 125 | 125 | 15/15 | 75/75 | 125/125 | 6/6 | 100 % |
| Ciblés | 29 | 29 | (hors matrice) | | | 6/6 | 100 % |

Durées mesurées (validation finale) : génération Jenny ≈ 11 à 13 ms (deux
lancements de processus : auto-test et génération), exécution de 125 cas
≈ 9 ms. Le temps n'est donc pas un critère discriminant à cette échelle ; le
nombre de cas l'est, et il croîtrait exponentiellement en exhaustif avec plus
de coefficients ou de valeurs.

Catégories non atteintes : Uniwise ne produit ni `INFINITE_SOLUTIONS` ni
`NO_SOLUTION` ; Pairwise ne produit pas `INFINITE_SOLUTIONS`, que seul le
triplet (0, 0, 0) déclenche.

## 6. Analyse de mutation

Dix défauts réalistes ont été injectés dans des copies du solveur
(`mutation.py`). Une stratégie « tue » un mutant si au moins un de ses cas le
fait échouer face à l'oracle.

| Mutant | Défaut | Uniwise | Pairwise | 3-way | Exhaustif | Ciblés |
|---|---|---|---|---|---|---|
| M01 | Δ = b² + 4ac | tué | tué | tué | tué | tué |
| M02 | Δ = 0 traité comme négatif | tué | tué | tué | tué | tué |
| M03 | a = 0 non traité | tué | tué | tué | tué | tué |
| M04 | a = 0 et b = 0 non distingués | **survit** | tué | tué | tué | tué |
| M05 | 0 = 0 déclaré sans solution | **survit** | **survit** | tué | tué | tué |
| M06 | racine double −b/a | **survit** | tué | tué | tué | tué |
| M07 | formule scolaire en flottants | tué | tué | tué | tué | tué |
| M08 | x = c/b au lieu de −c/b | tué | tué | tué | tué | tué |
| M09 | Δ < 0 ignoré (√\|Δ\|) | tué | tué | tué | tué | tué |
| M10 | formule stable avec signe(0) = 0 | **survit** | **survit** | tué | tué | tué |

Interprétation :

- **Pourquoi Pairwise fait mieux qu'Uniwise** : M04 ne se déclenche que si
  a = 0 **et** b = 0 en même temps. Les 5 cas Uniwise contiennent a = 0
  (UNI-003 : 0, 10, −1) et b = 0 (UNI-004 : 1, 0, 0), mais jamais ensemble.
  Pairwise garantit la paire (a = 0, b = 0), présente dans PAIR-020 (0, 0, 1).
- **Pourquoi Pairwise ne suffit pas** : M05 exige le triplet (0, 0, 0) et M10
  exige b = 0 avec a et c de signes opposés. Ce sont des interactions
  d'ordre 3, que Pairwise ne garantit pas. Les 28 cas Pairwise n'en contiennent
  aucune.
- Les **29 cas ciblés** tuent les 10 mutants. CAS 1 (x² − 1) suffit à tuer M10 :
  c'est pourquoi l'énoncé impose des tests dirigés en plus de Jenny.

## 7. Oracle et validation numérique

- L'oracle n'importe ni le solveur ni la validation (vérifié par analyse
  syntaxique dans `test_oracle_does_not_import_the_solver`).
- Il a lui-même été validé de deux façons : (1) les 29 formes closes calculées
  à la main satisfont leur équation (résidu < 10⁻¹⁰⁰) ; (2) des résultats
  volontairement faux sont rejetés (catégorie, racine décalée de 10⁻²⁸,
  discriminant, racine manquante, ordre).
- Démonstration du problème de l'oracle : la formule scolaire en double
  précision donne −7,45·10⁻⁹ au lieu de −10⁻⁸ pour x² + 10⁸x + 1. Elle paraît
  correcte sur les cas simples, mais l'oracle la rejette.
- Tolérance relative 10⁻⁴⁰ : le solveur est précis à ~10⁻⁴⁸ et l'oracle à mieux
  que 10⁻⁷⁰. La catégorie et le discriminant sont comparés **exactement**.

## 8. Couverture du code

| Périmètre | Lignes | Branches |
|---|---|---|
| Code métier (hors GUI) | **100 %** (1424/1424) | **100 %** (396/396) |
| Interface graphique (mesure séparée, `tests/test_gui.py`) | 92,9 % (509/548) | 90 % en mesure combinée lignes + branches (72 branches, 13 partielles) |

Six blocs sont exclus par `# pragma: no cover`, chacun justifié :

| Emplacement | Raison |
|---|---|
| `cli.py` `cmd_gui` | lance la boucle interactive Tkinter |
| `cli.py` reconfiguration des flux | flux standard non reconfigurable (cas d'environnement) |
| `solver.py` `compute_discriminant` (`DecimalException` hors `Inexact`) | impossible pour des décimaux finis |
| `solver.py` `solve` (`DecimalException`) | exclu par la validation (S-24) |
| `solver.py` `format_roots` (repli final) | les racines distinctes diffèrent toujours à 50 chiffres (S-24) |
| `validation.py` (`InvalidOperation` après l'expression régulière) | l'expression régulière garantit un texte accepté par `Decimal` |

Rappel : 100 % de couverture signifie que chaque ligne et chaque branche a
été exécutée au moins une fois, **pas** que le programme est sans défaut.

## 9. Anomalies rencontrées et corrigées

| ID | Constat | Cause | Correction | Test permanent |
|---|---|---|---|---|
| A1 | Deux références de test calculées avec `-x` et `(√5 − 1)/2` en `Decimal` | les opérateurs arrondissent au contexte par défaut (28 chiffres) ; défaut du **test** | calculs dans un `Context` à 60 chiffres | `test_regression.py::test_a1_…` |
| A2 | Test « très grands coefficients » avec b = −3·10¹² | hors domaine ; le solveur répondait correctement `INVALID_INPUT` | cas remplacé, rejet hors limites testé | `test_regression.py::test_a2_…` |
| A3 | Jenny : erreurs sur stdout, code 0 | comportement de l'outil tiers | analyse du contenu (`jenny:`) | `test_jenny_adapter.py`, `test_regression.py::test_a3_…` |
| A4 | Tableau Markdown cassé par « \|x\| » | cellules non échappées | échappement de « \| » | `test_regression.py::test_a4_…` |
| A5 | Un test GUI ignoré : `init.tcl` illisible (« No error ») | échec intermittent de Tk() répété sous Windows | une instance Tk par module, 5 tentatives | `tests/test_gui.py` (fixtures) |
| A6 | Sous Ubuntu, un test d'adaptateur échoue (`/usr/bin/python3.12` ≠ `.venv/bin/python`) | défaut du **test** : le python d'un venv Linux est un lien symbolique, résolu par `find_jenny()` | comparaison au chemin résolu | `test_jenny_adapter.py::test_build_command_uniwise_and_pairwise` |
| A7 | Jenny compilé tel quel sous Ubuntu 64 bits : autres combinaisons, 29 cas Pairwise | `ub4` (« 4 octets ») déclaré `unsigned long`, qui fait 8 octets sous Linux | copie de compilation avec `ub4`/`sb4` sur 32 bits ; sorties identiques à Windows | `test_jenny_adapter.py::test_real_jenny_matches_reference_outputs` |

Le solveur n'a présenté **aucun défaut** à l'exécution. Les pièges connus,
comme le zéro négatif, signe(0) ou un Δ minuscule arrondi à 0 en flottants,
ont été traités dès la conception et sont verrouillés par des tests de
non-régression.

## 10. Limites

- Pairwise couvre 100 % des paires mais seulement 22,4 % des triplets.
- La matrice 5 × 5 × 5 ne contient ni décimaux ni valeurs extrêmes : ceux-ci
  sont couverts par les cas ciblés et Hypothesis.
- Les racines irrationnelles sont validées par tolérance : cela prouve leur
  proximité avec la valeur exacte, pas l'égalité.
- Compilé tel quel, Jenny dépend de la plateforme (`unsigned long` sur 32 ou
  64 bits). Le correctif de portabilité (A7) rend les combinaisons identiques
  sous Windows et Ubuntu ; la couverture est de toute façon revérifiée à
  chaque exécution.
- Aucune stratégie de test ne prouve l'absence de défauts.

## 11. Conclusion

Le solveur est correct sur l'ensemble des scénarios exécutés, et il rejette
explicitement les entrées invalides. Pour le vérifier, aucune stratégie ne
suffit seule : il faut les combiner. Jenny réduit l'effort (28 cas au lieu de
125) tout en garantissant 100 % des paires. Les cas ciblés et les propriétés
couvrent ce que la combinatoire ne garantit pas. L'oracle indépendant rend
chaque verdict crédible, et l'analyse de mutation **mesure** l'efficacité de
chaque stratégie au lieu de la supposer.

## 12. Reproduire

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1
powershell -ExecutionPolicy Bypass -File tools\run_validation.ps1
```

```bash
# Ubuntu
bash tools/setup_ubuntu.sh --apt
bash tools/run_validation.sh
```
