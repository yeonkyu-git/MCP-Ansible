param(
    [string]$PythonExe = "python",
    [string]$Requirements = "requirements-offline.txt",
    [string]$WheelhouseDir = "wheelhouse",
    [string]$VenvDir = ".venv"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $Requirements)) {
    throw "Requirements file not found: $Requirements"
}
if (!(Test-Path $WheelhouseDir)) {
    throw "Wheelhouse directory not found: $WheelhouseDir"
}

& $PythonExe -m venv $VenvDir

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (!(Test-Path $VenvPython)) {
    throw "Venv python not found: $VenvPython"
}

& $VenvPython -m pip install `
    --no-index `
    --find-links $WheelhouseDir `
    -r $Requirements

Write-Host "Offline install completed in venv: $VenvDir"
Write-Host "Run from package parent directory:"
Write-Host "  $VenvDir\\Scripts\\python.exe -m mcp_ansible.main"
