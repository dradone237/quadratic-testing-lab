# Uniwise, Pairwise, Exhaustif, Ciblés, Propriétés

Ce document compare les stratégies de génération de tests utilisées dans le
projet. Il présente d'abord un exemple fait à la main, puis les **résultats
réellement mesurés** sur le solveur (voir `reports/rapport_validation.md` et
`reports/comparison.json`).

---

## 1. Les stratégies en une phrase

| Stratégie | Garantie | Générateur dans le projet |
|---|---|---|
| **Uniwise** (1-way) | chaque **valeur** de chaque paramètre apparaît au moins une fois | `jenny -n1 5 5 5` |
| **Pairwise** (2-way) | chaque **couple de valeurs** de deux paramètres différents apparaît au moins une fois | `jenny -n2 5 5 5` |
| **3-way** | chaque **triplet** de valeurs apparaît au moins une fois | `jenny -n3 5 5 5` |
| **Exhaustif** | **toutes** les combinaisons | `itertools.product` (Python) |
| **Ciblés** | chaque **branche mathématique** et chaque situation délicate, choisie à la main | `oracle.REFERENCE_CASES` |
| **Propriétés** | une **propriété** vérifiée sur des centaines d'entrées générées | Hypothesis |

Les quatre premières stratégies portent sur une **matrice** de valeurs fixée
à l'avance. Les cas ciblés et les propriétés sortent de cette matrice
(décimaux, très petites et très grandes valeurs, Δ proche de zéro).

## 2. Exemple manuel complet

### 2.1 Le modèle

Un petit modèle à trois dimensions :

| Dimension | Valeurs |
|---|---|
| X | x1, x2 |
| Y | y1, y2 |
| Z | z1, z2, z3 |

Exhaustif : 2 × 2 × 3 = **12** combinaisons.

### 2.2 Uniwise à la main

Il faut que x1, x2, y1, y2, z1, z2, z3 apparaissent chacun au moins une fois.
La plus grande dimension (Z) a 3 valeurs, donc **3 cas au minimum** :

| Cas | X | Y | Z |
|---|---|---|---|
| U1 | x1 | y1 | z1 |
| U2 | x2 | y2 | z2 |
| U3 | x1 | y1 | z3 |

Les 7 valeurs sont présentes : couverture 1-way de **7/7**.

### 2.3 Combien de paires faut-il couvrir ?

Le nombre de paires est la **somme, pour chaque couple de dimensions, du
produit de leurs tailles** :

```
(X,Y) : 2 × 2 = 4
(X,Z) : 2 × 3 = 6
(Y,Z) : 2 × 3 = 6
Total : 16 paires
```

Paires couvertes par le jeu Uniwise ci-dessus :

| Couple | Paires couvertes | Paires manquantes |
|---|---|---|
| (X,Y) | (x1,y1), (x2,y2) | **(x1,y2), (x2,y1)** |
| (X,Z) | (x1,z1), (x2,z2), (x1,z3) | (x2,z1), (x1,z2), (x2,z3) |
| (Y,Z) | (y1,z1), (y2,z2), (y1,z3) | (y2,z1), (y1,z2), (y2,z3) |

Le jeu Uniwise couvre **8/16** paires. Par exemple, la paire **(x1, y2)** n'est
jamais testée. Un défaut qui ne se manifeste que lorsque X = x1 **et** Y = y2
passerait inaperçu.

### 2.4 Pairwise à la main

La borne inférieure est le produit des deux plus grandes dimensions :
3 × 2 = **6 cas**. On place chaque valeur de Z face aux couples (X,Y) en les
alternant :

| Cas | X | Y | Z |
|---|---|---|---|
| P1 | x1 | y1 | z1 |
| P2 | x2 | y2 | z1 |
| P3 | x1 | y2 | z2 |
| P4 | x2 | y1 | z2 |
| P5 | x1 | y1 | z3 |
| P6 | x2 | y2 | z3 |

Vérification :

- (X,Y) : (x1,y1), (x2,y2), (x1,y2), (x2,y1), soit **4/4** ;
- (X,Z) : x1 et x2 apparaissent chacun avec z1, z2 et z3, soit **6/6** ;
- (Y,Z) : y1 et y2 apparaissent chacun avec z1, z2 et z3, soit **6/6**.

**16/16 paires avec 6 cas au lieu de 12.** Mais le triplet (x1, y2, z1), par
exemple, n'est pas testé : Pairwise **ne couvre pas tous les triplets**.

## 3. Résultats réels du projet

Matrice : 3 coefficients (a, b, c) × 5 valeurs. Exhaustif : 5³ = **125** cas.
Paires : 3 couples × (5 × 5) = **75**. Triplets : **125**.

### 3.1 Tableau comparatif (mesuré)

| Méthode | Cas | % de l'exhaustif | 1-way | 2-way | 3-way | Catégories atteintes | Réussis | Score de mutation |
|---|---|---|---|---|---|---|---|---|
| Uniwise | 5 | 4.0 % | 15/15 | 15/75 (20 %) | 5/125 | 4/6 | 5/5 | **60 %** |
| Pairwise | 28 | 22.4 % | 15/15 | **75/75 (100 %)** | 28/125 (22.4 %) | 5/6 | 28/28 | **80 %** |
| 3-way (Jenny -n3) | 125 | 100 % | 15/15 | 75/75 | 125/125 | 6/6 | 125/125 | **100 %** |
| Exhaustif | 125 | 100 % | 15/15 | 75/75 | 125/125 | 6/6 | 125/125 | **100 %** |
| Ciblés | 29 | 23.2 % | 9/15 | 17/75 | 6/125 | 6/6 | 29/29 | **100 %** |

Les 312 cas exécutés sont conformes à l'oracle indépendant. Les cas ciblés
ont volontairement peu de couverture t-wise : ils sont presque tous **hors**
de la matrice (décimaux, valeurs extrêmes).

### 3.2 Observations

- **Uniwise** : 5 cas, le minimum théorique (5 valeurs par dimension). Les
  15 valeurs sont présentes, mais seulement 15 des 75 paires (chaque cas
  couvre 3 paires). Catégories non atteintes : `INFINITE_SOLUTIONS` et
  `NO_SOLUTION`.
- **Pairwise** : 28 cas. La borne inférieure est 5 × 5 = 25, et un carré
  latin d'ordre 5 l'atteint (`tests/test_coverage.py`, 25 cas, 75/75 paires).
  Jenny, algorithme **glouton**, en produit 28 : il n'est pas optimal, mais
  la couverture est complète et vérifiée indépendamment.
- Les **5 premières lignes** de `jenny -n2` sont identiques aux 5 lignes de
  `jenny -n1` : Jenny couvre d'abord les valeurs seules, puis complète les
  paires. Le jeu Pairwise contient donc le jeu Uniwise.
- **Catégorie manquante en Pairwise : `INFINITE_SOLUTIONS`.** Seul le triplet
  (a, b, c) = (0, 0, 0) mène à « 0 = 0 ». C'est une interaction d'**ordre 3** :
  les paires (a=0, b=0), (a=0, c=0) et (b=0, c=0) sont bien couvertes, mais
  jamais dans le même cas.
- **`jenny -n3 5 5 5` produit 125 cas = l'exhaustif** : avec 3 dimensions,
  couvrir tous les triplets revient à tout tester.

## 4. Ce que révèle l'analyse de mutation

Chaque mutant est une copie du solveur contenant un défaut injecté. Il est
« tué » si au moins un cas de la stratégie le fait échouer face à l'oracle.

| Mutant | Défaut injecté | Déclencheur | Uniwise | Pairwise | 3-way | Exhaustif | Ciblés |
|---|---|---|---|---|---|---|---|
| M01 | Signe du discriminant inversé | a ≠ 0 et c ≠ 0 | tué | tué | tué | tué | tué |
| M02 | Δ = 0 traité comme négatif | Δ = 0 | tué | tué | tué | tué | tué |
| M03 | Cas a = 0 non traité | a = 0 (1-way) | tué | tué | tué | tué | tué |
| M04 | a = 0 et b = 0 non distingués | paire (a=0, b=0) (2-way) | **survit** | tué | tué | tué | tué |
| M05 | 0 = 0 déclaré sans solution | triplet (0, 0, 0) (3-way) | **survit** | **survit** | tué | tué | tué |
| M06 | Racine double −b/a au lieu de −b/(2a) | Δ = 0 avec b ≠ 0 | **survit** | tué | tué | tué | tué |
| M07 | Formule scolaire en double précision | racine non exacte en binaire | tué | tué | tué | tué | tué |
| M08 | x = c/b au lieu de −c/b | a = 0, b ≠ 0, c ≠ 0 | tué | tué | tué | tué | tué |
| M09 | Δ négatif ignoré (√\|Δ\|) | Δ < 0 | tué | tué | tué | tué | tué |
| M10 | Formule stable avec signe(0) = 0 | b = 0 et a·c < 0 (3-way) | **survit** | **survit** | tué | tué | tué |
| **Score** | | | **60 %** | **80 %** | **100 %** | **100 %** | **100 %** |

### 4.1 Pourquoi Pairwise trouve ce qu'Uniwise rate

**M04** traite `0·x + c = 0` comme une équation linéaire et divise par
`b = 0`. Il faut un cas où **a = 0 et b = 0 en même temps** : c'est une
**paire**. Les 5 cas Uniwise contiennent a = 0 une seule fois (UNI-003 :
a = 0, b = 10, c = −1) : la paire (a=0, b=0) n'y figure pas, et le mutant
survit. Pairwise garantit la présence de cette paire : PAIR-008 (0, −10, 0)
la contient en partie, et PAIR-020 (0, 0, 1) la contient exactement. Le
mutant plante, il est tué.

De même, **M06** (racine double fausse) n'est révélé que par un cas où Δ = 0
avec b ≠ 0, par exemple (1, 2, 1). Uniwise n'a que (1, 0, 0), pour lequel la
racine double vaut 0 avec les deux formules. Pairwise contient PAIR-018
(1, 2, 1).

C'est l'argument central du Pairwise : beaucoup de défauts naissent de
l'**interaction de deux paramètres**. Uniwise vérifie chaque valeur
isolément et ne voit pas ces interactions.

### 4.2 Pourquoi Pairwise ne garantit pas l'absence de défauts

- **M05** (« 0 = 0 » déclaré sans solution) ne se déclenche que sur le
  triplet **(0, 0, 0)**. Aucun des 28 cas Pairwise ne le contient : le mutant
  survit.
- **M10** (signe(0) = 0 dans la formule stable) ne se déclenche que si
  **b = 0 et a, c de signes opposés** (Δ = −4ac > 0). Les 28 cas Pairwise
  avec b = 0 sont (1, 0, 0) (Δ = 0), (−10, 0, −1), (−1, 0, −10), (10, 0, 10)
  (Δ < 0) et (0, 0, 1) (a = 0). Aucun n'a Δ > 0 : le mutant survit.

Ce sont des interactions d'**ordre 3**. Pairwise garantit les paires, pas les
triplets. Les **cas ciblés** les détectent : CIB-05 (0, 0, 0) tue M05, CIB-01
(1, 0, −1) tue M10.

## 5. Conclusions

1. **Uniwise** est peu coûteux (5 cas), mais aveugle aux interactions.
2. **Pairwise** couvre toutes les paires avec 22.4 % de l'exhaustif et
   détecte les défauts d'interaction d'ordre 2. Il **ne garantit pas**
   l'absence de défauts : deux mutants d'ordre 3 lui échappent ici.
3. **L'exhaustif** reste possible pour 125 cas, mais devient impraticable
   dès que le nombre de paramètres ou de valeurs augmente (vᵏ).
4. **Moins de tests ne signifie pas meilleure méthode** : le nombre de cas
   doit être lu avec la couverture des paires et des triplets, les
   catégories atteintes et le score de mutation.
5. **Les cas ciblés sont indispensables** : 29 cas choisis à partir de la
   structure mathématique atteignent les 6 catégories et tuent les 10
   mutants. Ils couvrent aussi ce que la matrice ignore : décimaux, valeurs
   extrêmes, Δ minuscule.
6. **Les tests par propriétés** explorent des centaines d'entrées hors
   matrice et vérifient des lois (Viète, invariance d'échelle, permutation
   des racines) plutôt que des valeurs.

Une bonne stratégie **combine** ces approches. Aucune, seule, ne prouve que
le programme est correct.
