$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Workspace = Split-Path -Parent $Root
$ReportRoot = Join-Path ((Get-ChildItem $Workspace -Directory -Filter "03-*" | Select-Object -First 1).FullName) "markdown"
$CalculatorRoot = (Get-ChildItem $Workspace -Directory -Filter "04-*" | Select-Object -First 1).FullName
$ExperimentRoot = (Get-ChildItem $Workspace -Directory | Where-Object {
    Get-ChildItem $_.FullName -Directory -Filter "B011*" -ErrorAction SilentlyContinue
} | Select-Object -First 1).FullName
$ReportDestination = (Split-Path (Split-Path $ReportRoot -Parent) -Leaf) + "\markdown"
$CalculatorDestination = Split-Path $CalculatorRoot -Leaf
$ExperimentDestination = Split-Path $ExperimentRoot -Leaf

if ($env:CODEX_PYTHON -and (Test-Path $env:CODEX_PYTHON)) {
    $Python = $env:CODEX_PYTHON
} else {
    $BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        $Python = $BundledPython
    } else {
        $Python = (Get-Command python -ErrorAction Stop).Source
    }
}

$BuildRoot = Join-Path $Root "build"
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null

$Arguments = @(
    "--noconfirm",
    "--clean",
    "--onedir",
    "--name", "material_mechanics_server",
    "--distpath", (Join-Path $Root "server-dist"),
    "--workpath", (Join-Path $BuildRoot "pyinstaller"),
    "--specpath", $BuildRoot,
    "--add-data", ((Join-Path $Workspace "material_mechanics_assistant\frontend") + ";material_mechanics_assistant\frontend"),
    "--add-data", ($ReportRoot + ";" + $ReportDestination),
    "--add-data", ($CalculatorRoot + ";" + $CalculatorDestination),
    "--add-data", ($ExperimentRoot + ";" + $ExperimentDestination),
    (Join-Path $Workspace "material_mechanics_assistant\backend\server.py")
)

& $Python -m PyInstaller @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Server packaging failed."
}

$Executable = Join-Path $Root "server-dist\material_mechanics_server\material_mechanics_server.exe"
if (-not (Test-Path $Executable)) {
    throw "Packaged server not found: $Executable"
}
Write-Host "Packaged server: $Executable"
