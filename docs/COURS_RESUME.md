# Résumé de cours — Vérification, Validation et Tests, appliqués au projet

Chaque notion du cours est reliée à ce que fait concrètement **QUADRATIC
TESTING LAB** : fichier de code, fichier de test ou résultat mesuré.

---

## 1. Vérification et validation

| | Vérification | Validation |
|---|---|---|
| Question | « Construit-on le produit **correctement** ? » | « Construit-on le **bon** produit ? » |
| Référence | la spécification | le besoin réel |
| Dans le projet | le solveur respecte-t-il les règles S-01 à S-62 de `docs/SPECIFICATIONS.md` ? | les solutions renvoyées sont-elles mathématiquement justes pour l'utilisateur ? |
| Moyens | tests unitaires et boîte blanche, couverture de code | oracle indépendant, cas calculés à la main, démonstration |

Exemple : vérifier que le discriminant est calculé avec le signal `Inexact`
piégé relève de la **vérification** (`tests/test_discriminant.py`). Constater
que x² − 3x + 2 donne bien 1 et 2 relève de la **validation**.

## 2. Tests en boîte noire et en boîte blanche

**Boîte noire** : on teste les entrées et les sorties sans regarder le code.
On s'appuie sur la spécification.

- `tests/test_solver.py` : les 8 cas obligatoires et les cas avancés ;
- `tests/test_linear_cases.py` : les cas a = 0 ;
- `tests/test_invalid_inputs.py` : les saisies rejetées ;
- `tests/test_cli.py` : la ligne de commande vue de l'extérieur (y compris
  dans un vrai processus `python -m quadratic_lab`).

**Boîte blanche** : on conçoit les tests à partir de la structure du code
(décisions, branches).

- `tests/test_discriminant.py` : exactitude du calcul interne de Δ, piège
  `Inexact` ;
- décisions testées : `a = 0`, `b = 0`, `c = 0`, `Δ > 0`, `Δ = 0`, `Δ < 0`,
  entrée invalide, exception numérique ;
- `tests/test_regression.py` : `signe(0) = +1` dans la formule stable,
  normalisation de `-0`.

La couverture de code (§10) mesure ce que les tests boîte blanche ont
réellement exécuté.

## 3. Partitions d'équivalence et valeurs limites

**Partition d'équivalence** : on découpe le domaine d'entrée en classes dont
on suppose que tous les éléments se comportent de la même façon ; on teste un
représentant par classe.

Dans le projet, chaque coefficient est partitionné en cinq classes, qui
forment la matrice envoyée à Jenny :

| Classe | a | b | c |
|---|---|---|---|
| grand négatif | −10 | −10 | −10 |
| petit négatif | −1 | −2 | −1 |
| **zéro** | 0 | 0 | 0 |
| petit positif | 1 | 2 | 1 |
| grand positif | 10 | 10 | 10 |

Pour b, ±2 remplace ±1 afin que Δ = 0 soit atteignable (b² = 4ac avec
a = c = ±1).

**Valeurs limites** : les défauts se concentrent aux frontières. Le projet
teste notamment :

- **zéro** et ses écritures (`0`, `"0.0"`, `"-0"`, `"0e5"`, `-0.0`) ;
- les bornes du domaine : `±10¹²` acceptés, `10¹³` et `−3·10¹²` refusés ;
  `10⁻¹²` accepté, `10⁻¹³` refusé ;
- la frontière Δ = 0 : Δ = 4·10⁻¹² (CIB-17), Δ = 4·10⁻²⁴ (CIB-18),
  Δ = −4·10⁻¹² (CIB-19) ;
- les valeurs négatives et positives de chaque coefficient.

**Types de données** : entiers, décimaux, flottants, chaînes, `Decimal`,
booléens (refusés), `None`, listes, complexes et fractions (refusés), NaN et
infinis (refusés). Voir `tests/test_invalid_inputs.py`.

## 4. Le problème de l'oracle

Un **oracle** est le mécanisme qui décide si un résultat est correct. Le
problème : pour un programme de calcul, on ne connaît souvent pas la bonne
réponse. Et un oracle qui réutilise le code testé reproduit ses erreurs.

Réponse du projet (`src/quadratic_lab/oracle.py`) :

1. **Indépendance** : l'oracle n'importe ni `solver.py` ni `validation.py`.
   Un test l'impose en analysant le code source (`tests/test_oracle.py`).
2. **Autre arithmétique** : nombres rationnels exacts (`fractions.Fraction`)
   au lieu de `Decimal`.
3. **Autre racine carrée** : `math.isqrt` sur des entiers mis à l'échelle,
   avec **120 chiffres** au lieu de 50.
4. **Autre formule** : la formule scolaire `(−b ± √Δ)/(2a)` au lieu de la
   formule stable. L'annulation y est absorbée par la précision de 120 chiffres.
5. **Cas calculés à la main** : 29 cas de référence (`CIB-01` à `CIB-29`) dont
   les racines sont des formes closes `p + q·√r`, vérifiées par substitution
   directe dans l'équation. Ils valident **l'oracle lui-même**.
6. **Contrôles complémentaires** : résidu relatif
   `|a·x² + b·x + c| / (|a|x² + |b||x| + |c|)` et relations de Viète
   (somme `−b/a`, produit `c/a`).
7. **Tolérance justifiée** : 10⁻⁴⁰ en relatif. Le solveur travaille à
   50 chiffres et cumule quelques arrondis (erreur ≲ 10⁻⁴⁸) ; l'oracle est
   exact à mieux que 10⁻⁷⁰. Il reste 8 ordres de grandeur de marge, et un
   calcul en double précision (≈ 10⁻¹⁶) est détecté.
8. **Exactitude là où c'est possible** : la catégorie et le discriminant sont
   comparés **exactement**, sans tolérance.
9. **L'oracle est lui-même testé** : on lui soumet des résultats faux
   (mauvaise catégorie, racine fausse de 10⁻²⁸, discriminant faux, racine
   manquante, racines non triées, formule naïve en flottants) et il doit les
   rejeter (`tests/test_oracle.py`).

**Limites** : pour une racine irrationnelle, la tolérance prouve la
**proximité**, pas l'égalité. Un défaut produisant une erreur inférieure à
10⁻⁴⁰ ne serait pas détecté. Les cas de référence ne couvrent que les
situations qu'on a pensé à écrire.

## 5. Tests combinatoires (t-wise)

Avec k paramètres de v valeurs, le test exhaustif demande vᵏ cas (ici
5³ = 125). Les tests combinatoires réduisent ce nombre en garantissant
seulement les interactions jusqu'à un ordre t :

- **1-way (Uniwise)** : chaque valeur apparaît au moins une fois ;
- **2-way (Pairwise)** : chaque couple de valeurs de deux paramètres
  différents apparaît au moins une fois ;
- **t-way** : chaque t-uplet de valeurs apparaît au moins une fois.

Justification empirique (NIST) : la plupart des défauts sont déclenchés par
l'interaction d'un petit nombre de paramètres. Mais « la plupart » ne veut
pas dire « tous ». Le détail figure dans `docs/UNIWISE_PAIRWISE.md`.

## 6. Jenny

Jenny (Bob Jenkins, 2003, domaine public) est un générateur de jeux de tests
combinatoires écrit en C. On lui donne la taille de chaque dimension et la
force d'interaction : `jenny -n2 5 5 5`. Il renvoie des lignes du type
`1a 2c 3d`, où le chiffre est la dimension et la lettre l'étiquette de valeur.

Dans le projet, Jenny est **compilé et exécuté réellement**
(`tools/jenny/build_jenny.ps1`, `src/quadratic_lab/jenny_adapter.py`), sa
sortie brute est conservée et chaque ligne est décodée par une table de
correspondance explicite (`mapping.py`). La couverture est ensuite recalculée
**indépendamment de Jenny** (`coverage.py`). Voir `docs/GUIDE_JENNY.md`.

## 7. Tests par propriétés

Au lieu d'écrire des exemples, on énonce une **propriété** vraie pour toutes
les entrées valides. Un outil (Hypothesis) génère des centaines d'entrées et
cherche un contre-exemple, puis le réduit au plus simple.

Propriétés testées dans `tests/test_properties.py`, sur 200 exemples chacune
avec un profil reproductible (`derandomize=True`) :

- aucune exception inattendue, catégorie toujours valide ;
- accord avec l'oracle indépendant ;
- cohérence entre catégorie et signe exact de Δ ;
- relations de Viète ;
- permutation des racines : construire l'équation à partir de (r1, r2) ou de
  (r2, r1) donne le même résultat, qui retrouve r1 et r2 ;
- invariance par multiplication des trois coefficients par k ≠ 0 (si le
  résultat reste dans le domaine) ;
- racine double exacte pour a(x − r)² ;
- saisies arbitraires : analysées ou rejetées proprement, jamais de plantage.

## 8. Tests de mutation

Un **mutant** est une copie du programme dans laquelle on a injecté un défaut
réaliste. Si un jeu de tests fait échouer le mutant, on dit qu'il le
**tue**. Le **score de mutation** (pourcentage de mutants tués) mesure la
capacité réelle de détection d'un jeu de tests, alors que la couverture ne
mesure que ce qui a été exécuté.

Le projet définit 10 mutants (`src/quadratic_lab/mutation.py`) : signe de Δ
inversé, Δ = 0 traité comme négatif, a = 0 oublié, etc. Résultats mesurés :
Uniwise 60 %, Pairwise 80 %, 3-way 100 %, Exhaustif 100 %, Ciblés 100 %.

## 9. Tests de non-régression

Une fois un défaut corrigé, un test permanent garantit qu'il ne reviendra
pas. `tests/test_regression.py` contient un test par anomalie du journal
(`reporting.ANOMALIES`, repris en section 9 du rapport de validation, qui
fait foi pour la liste complète). Exemples :

- A1 : les opérateurs `Decimal` arrondissent au contexte courant (28 chiffres),
  ce qui avait faussé deux valeurs de référence dans les tests ;
- A2 : un test utilisait un coefficient hors domaine ;
- A3 : Jenny signale ses erreurs sur la sortie standard avec le code de
  retour 0.

S'y ajoutent les défauts évités dès la conception : zéro négatif, signe(0),
Δ minuscule arrondi à 0 en flottants.

## 10. Couverture de code

La couverture mesure la part du code exécutée par les tests :

- **couverture des lignes** : instructions exécutées ;
- **couverture des branches** : pour chaque décision, les deux issues
  (vrai et faux) ont-elles été prises ?

Résultats **mesurés** avec pytest-cov (`tools/run_validation.ps1`) :

| Périmètre | Lignes | Branches |
|---|---|---|
| Code métier (hors interface graphique) | **100 %** (1424/1424) | **100 %** (396/396) |
| Interface graphique (mesurée à part) | 90 % au global (lignes + branches) | — |

Objectifs de l'énoncé : ≥ 95 % des lignes et ≥ 90 % des branches du code
métier. Six blocs défensifs sont exclus de la mesure par `pragma: no cover`
et justifiés dans le code : la commande interactive `gui`, la
reconfiguration d'un flux de sortie, deux gardes `DecimalException`
inatteignables dans le domaine validé, le repli d'affichage de
`format_roots`, et une garde `InvalidOperation` déjà exclue par l'expression
régulière de validation.

**Attention** : 100 % de couverture signifie que tout le code a été
**exécuté**, pas qu'il est **correct**. C'est pourquoi le projet combine la
couverture avec un oracle indépendant et l'analyse de mutation.

## 11. Ce qu'il faut retenir

1. Tester, c'est montrer la présence de défauts, jamais leur absence (Dijkstra).
2. Un test n'a de valeur que si son oracle est fiable : l'oracle doit être
   indépendant et lui-même testé.
3. La couverture combinatoire (1-way, 2-way) porte sur les **entrées** ; la
   couverture de code porte sur le **programme** ; le score de mutation porte
   sur la **capacité de détection**. Ce sont trois mesures différentes.
4. Les stratégies se complètent : combinatoire, cas ciblés, propriétés,
   non-régression.
