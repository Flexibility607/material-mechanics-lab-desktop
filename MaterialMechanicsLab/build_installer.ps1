$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pnpm = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
if (-not (Test-Path $Pnpm)) {
    $Pnpm = (Get-Command pnpm -ErrorAction Stop).Source
}

& (Join-Path $Root "build_server.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Server build failed."
}

& $Pnpm install
if ($LASTEXITCODE -ne 0) {
    throw "Electron dependency installation failed."
}

$LocalNsis = Join-Path ${env:ProgramFiles(x86)} "NSIS"
$MakeNsis = Join-Path $LocalNsis "Bin\makensis.exe"
$ElectronDist = Join-Path $Root "node_modules\electron\dist\electron.exe"
if (-not (Test-Path $ElectronDist)) {
    throw "Local Electron runtime not found: $ElectronDist"
}

& $Pnpm exec electron-builder --dir --win --x64
if ($LASTEXITCODE -ne 0) {
    throw "Electron application packaging failed."
}

if (Test-Path $MakeNsis) {
    & $MakeNsis /INPUTCHARSET UTF8 (Join-Path $Root "installer.nsi")
} else {
    & $Pnpm exec electron-builder --prepackaged (Join-Path $Root "dist\win-unpacked") --win nsis --x64
}
if ($LASTEXITCODE -ne 0) {
    throw "Windows installer build failed."
}

$Installer = Join-Path $Root "dist\MaterialMechanicsLab-Setup.exe"
if (-not (Test-Path $Installer)) {
    throw "Installer was not found after build."
}
$Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Installer).Hash
$HashFile = Join-Path $Root "dist\SHA256SUMS.txt"
Set-Content -LiteralPath $HashFile -Encoding ASCII -Value "$Hash *MaterialMechanicsLab-Setup.exe"
Write-Host "Installer: $Installer"
Write-Host "SHA256: $Hash"
