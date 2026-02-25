param(
    [string]$PythonExe = "python",
    [string]$Requirements = "requirements-offline.txt",
    [string]$OutputDir = "wheelhouse"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $Requirements)) {
    throw "Requirements file not found: $Requirements"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

& $PythonExe -m pip download `
    --dest $OutputDir `
    -r $Requirements

Write-Host "Wheelhouse ready at: $OutputDir"
