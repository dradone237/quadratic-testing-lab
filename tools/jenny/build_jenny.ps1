<#
.SYNOPSIS
  Compile Jenny (Bob Jenkins, domaine public) a partir de tools/jenny/src/jenny.c.

.DESCRIPTION
  1. Verifie l'empreinte SHA-256 de la source officielle (burtleburtle.net).
  2. Choisit un compilateur C : gcc, puis clang, puis zig cc (paquet PyPI
     "ziglang" installe dans le .venv du projet).
  3. Produit tools/jenny/bin/jenny.exe puis execute un auto-test (-n1 2).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1
  powershell -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1 -Force
#>
param([switch]$Force)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (Resolve-Path (Join-Path $here "..\..")).Path
$src = Join-Path $here "src\jenny.c"
$binDir = Join-Path $here "bin"
$exe = Join-Path $binDir "jenny.exe"
$expectedHash = "b93222086d8c5e778210f145b730547805662cbb207ace490a373eeb5f7dcb23"

# 1. Integrite de la source
$hash = (Get-FileHash $src -Algorithm SHA256).Hash.ToLower()
if ($hash -ne $expectedHash) {
    throw "Empreinte SHA-256 inattendue pour jenny.c : $hash (attendu $expectedHash)"
}
Write-Host "Source verifiee : $src"
Write-Host "SHA-256 source  : $hash"

# 2. Compilation
if ((Test-Path $exe) -and -not $Force) {
    Write-Host "jenny.exe existe deja (option -Force pour recompiler)."
} else {
    New-Item -ItemType Directory -Force $binDir | Out-Null
    $gcc = Get-Command gcc -ErrorAction SilentlyContinue
    $clang = Get-Command clang -ErrorAction SilentlyContinue
    $py = Join-Path $root ".venv\Scripts\python.exe"
    $hasZig = $false
    if (Test-Path $py) {
        $null = & $py -c "import ziglang"
        $hasZig = ($LASTEXITCODE -eq 0)
    }
    if ($gcc) {
        Write-Host "Compilateur : gcc ($($gcc.Source))"
        & gcc -O3 -std=c99 $src -o $exe
    } elseif ($clang) {
        Write-Host "Compilateur : clang ($($clang.Source))"
        & clang -O3 -std=c99 $src -o $exe
    } elseif ($hasZig) {
        Write-Host "Compilateur : zig cc (paquet PyPI ziglang du .venv)"
        & $py -m ziglang cc -O3 -std=c99 $src -o $exe
    } else {
        throw ("Aucun compilateur C trouve. Solutions : " +
               ".venv\Scripts\python -m pip install ziglang ; ou installer MSYS2 " +
               "(winget install MSYS2.MSYS2 puis pacman -S mingw-w64-ucrt-x86_64-gcc). Voir docs/GUIDE_JENNY.md.")
    }
    if ($LASTEXITCODE -ne 0) { throw "Echec de la compilation (code $LASTEXITCODE)." }
}

# 3. Auto-test : jenny -n1 2 doit produire exactement 1a puis 1b
$output = & $exe -n1 2
$lines = ($output | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ","
if ($lines -ne "1a,1b") { throw "Auto-test echoue : sortie '$lines'" }
Write-Host "Auto-test OK    : jenny -n1 2 => 1a, 1b"
Write-Host "Jenny operationnel : $exe"
Write-Host ("SHA-256 binaire : " + (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower())
