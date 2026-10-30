<#
.SYNOPSIS
  Demonstration CLI pas a pas (plan B si l'interface graphique ne demarre pas).
  Appuyer sur Entree entre chaque etape.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File samples\demo_cli.ps1
#>
$root = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"
$out = Join-Path $root "reports\demo"

$steps = @(
    @("1. Equation simple (x-1)(x-2)",              @("solve", "--a", "1", "--b", "-3", "--c", "2")),
    @("2. Delta positif : nombre d'or",             @("solve", "--a", "1", "--b", "-1", "--c", "-1")),
    @("3. Delta nul : racine double",               @("solve", "--a", "1", "--b", "2", "--c", "1")),
    @("4. Delta negatif (+ extension complexe)",    @("solve", "--a", "1", "--b", "2", "--c", "5", "--complexe")),
    @("5. Cas a = 0 : premier degre",               @("solve", "--a", "0", "--b", "2", "--c", "-4")),
    @("5b. Saisie invalide",                        @("solve", "--a", "abc", "--b", "0", "--c", "1")),
    @("6. Jenny reel + table de correspondance",    @("jenny")),
    @("6b. Uniwise : jenny -n1 5 5 5",              @("test", "--method", "uniwise", "--output-dir", $out)),
    @("7. Pairwise : jenny -n2 5 5 5",              @("test", "--method", "pairwise", "--output-dir", $out)),
    @("8. Comparaison + mutation",                  @("compare", "--output-dir", $out))
)

foreach ($step in $steps) {
    Write-Host ""
    Write-Host ("=== " + $step[0] + " ===") -ForegroundColor Cyan
    Write-Host ("> python -m quadratic_lab " + ($step[1] -join " ")) -ForegroundColor DarkGray
    & $py -m quadratic_lab @($step[1])
    Read-Host "Entree pour continuer" | Out-Null
}
