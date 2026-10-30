# Guide de soutenance — présentation de 5 minutes

Ce guide donne, minute par minute, **ce qu'il faut dire** (phrases simples) et
**ce qu'il faut montrer** à l'écran. Tous les chiffres cités ont été mesurés
lors de l'exécution réelle du projet (voir `reports/rapport_validation.md`).

## Avant la séance (préparation, 2 minutes)

Sur l'ordinateur de soutenance (Ubuntu) — la veille, lancer une fois
`bash tools/setup_ubuntu.sh --apt` (voir README) ; le jour même :

```bash
cd ~/quadratic-testing-lab
source .venv/bin/activate
python -m quadratic_lab jenny        # doit finir par « Jenny est opérationnel. »
python launch_gui.py                 # ouvrir la fenêtre et la laisser prête
```

Sous Windows, remplacer `source .venv/bin/activate` par
`.\.venv\Scripts\Activate.ps1`. Les combinaisons Jenny (5 cas Uniwise,
28 cas Pairwise, PAIR-020…) sont identiques sur les deux systèmes.

Garder un second terminal ouvert pour le plan B (CLI).

## Déroulé minute par minute

### 0:00 – 0:30 — Introduction

**À dire :**
« Mon projet s'appelle Quadratic Testing Lab. Il répond à deux questions.
La question mathématique : est-ce que mon programme calcule correctement les
solutions de a x² + b x + c = 0 ? Et la question de génie logiciel : comment
le prouver avec une stratégie de tests rigoureuse ? Pour cela j'utilise le
vrai outil Jenny, les tests Uniwise et Pairwise, et un oracle indépendant. »

**À montrer :** la fenêtre QUADRATIC TESTING LAB, l'en-tête
« Jenny : opérationnel » avec le chemin de `jenny.exe`.

### 0:30 – 1:45 — Le solveur et ses cas mathématiques (étapes 1 à 5)

**À montrer :** bouton **« Étape suivante ▶ »** cinq fois.

| Étape | Équation | À dire |
|---|---|---|
| 1 | x² - 3x + 2 = 0 | « Cas simple : (x - 1)(x - 2), racines 1 et 2. En bas, l'oracle indépendant confirme : conforme. » |
| 2 | x² - x - 1 = 0 | « Delta = 5, positif : deux racines irrationnelles, le nombre d'or. Je calcule en Decimal à 50 chiffres avec une formule stable. » |
| 3 | x² + 2x + 1 = 0 | « Delta = 0 exactement : une racine double, -1. Mon discriminant est calculé exactement, donc je n'ai pas besoin de tolérance pour dire qu'il est nul. » |
| 4 | x² + 2x + 5 = 0 | « Delta = -16 : aucune racine réelle. Les racines complexes -1 ± 2i sont affichées seulement à titre d'information. » |
| 5 | 2x - 4 = 0 | « Si a = 0, ce n'est plus du second degré : équation du premier degré, x = 2. Je distingue aussi 0 = 0 (infinité de solutions), c = 0 impossible, et la saisie invalide. » |

**Phrase sur la robustesse :** « Les saisies vides, le texte, NaN, l'infini,
les booléens ou les nombres hors limites sont refusés avec un message clair.
Jamais une erreur n'est transformée en zéro. » (Si le temps le permet : taper
`abc` dans a et cliquer sur Résoudre → « Saisie invalide ».)

### 1:45 – 2:15 — Le problème de l'oracle

**À dire :**
« Pour savoir si un résultat est juste, il faut un oracle. Si je compare mon
programme à lui-même, il répète ses propres erreurs. Mon oracle est donc
indépendant : il n'importe pas le solveur, il calcule avec des fractions
exactes et une racine carrée entière à 120 chiffres, avec une autre formule.
Il vérifie la catégorie, le discriminant exact, les racines à 10⁻⁴⁰ près, le
résidu et les relations de Viète. Et je teste l'oracle lui-même : il détecte
des résultats volontairement faux. »

### 2:15 – 3:30 — Jenny, Uniwise et Pairwise (étapes 6 et 7)

**À montrer :** étape 6 (onglet B. Tests Uniwise).

**À dire :**
« Jenny est un programme C de Bob Jenkins, dans le domaine public. J'ai
vérifié sa source, je l'ai compilé moi-même et je l'exécute vraiment : vous
voyez ici la commande `jenny -n1 5 5 5` et sa sortie brute. Chaque
coefficient a cinq valeurs : -10, -1 ou -2, 0, 1 ou 2, 10. Attention, les
lettres de Jenny sont des étiquettes de valeurs : 1c veut dire a = 0, pas le
coefficient c. En Uniwise, Jenny donne 5 cas : chaque valeur apparaît au moins
une fois, couverture 1-way 15 sur 15. »

**À montrer :** étape 7 (onglet C. Tests Pairwise), le tableau « Vérification
des 75 paires ».

**À dire :**
« En Pairwise, `jenny -n2 5 5 5` donne 28 cas. Il y a 3 couples de
coefficients, (a,b), (a,c), (b,c), et 25 paires de valeurs par couple : 75
paires. Mon programme recalcule la couverture lui-même, sans faire confiance
à Jenny : 75 sur 75. Les 28 cas sont tous conformes à l'oracle. »

**Pourquoi Pairwise trouve des problèmes qu'Uniwise ne voit pas (exemple réel) :**
« Imaginons un défaut : le programme oublie de séparer le cas a = 0 et b = 0,
et divise par zéro. Il faut que a et b soient nuls **en même temps** : c'est
une interaction entre deux paramètres. Dans les 5 cas Uniwise, a = 0 apparaît
une seule fois, avec b = 10 : le défaut passe inaperçu. Pairwise garantit que
la paire (a = 0, b = 0) est testée : c'est le cas PAIR-020, avec a = 0, b = 0,
c = 1. Le défaut est détecté. C'est le mutant M04 dans mon analyse. »

### 3:30 – 4:30 — Comparaison des stratégies (étape 8)

**À montrer :** étape 8 (onglet D. Comparaison), les deux tableaux.

**À dire :**
« Voici la comparaison mesurée. Uniwise : 5 cas. Pairwise : 28 cas, soit
22,4 % de l'exhaustif. Exhaustif : 125 cas. Pour mesurer la capacité à
trouver des erreurs, j'ai injecté 10 défauts réalistes dans des copies du
solveur : ce sont des mutants. Uniwise en détecte 6 sur 10 (60 %), Pairwise 8
sur 10 (80 %), l'exhaustif et mes 29 cas ciblés 10 sur 10. »

**Pairwise ne garantit pas l'absence de défauts :**
« Deux mutants survivent à Pairwise. M05 : déclarer que 0 = 0 n'a pas de
solution. Il ne se voit qu'avec le triplet a = 0, b = 0, c = 0, et Pairwise
ne couvre que 28 triplets sur 125. D'ailleurs la catégorie "infinité de
solutions" n'est jamais atteinte par Pairwise. M10 : la formule stable avec
signe(0) = 0. Il faut b = 0 avec a et c de signes opposés : là encore une
interaction de trois valeurs. C'est pour cela que j'ajoute des tests ciblés,
qui exécutent toutes les branches du solveur. »

### 4:30 – 5:00 — Conclusion

**À dire :**
« En résumé : 478 tests automatisés réussis, 100 % des lignes et des branches
du code métier couvertes, Jenny réellement exécuté, Uniwise et Pairwise
vérifiés à 100 % sur la matrice, et tous les cas conformes à un oracle
indépendant. Mais je retiens surtout ceci : moins de tests ne veut pas dire
meilleure méthode, Pairwise ne remplace pas l'exhaustif, et aucun test ne
prouve l'absence de défauts. Une bonne stratégie combine plusieurs méthodes.
Merci. »

## Questions probables de l'enseignant et réponses

**1. Qu'est-ce que le problème de l'oracle, et comment le traitez-vous ?**
C'est la difficulté de savoir quel est le bon résultat attendu. Je le traite
avec un oracle indépendant (fractions exactes, `isqrt` à 120 chiffres, formule
différente, aucun import du solveur, vérifié par un test), avec 29 cas
calculés à la main, avec le résidu et les relations de Viète. Je teste aussi
que l'oracle rejette des résultats faux.

**2. Pourquoi Decimal et pas des float ?**
Les float n'ont que 15 à 17 chiffres et ne représentent pas 0,1 exactement.
Avec Decimal à 50 chiffres et un domaine limité (|x| ≤ 10¹², au plus 12
décimales), le discriminant tient en 49 chiffres : il est **exact**. Exemple
réel : pour a = 1000000.000000000001, b = 2000000, c = 999999.999999999999,
Delta vaut 4·10⁻²⁴ ; en float il vaut 0 et on conclurait à tort à une racine
double.

**3. Pourquoi 28 cas Pairwise et pas 25 ?**
25 = 5 × 5 est la borne inférieure, et elle est atteignable : un carré latin
de 25 cas couvre les 75 paires (je le vérifie dans `test_coverage.py`). Jenny
utilise un algorithme glouton, rapide mais pas toujours optimal : il en
produit 28.

**4. Jenny est-il vraiment exécuté ?**
Oui. La source officielle est vérifiée par SHA-256 et comparée au miroir
GitHub, compilée avec `zig cc`, puis lancée par `subprocess.run` sans shell.
La sortie brute est conservée dans `reports/jenny_*_raw.txt`. Si Jenny est
absent, le programme le dit et s'arrête avec le code 3 : il n'y a aucune
simulation.

**5. Pourquoi ajouter des tests ciblés si Pairwise couvre 100 % des paires ?**
Parce que couvrir les paires de valeurs ne garantit pas de passer par toutes
les branches du programme. Pairwise n'atteint jamais « infinité de
solutions », et deux mutants lui échappent. Les tests ciblés couvrent aussi
ce que la matrice ne contient pas : décimaux, très petits et très grands
nombres, Delta proche de zéro.

**6. Que prouvent 100 % de couverture de code ?**
Que chaque ligne et chaque branche du code métier a été exécutée au moins une
fois par un test. Cela ne prouve pas que le code est juste : une ligne exécutée
peut calculer une valeur fausse. C'est l'oracle qui juge la justesse, et
l'analyse de mutation qui mesure la force des tests.

**7. Pourquoi une tolérance de 10⁻⁴⁰ ?**
Le solveur calcule à 50 chiffres et la formule stable ne cumule que quelques
arrondis (erreur relative de l'ordre de 10⁻⁴⁸). 10⁻⁴⁰ laisse une marge,
mais un calcul en double précision (environ 10⁻¹⁶) échoue. La catégorie et le
discriminant, eux, sont comparés exactement, sans tolérance.

**8. Quelle est la différence entre vérification et validation ?**
Vérifier, c'est contrôler que le programme respecte sa spécification (par
exemple : le discriminant est exact). Valider, c'est contrôler qu'il répond
au besoin réel (il donne les bonnes solutions de l'équation dans tous les cas).

**9. Boîte noire ou boîte blanche ?**
Les deux. Boîte noire : les cas de l'énoncé et les propriétés, sans regarder
le code. Boîte blanche : tests des branches a = 0, b = 0, c = 0, Delta > 0,
= 0, < 0, du calcul exact du discriminant et des exceptions numériques.

**10. Qu'avez-vous corrigé pendant le projet ?**
Des anomalies réelles sont consignées dans le journal du rapport de
validation, chacune avec un test de non-régression. Par exemple : deux faux
échecs venaient de mes tests, qui calculaient la valeur de référence avec
l'arithmétique Decimal par défaut à 28 chiffres (A1) ; et Jenny signale ses
erreurs sur la sortie standard avec le code 0, donc l'adaptateur analyse aussi
le contenu (A3).

**11. Pourquoi ces cinq valeurs par coefficient ?**
Ce sont des classes d'équivalence : grand négatif, petit négatif, zéro, petit
positif, grand positif. Pour b, j'ai pris ±2 au lieu de ±1 pour pouvoir
obtenir Delta = 0 (b² = 4ac avec a = c = ±1).

## Plan B : si l'interface graphique ne démarre pas

Faire la même démonstration en ligne de commande. Le script
`bash samples/demo_cli.sh` (Ubuntu) ou
`powershell -ExecutionPolicy Bypass -File samples\demo_cli.ps1` (Windows)
enchaîne ces étapes en marquant une pause (touche Entrée) entre chacune. On
peut aussi les taper une par une (venv activé) :

```bash
python -m quadratic_lab solve --a 1 --b -3 --c 2
python -m quadratic_lab solve --a 1 --b -1 --c -1
python -m quadratic_lab solve --a 1 --b 2 --c 1
python -m quadratic_lab solve --a 1 --b 2 --c 5 --complexe
python -m quadratic_lab solve --a 0 --b 2 --c -4
python -m quadratic_lab solve --a abc --b 0 --c 1        # saisie invalide (code 2)
python -m quadratic_lab mapping                          # table des étiquettes Jenny
python -m quadratic_lab test --method uniwise
python -m quadratic_lab test --method pairwise           # affiche 75/75
python -m quadratic_lab compare
python -m quadratic_lab mutation
```

Et ouvrir `reports/rapport_validation.md` pour montrer les tableaux.
