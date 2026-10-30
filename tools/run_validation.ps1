<#
.SYNOPSIS
  Validation complete : Jenny, suite pytest avec couverture, comparaison des strategies.

.DESCRIPTION
  Produit dans reports/ : pytest_junit.xml, coverage.json, htmlcov/, puis
  tous les rapports de campagne et rapport_validation.md (qui reprend les
  resultats pytest et la couverture mesures juste avant).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\run_validation.ps1
#>
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Environnement .venv absent : voir README.md (installation)." }

if (-not (Test-Path "tools\jenny\bin\jenny.exe")) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File tools\jenny\build_jenny.ps1
}

New-Item -ItemType Directory -Force reports | Out-Null
Write-Host "=== Suite de tests (pytest + couverture du code metier) ==="
& $py -m pytest --cov=quadratic_lab --cov-branch --cov-report=term-missing `
    --cov-report=json:reports/coverage.json --cov-report=html:reports/htmlcov `
    --junitxml=reports/pytest_junit.xml
$pytestCode = $LASTEXITCODE

Write-Host "=== Comparaison des strategies et rapports ==="
& $py -m quadratic_lab compare
$compareCode = $LASTEXITCODE

Write-Host "Code pytest : $pytestCode ; code compare : $compareCode"
exit [Math]::Max($pytestCode, $compareCode)
