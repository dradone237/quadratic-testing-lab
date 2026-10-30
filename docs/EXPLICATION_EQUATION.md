# Explication mathématique — l'équation du second degré

Ce document explique **ce que calcule le programme** et **pourquoi il le
calcule de cette façon**. Les exemples sont ceux des cas ciblés du projet
(`CIB-xx`, définis dans `src/quadratic_lab/oracle.py`) ; les valeurs
numériques citées ont été obtenues en exécutant réellement le programme.

---

## 1. L'équation

On cherche les réels `x` tels que :

```
a·x² + b·x + c = 0
```

`a`, `b`, `c` sont les **coefficients**. Lorsque `a ≠ 0`, c'est une équation
du **second degré** ; lorsque `a = 0`, ce n'en est plus une (voir §4).

## 2. Le discriminant

On met `a` en facteur et on complète le carré :

```
a·x² + b·x + c = a·[ (x + b/(2a))² − (b² − 4ac)/(4a²) ]
```

La quantité qui décide de tout est le **discriminant** :

```
Δ = b² − 4ac
```

L'équation équivaut à `(x + b/(2a))² = Δ/(4a²)` : un carré est positif ou
nul, donc le signe de Δ dit combien de solutions réelles existent.

## 3. Les trois cas lorsque a ≠ 0

| Cas | Conclusion | Formule | Catégorie du programme |
|---|---|---|---|
| Δ > 0 | deux racines réelles distinctes | `x = (−b ± √Δ)/(2a)` | `TWO_REAL_ROOTS` |
| Δ = 0 | une racine réelle double | `x = −b/(2a)` | `DOUBLE_REAL_ROOT` |
| Δ < 0 | aucune racine réelle | — | `NO_REAL_ROOT` |

### Exemples chiffrés (cas ciblés)

- **CIB-01 — Δ > 0** : `x² − 1 = 0`. Δ = 0² − 4·1·(−1) = 4.
  x = (0 ± 2)/2, donc **x1 = −1, x2 = 1**. Factorisation : (x − 1)(x + 1).
- **CIB-13 — Δ > 0, racines irrationnelles** : `x² − x − 1 = 0`. Δ = 1 + 4 = 5.
  x = (1 ± √5)/2 : le nombre d'or **1.61803398874989…** et **−0.618033988749895…**.
- **CIB-02 — Δ = 0** : `x² + 2x + 1 = 0`. Δ = 4 − 4 = 0.
  Racine double **x = −2/2 = −1**. Factorisation : (x + 1)².
- **CIB-03 — Δ < 0** : `x² + 1 = 0`. Δ = 0 − 4 = **−4**.
  x² = −1 est impossible dans ℝ : **aucune racine réelle**.

Le programme renvoie toujours les racines **triées par ordre croissant**
(x1 < x2), y compris lorsque `a < 0` (contrat S-03).

**Extension facultative** : si Δ < 0, le programme peut afficher les racines
complexes `−b/(2a) ± i·√(−Δ)/(2|a|)` (option `--complexe` de la CLI). Par
exemple, pour `x² + 2x + 5` (CIB-29, Δ = −16) : **−1 − 2i** et **−1 + 2i**.
Elles sont **informatives** : la catégorie reste `NO_REAL_ROOT` et les
critères de validation du mode réel ne changent pas.

## 4. Le cas a = 0 (l'équation n'est plus du second degré)

Avec `a = 0`, il reste `b·x + c = 0`. Trois situations sont possibles, et le
programme les distingue explicitement :

| Situation | Équation | Conclusion | Catégorie |
|---|---|---|---|
| a = 0, b ≠ 0 | `b·x + c = 0` | une solution `x = −c/b` | `LINEAR_ROOT` |
| a = 0, b = 0, c = 0 | `0 = 0` | toujours vrai : **infinité** de solutions | `INFINITE_SOLUTIONS` |
| a = 0, b = 0, c ≠ 0 | `c = 0` | toujours faux : **aucune** solution | `NO_SOLUTION` |

Exemples : CIB-04 `2x − 4 = 0` donne x = 2 ; CIB-05 `0 = 0` ; CIB-06 `5 = 0`.

Le discriminant n'a pas de sens si a = 0 : le programme ne le calcule pas
(champ `discriminant = None`) et ne divise jamais par `2a`.

### Ne pas confondre

| Situation | Exemple | Catégorie |
|---|---|---|
| Équation du 2nd degré sans racine réelle | x² + 1 = 0 | `NO_REAL_ROOT` |
| Équation impossible | 5 = 0 | `NO_SOLUTION` |
| Infinité de solutions | 0 = 0 | `INFINITE_SOLUTIONS` |
| Équation du premier degré | 2x − 4 = 0 | `LINEAR_ROOT` |
| Erreur de saisie | a = « abc » | `INVALID_INPUT` |

## 5. Erreurs de saisie

Le programme accepte un nombre décimal **fini**, de valeur absolue
**≤ 10¹²**, avec **au plus 12 chiffres après la virgule** (plus petite valeur
non nulle : 10⁻¹²). Tout le reste est **rejeté avec un message explicite**,
et une saisie invalide n'est **jamais** convertie en zéro. Rejets réels de
`validation.py` :

| Saisie | Raison du rejet |
|---|---|
| `""`, `"   "` | saisie vide |
| `None` | valeur manquante |
| `"abc"`, `"1..2"`, `"--1"`, `"1e"`, `"0x1F"` | format numérique invalide |
| `"1_000"` | séparateur `_` refusé |
| `"١٢"` (chiffres arabo-indiens) | seuls les chiffres ASCII 0–9 sont acceptés |
| `"nan"`, `NaN`, `float('nan')` | NaN n'est pas un nombre |
| `"inf"`, `"-Infinity"`, `float('inf')` | valeur infinie interdite |
| `True`, `False` | un booléen n'est pas un coefficient |
| `[1]`, `1+2j`, `Fraction(1, 3)` | type non pris en charge |
| `"1e13"`, `10**13`, `1e300` | hors limites (\|x\| ≤ 10¹²) |
| `"1e-13"`, `"0.0000000000001"` | trop de décimales (> 12) |
| `0.1 + 0.2` (= 0.30000000000000004) | trop de décimales : refusé plutôt qu'arrondi en silence |
| chaîne de plus de 100 caractères | longueur excessive |

**Virgule décimale française** (CLI et interface graphique uniquement) :
`1,5` est accepté et vaut 1.5 **si et seulement si** la saisie contient une
seule virgule et aucun point. `1,000.5`, `1.000,5` et `1,2,3` sont rejetés
comme **ambigus**. Le signe moins typographique « − » est aussi accepté.

## 6. Précision numérique

### 6.1 Pourquoi pas les flottants ?

Un `float` Python (double précision IEEE 754) a environ 16 chiffres
significatifs et ne représente pas exactement 0.1. Le programme utilise
`decimal.Decimal` avec une **précision interne de 50 chiffres
significatifs** et l'arrondi « au plus proche pair » (`ROUND_HALF_EVEN`).

### 6.2 Le discriminant est calculé EXACTEMENT

C'est le choix central du projet (règle S-21). Dans le domaine accepté,
chaque coefficient s'écrit `N·10⁻¹²` avec `|N| ≤ 10²⁴` (au plus 25 chiffres).
Donc :

- `b²` et `4ac` sont des multiples de `10⁻²⁴` de valeur absolue ≤ `4·10²⁴` ;
- `Δ = M·10⁻²⁴` avec `|M| ≤ 5·10⁴⁸`, soit **au plus 49 chiffres** ;
- 49 chiffres tiennent dans les 50 chiffres de travail : **aucun arrondi**.

Le calcul est fait avec le signal `Inexact` **piégé** : si un arrondi se
produisait malgré tout (coefficients hors domaine), une exception
`NumericalError` serait levée au lieu d'un résultat faux silencieux.

**Conséquence** : le signe de Δ est certain. Le programme n'utilise **aucune
tolérance** pour décider si Δ est nul. Un Δ positif minuscule donne deux
racines distinctes, un Δ négatif minuscule aucune racine réelle.

### 6.3 Le piège du Δ minuscule (CIB-18)

```
a = 1000000.000000000001   b = 2000000   c = 999999.999999999999
```

Calcul exact : `a·c = 10¹² − 10⁻²⁴`, donc `Δ = 4·10¹² − 4·(10¹² − 10⁻²⁴) = 4·10⁻²⁴ > 0`.

| Calcul | Δ obtenu | Conclusion |
|---|---|---|
| Flottants (mesuré) | **0.0** | « racine double » : **faux** |
| Programme (Decimal exact) | **4E-24** | deux racines distinctes : −1 et −0.999999999999999998 |

### 6.4 La formule stable et l'annulation catastrophique

La formule scolaire `(−b + √Δ)/(2a)` soustrait deux nombres presque égaux
quand `b² ≫ |4ac|` : les chiffres significatifs s'annulent.

Exemple mesuré, `x² + 10⁸·x + 1 = 0`, en double précision :

| Méthode | Petite racine |
|---|---|
| Formule scolaire en flottants | **−7.450580596923828e-09** (erreur ≈ 25 %) |
| Programme | **−1E-8** (exact à 50 chiffres près) |

Exemple encore plus sévère, **CIB-16** (`a = 10⁻¹²`, `b = 10¹²`, `c = 10⁻¹²`) :
la formule scolaire en flottants donne une petite racine égale à **0.0** ;
le programme trouve **−1E+24** et **−1E-24**.

Le programme utilise donc la **formule stable** (règle S-23) :

```
q  = −(b + signe(b)·√Δ) / 2
x1 = q / a
x2 = c / q
```

`b` et `signe(b)·√Δ` ont le même signe : on additionne des nombres de même
signe, il n'y a plus d'annulation. La seconde racine vient de la relation
de Viète `x1·x2 = c/a`.

**Validité** : la formule n'est employée que si Δ > 0. Alors `|b| + √Δ > 0`,
donc `q ≠ 0` et les deux divisions sont sûres. Le cas Δ = 0 est traité à
part par `x = −b/(2a)`.

**Le cas b = 0 et signe(0)** : le programme prend **signe(0) = +1**. Avec
signe(0) = 0, on aurait `q = 0` dès que `b = 0`, donc une division par zéro
dans `c/q` (par exemple pour x² − 1 = 0). Ce défaut est justement le
mutant **M10** de l'analyse de mutation (voir `UNIWISE_PAIRWISE.md`).

### 6.5 Le zéro négatif

En `Decimal`, `0 / (−2)` donne `-0`. Pour `x² + 2x = 0` (CIB-22), la formule
stable produit `x2 = c/q = 0/(−2) = −0`. Le programme **normalise** toute
racine nulle en `0` (règle S-04) ; un test de non-régression le vérifie.

### 6.6 L'affichage

- Affichage par défaut : **15 chiffres significatifs**, arrondi au plus
  proche pair ; notation scientifique pour les très grandes ou très petites
  valeurs (`1E+24`, `1E-24`). L'option `--chiffres N` (1 à 50) change ce réglage.
- **Affichage adaptatif** : si deux racines distinctes s'afficheraient
  identiquement, le nombre de chiffres est augmenté automatiquement. Pour
  CIB-18, à 15 chiffres, les deux racines s'écriraient « -1 » ; le
  programme affiche `-1` et `-0.999999999999999998`.
- Le discriminant est affiché **exactement** (il est exact), par exemple
  `999999999999999999999999.999999999999999999999996` pour CIB-16.

### 6.7 Résultats toujours représentables

Dans le domaine accepté, toute racine vérifie `|x| ≤ 2·10²⁴` et toute racine
non nulle `|x| > 10⁻²⁵`. La plage d'exposants de `Decimal` (±999 999) est
largement suffisante : aucun dépassement n'est possible (règle S-24).

## 7. Les relations de Viète

Si `x1` et `x2` sont les deux racines de `a·x² + b·x + c` (a ≠ 0), alors
`a·x² + b·x + c = a·(x − x1)(x − x2)`. En développant :

```
x1 + x2 = −b/a        x1 · x2 = c/a
```

Exemple CIB-07, `x² − 3x + 2` : `1 + 2 = 3 = −(−3)/1` et `1 × 2 = 2 = 2/1`.

Ces relations servent deux fois dans le projet :

1. **dans le calcul** : `x2 = c/q` découle de `x1·x2 = c/a` (formule stable) ;
2. **dans la vérification** : l'oracle contrôle que la somme et le produit
   des racines obtenues valent `−b/a` et `c/a` à 10⁻⁴⁰ près en relatif.
   Un résultat faux qui vérifierait par hasard l'équation pour une racine
   serait ainsi détecté par l'autre relation.

## 8. Résumé de l'algorithme

```
1. Valider a, b, c (sinon INVALID_INPUT avec message).
2. Si a = 0 :
     si b = 0 : c = 0 -> INFINITE_SOLUTIONS ; sinon -> NO_SOLUTION
     sinon    : x = −c/b -> LINEAR_ROOT
3. Sinon : Δ = b² − 4ac (exact)
     Δ < 0 -> NO_REAL_ROOT (+ racines complexes informatives)
     Δ = 0 -> DOUBLE_REAL_ROOT, x = −b/(2a)
     Δ > 0 -> TWO_REAL_ROOTS, formule stable, racines triées
4. Normaliser −0 en 0.
```
