#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$previousInstaller = $env:NESTOR_TEST_INSTALLER
$previousPwsh = $env:NESTOR_TEST_PWSH
try {
    $env:NESTOR_TEST_INSTALLER = 'powershell'
    $env:NESTOR_TEST_PWSH = (Get-Process -Id $PID).Path
    $python = Get-Command python3 -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python) { $python = Get-Command python -CommandType Application | Select-Object -First 1 }
    & $python.Source -m unittest discover -s (Join-Path $PSScriptRoot '.') -p test_install.py -v
    $result = $LASTEXITCODE
} finally {
    $env:NESTOR_TEST_INSTALLER = $previousInstaller
    $env:NESTOR_TEST_PWSH = $previousPwsh
}
exit $result
