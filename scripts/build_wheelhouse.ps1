param(
    [string]$PythonExe = "python",
    [string]$Requirements = "requirements-offline.txt",
    [string]$OutputDir = "wheelhouse",
    [ValidateSet("host", "linux")]
    [string]$TargetPlatform = "host",
    [string]$LinuxPlatformTag = "manylinux2014_x86_64",
    [string]$PythonVersion = "311",
    [string]$Implementation = "cp",
    [string]$Abi = "cp311"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $Requirements)) {
    throw "Requirements file not found: $Requirements"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$pipArgs = @(
    "-m", "pip", "download",
    "--dest", $OutputDir,
    "-r", $Requirements
)

if ($TargetPlatform -eq "linux") {
    $pipArgs += @(
        "--only-binary=:all:",
        "--platform", $LinuxPlatformTag,
        "--python-version", $PythonVersion,
        "--implementation", $Implementation,
        "--abi", $Abi
    )
    Write-Host "Target platform: linux ($LinuxPlatformTag, py$PythonVersion, $Implementation/$Abi)"
}
else {
    Write-Host "Target platform: host (current OS/Python compatibility)"
}

& $PythonExe @pipArgs

Write-Host "Wheelhouse ready at: $OutputDir"
