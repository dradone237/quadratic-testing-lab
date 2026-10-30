# tools/jenny — construction de l'outil Jenny

Jenny est un générateur de tests combinatoires écrit en C par Bob Jenkins
(domaine public). Le projet l'exécute **réellement** ; il n'existe aucune
simulation en Python.

```
tools/jenny/
├── src/jenny.c        source officielle, non modifiée (voir SOURCE.md)
├── bin/jenny.exe      binaire compilé localement (non versionné)
├── build_jenny.ps1    compilation Windows (gcc, clang ou zig cc)
├── build_jenny.sh     compilation MSYS2 / Linux / macOS (gcc)
└── SOURCE.md          provenance, licence, empreintes SHA-256
```

## Compiler sous Windows

```powershell
# 1. Compilateur sans installation système : zig cc dans le .venv
.\.venv\Scripts\python.exe -m pip install ziglang

# 2. Compilation + vérification SHA-256 + auto-test
powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1
```

Le script utilise `gcc` s'il est présent dans le PATH, sinon `clang`, sinon
`zig cc`. Pour installer GCC à la place (alternative) : voir
[docs/GUIDE_JENNY.md](../../docs/GUIDE_JENNY.md), section MSYS2.

## Vérifier

```powershell
.\tools\jenny\bin\jenny.exe -n2 5 5 5
python -m quadratic_lab jenny
```

## Localisation par le programme

`quadratic_lab.jenny_adapter.find_jenny()` cherche, dans l'ordre :

1. la variable d'environnement `QUADRATIC_LAB_JENNY` (erreur explicite si elle
   pointe vers un fichier absent) ;
2. `tools/jenny/bin/jenny.exe` puis `tools/jenny/bin/jenny` ;
3. `jenny` dans le PATH.
