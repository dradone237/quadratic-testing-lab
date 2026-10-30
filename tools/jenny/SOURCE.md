# Provenance de Jenny

| Élément | Valeur |
|---|---|
| Auteur | Bob Jenkins, mars 2003 |
| Licence | **Domaine public** (en-tête de `jenny.c`, ligne 3 : « By Bob Jenkins, March 2003. Public domain. ») |
| Source de référence | <https://burtleburtle.net/bob/c/jenny.c> (page : <https://burtleburtle.net/bob/math/jenny.html>) |
| Date de téléchargement | 30/10/2026 |
| SHA-256 de `src/jenny.c` | `b93222086d8c5e778210f145b730547805662cbb207ace490a373eeb5f7dcb23` |
| Miroir comparé | <https://github.com/ligurio/jenny>, commit `eedabf4fb4f5dc8a7dc7e648d7f05cb4e48fc289` (24/03/2023) |
| SHA-256 du `jenny.c` du miroir | `8314000e1d124d7b0d8230dc8d2ae1d8da94c8387385e5139d985c6692c9098a` |

## Vérification croisée des deux sources

Le fichier officiel et celui du miroir GitHub ont été comparés ligne à ligne
(`diff`, fins de ligne normalisées). Les différences sont **uniquement
cosmétiques** :

- spécificateurs de format `%d` remplacés par `%lu` dans des `printf` de
  messages d'erreur ;
- suppression de variables locales inutilisées (`token`, `k`, `t`, `w`, `ctx`) ;
- espaces en fin de ligne.

Aucune ligne de l'algorithme de génération n'est modifiée. Le projet utilise
la **source officielle** de burtleburtle.net, sans modification.

## Compilation réalisée

- Environnement : Windows 11, aucun GCC installé.
- Compilateur : `zig cc` 0.16.0 (clang/LLVM), distribué par la Zig Software
  Foundation sous forme du paquet PyPI officiel `ziglang`, installé dans le
  `.venv` du projet (aucune modification du système).
- Commande : `python -m ziglang cc -O3 -std=c99 src/jenny.c -o bin/jenny.exe`
  (via `build_jenny.ps1`).
- 15 avertissements bénins, tous présents dans la source d'origine
  (spécificateurs `%d` pour des `unsigned long`, boucles `for (i; …)` dont la
  première expression est sans effet).
- Cible : `x86_64-windows-gnu`. Sous Windows (modèle LLP64), `unsigned long`
  fait 32 bits, comme l'attend le générateur pseudo-aléatoire de Jenny.

## Compilation sous Ubuntu et correctif de portabilité

- Environnement de vérification : Ubuntu 24.04.5 LTS (WSL), gcc 13, Python 3.12.3.
- Constat : compilée telle quelle, la source produit d'autres combinaisons
  (`-n2 5 5 5` → 29 lignes au lieu de 28), car `unsigned long` fait 64 bits
  (modèle LP64) alors que `ub4` signifie « 4 octets ».
- Correctif : `build_jenny.sh` compile une copie
  `build/jenny_portable.c` dans laquelle **seules ces deux lignes** changent :

  ```diff
  -typedef  unsigned long      ub4;
  -typedef  signed   long      sb4;
  +typedef  unsigned int       ub4;
  +typedef  signed   int       sb4;
  ```

  Le script vérifie qu'exactement deux lignes diffèrent. Sous Windows, ce
  changement n'a aucun effet (`int` et `long` font tous deux 32 bits).
- Vérification : sorties de `-n1`, `-n2`, `-n3 5 5 5` et de `-n1 5 5 5 -s12345`
  identiques octet par octet à celles du binaire Windows.
- `JENNY_RAW_SOURCE=1 sh tools/jenny/build_jenny.sh` compile la source brute.

Le binaire n'est pas versionné (`.gitignore`) : il est reconstruit à partir
de la source vérifiée.
