# Guide Jenny

Ce guide explique ce qu'est Jenny, d'où vient l'exécutable utilisé dans le
projet, comment le compiler sous Windows, comment il fonctionne et comment ses
combinaisons deviennent des cas de test.

## 1. Qu'est-ce que Jenny ?

Jenny est un **générateur de tests combinatoires** écrit en langage C par
**Bob Jenkins** en mars 2003. Il est placé dans le **domaine public** : la
ligne 3 de `jenny.c` indique « By Bob Jenkins, March 2003. Public domain. ».
On peut donc le copier, le compiler et le redistribuer librement.

Son rôle : on lui décrit des **dimensions** (ici les coefficients a, b, c),
chacune avec un nombre de **valeurs** possibles. Il produit alors un petit
ensemble de tests qui couvre toutes les combinaisons de *n* valeurs prises
dans *n* dimensions différentes :

- `-n1` : chaque valeur apparaît au moins une fois (**Uniwise**, 1-way) ;
- `-n2` : chaque paire de valeurs apparaît au moins une fois (**Pairwise**, 2-way) ;
- `-n3` : chaque triplet de valeurs apparaît au moins une fois (3-way).

Jenny est un algorithme **glouton** : il ne cherche pas le nombre minimal
absolu de tests, mais un nombre proche du minimum, très rapidement.

## 2. Provenance vérifiée

| Élément | Valeur |
|---|---|
| Source de référence | <https://burtleburtle.net/bob/c/jenny.c> (page : <https://burtleburtle.net/bob/math/jenny.html>) |
| SHA-256 de la source utilisée | `b93222086d8c5e778210f145b730547805662cbb207ace490a373eeb5f7dcb23` |
| Miroir comparé | <https://github.com/ligurio/jenny>, commit `eedabf4fb4f5dc8a7dc7e648d7f05cb4e48fc289` |
| SHA-256 du `jenny.c` du miroir | `8314000e1d124d7b0d8230dc8d2ae1d8da94c8387385e5139d985c6692c9098a` |

Les deux fichiers ont été comparés ligne à ligne. Les différences sont
**uniquement cosmétiques** : `%d` remplacé par `%lu` dans des messages
d'erreur, variables inutilisées supprimées, espaces en fin de ligne. Aucune
ligne de l'algorithme n'est modifiée. Le projet utilise la **source officielle**
sans modification, copiée dans `tools/jenny/src/jenny.c`.

Le détail complet est dans [tools/jenny/SOURCE.md](../tools/jenny/SOURCE.md).
Le binaire compilé n'est pas versionné (`.gitignore`) : il est toujours
reconstruit à partir de la source vérifiée.

## 3. Compilation sous Windows

### 3.1 Méthode utilisée dans le projet : `zig cc`

Le poste de développement ne disposait d'aucun compilateur C (ni GCC, ni
clang, ni Visual Studio). La solution retenue est la moins intrusive :
**`zig cc`**, un compilateur C basé sur clang/LLVM, distribué par la Zig
Software Foundation sous forme du paquet PyPI officiel `ziglang`. Il s'installe
**dans le `.venv` du projet**, sans rien modifier au système.

```powershell
# 1. Installer le compilateur dans l'environnement virtuel
.\.venv\Scripts\python.exe -m pip install ziglang

# 2. Compiler (vérification SHA-256 + compilation + auto-test)
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1

# Recompiler même si jenny.exe existe déjà
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1 -Force
```

Le script `build_jenny.ps1` :

1. calcule le SHA-256 de `tools/jenny/src/jenny.c` et **refuse de compiler**
   s'il ne vaut pas `b93222…cb23` ;
2. choisit un compilateur dans l'ordre : `gcc`, puis `clang`, puis `zig cc` ;
3. compile avec `-O3 -std=c99` vers `tools/jenny/bin/jenny.exe` ;
4. exécute un **auto-test** : `jenny -n1 2` doit afficher exactement `1a` puis `1b`.

Résultat obtenu (zig 0.16.0) : compilation réussie avec 15 avertissements
bénins, tous présents dans la source d'origine (formats `%d` pour des
`unsigned long`, boucles `for (i; …)` dont la première expression est sans
effet). Auto-test réussi.

### 3.2 Alternative : GCC avec MSYS2

Si l'on préfère GCC :

```powershell
# Installer MSYS2
winget install MSYS2.MSYS2
```

Puis, dans le terminal **MSYS2 UCRT64** :

```sh
pacman -S mingw-w64-ucrt-x86_64-gcc
cd "/c/Users/<vous>/Desktop/ProjetM2/quadratic-testing-lab"
gcc -O3 -std=c99 tools/jenny/src/jenny.c -o tools/jenny/bin/jenny.exe
# ou, avec vérification SHA-256 et auto-test :
sh tools/jenny/build_jenny.sh
```

Si `gcc` est ensuite ajouté au PATH Windows, `build_jenny.ps1` l'utilisera
automatiquement en priorité.

### 3.3 Compilation sous Ubuntu

```bash
sudo apt install -y gcc
sh tools/jenny/build_jenny.sh        # produit tools/jenny/bin/jenny
```

Le script vérifie le SHA-256 de la source, mesure la taille de
`unsigned long`, compile, exécute l'auto-test et contrôle la
reproductibilité : il doit afficher « identique a la reference Windows
(5 cas Uniwise, 28 cas Pairwise) ».

**Correctif de portabilité (constaté sous Ubuntu 24.04, gcc 13).** Compilé
tel quel sous Linux 64 bits, Jenny produit d'autres combinaisons : `-n1`
donne d'autres lignes et `-n2` donne 29 cas au lieu de 28. La cause est la
ligne `typedef unsigned long ub4;` : « ub4 » signifie « 4 octets », or
`unsigned long` fait 8 octets sous Linux 64 bits, ce qui change le générateur
pseudo-aléatoire. Le script compile donc une **copie**
(`tools/jenny/build/jenny_portable.c`) où seules les deux définitions
`ub4`/`sb4` passent en `unsigned int`/`signed int`, conformément à leur nom.
Les sorties `-n1`, `-n2`, `-n3` et avec graine ont été vérifiées **identiques
octet par octet** à celles de Windows. La source officielle n'est jamais
modifiée. Pour compiler la source brute (et observer la différence) :
`JENNY_RAW_SOURCE=1 sh tools/jenny/build_jenny.sh`.

### 3.4 Vérifier l'installation

```powershell
.\tools\jenny\bin\jenny.exe -n2 5 5 5
python -m quadratic_lab jenny
```

La commande `python -m quadratic_lab jenny` affiche le chemin de
l'exécutable, son empreinte SHA-256, celle de la source, le résultat de
l'auto-test et un essai `jenny -n1 5 5 5`. Elle se termine par
« Jenny est opérationnel. ».

## 4. Fonctionnement

### 4.1 Arguments

| Argument | Rôle |
|---|---|
| nombre sans tiret (2 à 52) | une **dimension** et son nombre de valeurs ; les dimensions sont numérotées 1, 2, 3… dans l'ordre |
| `-nN` | force des interactions à couvrir (1, 2, 3…) ; défaut : 2 |
| `-sN` | **graine** du générateur pseudo-aléatoire |
| `-w…` | *without* : interdire une combinaison (ex. `-w1a2b`) |
| `-ofichier` | réutiliser des tests déjà écrits et compléter la couverture |
| `-h` | aide |

Les valeurs d'une dimension sont nommées automatiquement **a, b, c, … z,
puis A … Z** (52 au maximum).

Dans ce projet : trois dimensions de cinq valeurs, donc `5 5 5`.

| Méthode | Commande |
|---|---|
| Uniwise | `jenny -n1 5 5 5` |
| Pairwise | `jenny -n2 5 5 5` |
| 3-way (information) | `jenny -n3 5 5 5` |

### 4.2 Sortie réelle

Chaque ligne est un test : un espace, puis une étiquette par dimension, puis
un espace final, avec des fins de ligne Windows (CRLF). Sortie réelle de
`jenny -n1 5 5 5` sur le binaire compilé :

```
 1a 2d 3a
 1b 2b 3e
 1c 2e 3b
 1d 2c 3c
 1e 2a 3d
```

Résultats mesurés sur ce binaire :

| Commande | Lignes produites | Commentaire |
|---|---|---|
| `jenny -n1 5 5 5` | 5 | égal au minimum théorique (5 valeurs par dimension) |
| `jenny -n2 5 5 5` | 28 | minimum théorique 25 (5 × 5) ; Jenny est glouton |
| `jenny -n3 5 5 5` | 125 | avec 3 dimensions, couvrir tous les triplets = l'exhaustif |

On observe aussi que les 5 premières lignes de `-n2` sont exactement celles
de `-n1` : Jenny couvre d'abord les valeurs seules, puis complète avec les
paires (vérifié par `tests/test_integration.py`).

## 5. Conversion des combinaisons en cas de test

### 5.1 Table de correspondance

| Étiquette | Coefficient | Valeur | Étiquette | Coefficient | Valeur | Étiquette | Coefficient | Valeur |
|---|---|---|---|---|---|---|---|---|
| 1a | a | -10 | 2a | b | -10 | 3a | c | -10 |
| 1b | a | -1 | 2b | b | -2 | 3b | c | -1 |
| 1c | a | 0 | 2c | b | 0 | 3c | c | 0 |
| 1d | a | 1 | 2d | b | 2 | 3d | c | 1 |
| 1e | a | 10 | 2e | b | 10 | 3e | c | 10 |

**Attention** : les lettres a…e sont des **étiquettes de valeurs** de Jenny.
Elles n'ont rien à voir avec les noms des coefficients a, b, c. Par exemple
`1c` signifie « troisième valeur de la dimension 1 », c'est-à-dire **a = 0**
(et pas « coefficient c »).

### 5.2 Exemple

La ligne Jenny `1a 2c 3d` se lit :

- `1a` : dimension 1 (coefficient a), valeur a → **a = -10** ;
- `2c` : dimension 2 (coefficient b), valeur c → **b = 0** ;
- `3d` : dimension 3 (coefficient c), valeur d → **c = 1**.

Le cas de test correspondant est l'équation -10·x² + 0·x + 1 = 0.

Le décodage (`src/quadratic_lab/mapping.py`) passe **uniquement** par cette
table explicite : aucune valeur n'est devinée à partir du nom d'une lettre.
Toute étiquette incohérente (dimension manquante, ordre faux, lettre `f` pour
une dimension de 5 valeurs…) provoque une erreur explicite.

Chaque cas conserve : son identifiant (`UNI-001`, `PAIR-001`…), la méthode,
la combinaison Jenny brute, le numéro de ligne Jenny, les valeurs numériques
et la commande de génération.

Commande utile : `python -m quadratic_lab mapping` affiche la table.

## 6. L'adaptateur Python (`src/quadratic_lab/jenny_adapter.py`)

### 6.1 Localisation de l'exécutable

Ordre de recherche :

1. la variable d'environnement **`QUADRATIC_LAB_JENNY`** : si elle pointe vers
   un fichier absent, c'est une **erreur explicite** (pas de repli silencieux) ;
2. `tools/jenny/bin/jenny.exe`, puis `tools/jenny/bin/jenny` ;
3. `jenny` dans le **PATH**.

### 6.2 Exécution sûre

- arguments construits sous forme de **liste** à partir d'**entiers validés**
  (2 à 52 valeurs par dimension, force entre 1 et le nombre de dimensions,
  graine entre 0 et 2³² - 1) : une chaîne comme `"5; rm -rf /"` est refusée ;
- `subprocess.run(..., shell=False, timeout=...)` : **aucun shell**, délai
  maximal de 20 secondes par défaut ;
- capture de stdout et stderr, contrôle du code de retour **et** du contenu ;
- auto-test avant usage (`verify()` : `jenny -n1 2` → `1a`, `1b`), qui rejette
  un exécutable qui ne serait pas Jenny ;
- la sortie brute est conservée dans `reports/jenny_<méthode>_raw.txt`, avec la
  commande, l'exécutable, le code de retour et la durée.

### 6.3 Exceptions

| Exception | Situation |
|---|---|
| `JennyNotFoundError` | exécutable introuvable |
| `JennyInvalidExecutableError` | le fichier n'est pas un programme exécutable, ou ne se comporte pas comme Jenny |
| `JennyExecutionError` | code de retour non nul, ou message `jenny: …` dans la sortie |
| `JennyTimeoutError` | délai maximal dépassé |
| `JennyOutputError` | sortie vide ou ligne mal formée |
| `JennyCombinationError` | combinaison incohérente (dimension manquante, ordre faux, valeur inexistante) |

Toutes héritent de `JennyError`.

### 6.4 Constat A3 : les erreurs arrivent sur stdout avec le code 0

En testant le binaire réel, on a constaté que Jenny écrit ses messages
d'erreur sur la **sortie standard** et se termine avec le **code 0** :

```
> jenny -n2 5 99 5
jenny: dimensions must be smaller than 52.  99 is too big.
(code de retour : 0)
```

Le code de retour seul ne suffit donc pas. L'adaptateur rejette toute ligne
qui commence par `jenny:` (`JennyExecutionError`). Ce comportement est figé
par le test `tests/test_jenny_adapter.py::test_real_jenny_reports_errors_on_stdout_with_exit_code_zero`.

## 7. Reproductibilité

- **Déterminisme** : sans option `-s`, la graine est fixe. Deux exécutions de
  `jenny -n2 5 5 5` donnent exactement la même sortie (vérifié par
  `test_real_jenny_is_deterministic`). Avec `-s12345`, la sortie change mais la
  couverture reste complète.
- **Plateforme** : le générateur pseudo-aléatoire de Jenny utilise le type
  `unsigned long`. Sous Windows (modèle LLP64), il fait **32 bits** ; sous
  Linux 64 bits (LP64), il fait **64 bits**. Compilée telle quelle, la source
  produit donc d'autres combinaisons sous Ubuntu (29 cas Pairwise mesurés au
  lieu de 28). `build_jenny.sh` applique le correctif de portabilité décrit en
  3.3 : les combinaisons sont alors identiques sur les deux systèmes, ce que
  vérifie `test_real_jenny_matches_reference_outputs` (référence figée dans
  `samples/`). Dans tous les cas, la couverture est **revérifiée
  indépendamment** par `coverage.py` à partir des valeurs décodées.

## 8. Si Jenny est absent

Il n'existe **aucune simulation** de Jenny en Python. Si l'exécutable est
introuvable ou invalide :

- `python -m quadratic_lab generate --method pairwise` affiche
  « Jenny indisponible — génération impossible, aucune simulation n'est
  faite. » et se termine avec le **code de sortie 3** ;
- `python -m quadratic_lab compare` exécute quand même l'exhaustif et les cas
  ciblés, marque Uniwise, Pairwise et 3-way comme **indisponibles** dans le
  rapport, et se termine avec le code 3 ;
- l'interface graphique affiche « Jenny : indisponible » dans l'en-tête ;
- les tests qui exigent le vrai Jenny sont **ignorés** (skip) avec la raison,
  les autres continuent de s'exécuter.
