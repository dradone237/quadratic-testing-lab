# samples — exemples et traces de référence

| Fichier | Contenu |
|---|---|
| `demo_cli.ps1` | Démonstration CLI pas à pas (plan B de la soutenance si la GUI ne démarre pas). |
| `jenny_uniwise_raw.txt` | Sortie brute réelle de `jenny -n1 5 5 5` (Windows, binaire compilé par `build_jenny.ps1`). |
| `jenny_pairwise_raw.txt` | Sortie brute réelle de `jenny -n2 5 5 5`. |
| `rapport_validation_reference.md` | Copie du rapport de validation généré lors de la validation finale. |

Les fichiers `jenny_*_raw.txt` et le rapport sont des **copies figées** des
fichiers produits dans `reports/` lors de la validation finale du projet ;
`reports/` est régénéré à chaque exécution (`python -m quadratic_lab compare`).
Ils servent de référence pour constater qu'une nouvelle exécution donne les
mêmes combinaisons (Jenny est déterministe avec sa graine par défaut).
