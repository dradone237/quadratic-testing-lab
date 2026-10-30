# Spécifications — QUADRATIC TESTING LAB

> Phase 1 du projet : ce document fixe le **contrat** du programme **avant**
> l'écriture du code. Les tests (phase 2) sont dérivés de ces règles, et
> chaque règle porte un identifiant (`S-xx`) repris dans le plan de tests.

## 1. Objet

Résoudre dans ℝ l'équation `a·x² + b·x + c = 0` pour des coefficients
décimaux `a`, `b`, `c`, en distinguant explicitement tous les cas
mathématiques, puis démontrer la correction du programme par une stratégie
de tests (Jenny, Uniwise, Pairwise, exhaustif, ciblés, propriétés, mutants).

## 2. Catégories de résultat (énumération `Category`)

| Code | Condition | Résultat attendu |
|---|---|---|
| `TWO_REAL_ROOTS` | a ≠ 0 et Δ > 0 | deux racines réelles distinctes, triées x1 < x2 |
| `DOUBLE_REAL_ROOT` | a ≠ 0 et Δ = 0 | une racine double x = −b/(2a) |
| `NO_REAL_ROOT` | a ≠ 0 et Δ < 0 | aucune racine réelle (racines complexes en option, à titre informatif) |
| `LINEAR_ROOT` | a = 0 et b ≠ 0 | équation du 1er degré, x = −c/b |
| `INFINITE_SOLUTIONS` | a = 0, b = 0, c = 0 | « 0 = 0 » : tout réel est solution |
| `NO_SOLUTION` | a = 0, b = 0, c ≠ 0 | « c = 0 » impossible : aucune solution |
| `INVALID_INPUT` | saisie rejetée | message d'erreur explicite, aucun calcul |

- **S-01** Les sept catégories sont mutuellement exclusives : « zéro racine
  réelle » (`NO_REAL_ROOT`), « équation impossible » (`NO_SOLUTION`) et
  « saisie invalide » (`INVALID_INPUT`) sont trois situations différentes.
- **S-02** Le résultat est une structure (`SolveResult`, dataclass figée)
  contenant : catégorie, coefficients validés, discriminant (si a ≠ 0),
  racines réelles, racines complexes (si Δ < 0), message d'erreur.
- **S-03** Les racines réelles sont renvoyées **triées par ordre croissant**.
- **S-04** Une racine nulle est toujours renvoyée comme `0` (jamais `-0`).

## 3. Domaine d'entrée et validation

- **S-10** Un coefficient valide est un nombre décimal **fini** tel que
  `|x| ≤ 10¹²` et ayant **au plus 12 chiffres après la virgule**
  (plus petite valeur non nulle : `10⁻¹²`).
- **S-11** Types acceptés : `int` (hors booléens), `Decimal` fini, `float`
  fini (converti par sa représentation décimale la plus courte, `repr`),
  chaîne de caractères au format `[+-]chiffres[.chiffres][e±exposant]`
  avec chiffres ASCII uniquement, longueur ≤ 100 caractères.
- **S-12** Sont rejetés avec un message explicite : saisie vide, texte non
  numérique, `NaN`, infinis, booléens, `None`, types non numériques
  (listes, complexes, …), séparateurs ambigus, nombres hors limites,
  nombres ayant trop de décimales, chiffres non ASCII, `_` de groupement.
- **S-13** Une saisie invalide n'est **jamais** convertie silencieusement en
  zéro.
- **S-14** Interface de saisie (CLI et GUI uniquement) : la virgule décimale
  française est acceptée **si et seulement si** la saisie contient une seule
  virgule et aucun point (`1,5` → `1.5`). `1,000.5` ou `1,2,3` sont rejetés
  comme ambigus. Les séparateurs de milliers ne sont pas acceptés.

## 4. Politique numérique

- **S-20** Arithmétique `decimal.Decimal`, précision interne **50 chiffres
  significatifs**, arrondi `ROUND_HALF_EVEN`.
- **S-21** **Le discriminant est calculé exactement.** Justification : sous
  S-10, chaque coefficient s'écrit `N·10⁻¹²` avec `|N| ≤ 10²⁴` ; donc `b²` et
  `4ac` sont des multiples de `10⁻²⁴` de valeur absolue ≤ `4·10²⁴`, et
  `Δ = M·10⁻²⁴` avec `|M| ≤ 5·10⁴⁸` : au plus 49 chiffres, ce qui tient dans
  les 50 chiffres. Le calcul est fait avec le signal `Inexact` **piégé** :
  toute perte d'exactitude lèverait une exception au lieu d'arrondir.
- **S-22** Conséquence : le **signe de Δ est exact**. Aucune tolérance n'est
  utilisée pour décider si Δ est nul. Un Δ positif minuscule (ex. `4·10⁻²⁴`)
  donne deux racines distinctes, un Δ négatif minuscule aucune racine réelle.
- **S-23** Formule stable pour Δ > 0 (sans annulation catastrophique) :
  `q = −(b + sign(b)·√Δ)/2`, `x1 = q/a`, `x2 = c/q`, avec **sign(0) = +1**.
  Validité : si Δ > 0 alors `|b| + √Δ > 0`, donc `q ≠ 0` ; le cas Δ = 0 est
  traité à part par `x = −b/(2a)`.
- **S-24** Les résultats sont toujours représentables : dans le domaine S-10,
  toute racine vérifie `|x| ≤ 2·10²⁴` et toute racine non nulle `|x| > 10⁻²⁵` ;
  la plage d'exposants de `Decimal` (±999 999) est très largement suffisante. Toute
  exception numérique inattendue est convertie en erreur explicite
  (`NumericalError`), jamais masquée.
- **S-25** Affichage : 15 chiffres significatifs par défaut (`ROUND_HALF_EVEN`),
  notation scientifique pour les très grandes ou très petites valeurs. Si deux
  racines distinctes s'afficheraient identiquement, le nombre de chiffres est
  augmenté automatiquement (jusqu'à 50) pour les distinguer.
- **S-26** Extension facultative : pour Δ < 0, les racines complexes
  `−b/(2a) ± i·√(−Δ)/(2|a|)` sont fournies à titre informatif ; elles ne
  changent ni la catégorie ni les critères de validation du mode réel.

## 5. Oracle (problème de l'oracle)

- **S-30** L'oracle est un module **indépendant** du solveur : il n'importe
  pas `solver.py`, utilise l'arithmétique **rationnelle exacte**
  (`fractions.Fraction`) et la racine carrée entière (`math.isqrt`) à
  **120 chiffres**, avec la formule « scolaire » `(−b ± √Δ)/(2a)` (algorithme
  différent de la formule stable du solveur).
- **S-31** Catégorie et discriminant attendus : exacts. Racines : exactes si
  Δ est le carré d'un rationnel, sinon approchées à mieux que 10⁻⁷⁰ en relatif.
- **S-32** Comparaison : catégorie identique, discriminant identique
  (exactement), même nombre de racines, écart relatif ≤ **10⁻⁴⁰** pour chaque
  racine, résidu relatif `|p(x)| / (|a|x² + |b||x| + |c|)` ≤ 10⁻⁴⁰, relations de
  Viète (somme `−b/a`, produit `c/a`) à 10⁻⁴⁰ près en relatif.
- **S-33** Des cas de référence **calculés à la main** (formes closes
  `p + q·√r`) valident l'oracle lui-même.

## 6. Génération combinatoire

- **S-40** Trois dimensions indépendantes (coefficients a, b, c), cinq
  valeurs chacune :

  | Dimension Jenny | Coefficient | a | b | c | d | e |
  |---|---|---|---|---|---|---|
  | 1 | a | −10 | −1 | 0 | 1 | 10 |
  | 2 | b | −10 | −2 | 0 | 2 | 10 |
  | 3 | c | −10 | −1 | 0 | 1 | 10 |

  Les lettres a…e sont des **étiquettes de valeurs Jenny**, sans rapport avec
  les noms des coefficients. `1a 2c 3d` signifie a = −10, b = 0, c = 1.
- **S-41** Uniwise : `jenny -n1 5 5 5`. Pairwise : `jenny -n2 5 5 5`.
  3-way (information) : `jenny -n3 5 5 5`. Exhaustif : `itertools.product`
  (125 cas). Les cas ciblés sont définis à la main.
- **S-42** Jenny est exécuté réellement (`subprocess.run`, sans shell, avec
  délai maximal). Sa sortie brute est conservée. En cas d'absence, la
  génération Jenny est déclarée **indisponible** (exception explicite) : il
  n'y a **aucune simulation**.
- **S-43** Jenny signale ses erreurs sur la sortie standard avec un code de
  retour 0 (constaté sur la version compilée) : l'adaptateur doit donc aussi
  analyser le contenu et rejeter toute ligne commençant par `jenny:`.
- **S-44** Chaque cas conserve : identifiant, méthode, combinaison Jenny,
  numéro de ligne Jenny, valeurs numériques, commande de génération.

## 7. Couverture (indépendante de Jenny)

- **S-50** Couverture t-wise calculée à partir des **valeurs numériques**
  des cas et de la table du domaine (S-40), sans utiliser les étiquettes
  Jenny : 15 valeurs pour 1-way, 75 paires pour 2-way, 125 triplets pour 3-way.
- **S-51** Une campagne n'est déclarée « 100 % Uniwise » (resp. Pairwise)
  que si **toutes** les valeurs (resp. les 75 paires) sont présentes ; les
  éléments manquants sont listés.
- **S-52** La couverture des **catégories mathématiques** atteintes est
  calculée et rapportée séparément : 100 % Pairwise ne garantit pas que
  toutes les branches du solveur sont exécutées.

## 8. Interfaces et rapports

- **S-60** CLI `python -m quadratic_lab` : `solve`, `generate`, `test`,
  `compare`, `mutation`, `mapping`, `jenny`, `gui`. Messages en français,
  codes de sortie : 0 succès, 1 échec de tests, 2 erreur d'utilisation ou
  saisie invalide, 3 Jenny indisponible.
- **S-61** GUI Tkinter à quatre onglets (Résolution, Uniwise, Pairwise,
  Comparaison) + mode Démonstration, appelant les **mêmes modules métier**.
- **S-62** Rapports dans `reports/` (CSV `;` UTF-8 avec BOM pour Excel, JSON,
  Markdown) calculés à partir des résultats réels exécutés.
