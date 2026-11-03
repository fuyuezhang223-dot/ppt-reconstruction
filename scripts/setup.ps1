param(
    [switch]$WithImageAnalysis,
    [string]$PythonCommand = "python"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

try {
    & $PythonCommand --version
} catch {
    throw "Python 3.10+ was not found. Install Python and add it to PATH, then rerun this script."
}
$versionText = & $PythonCommand -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $versionText.Split('.')
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 10)) {
    throw "Python 3.10+ is required. Found $versionText."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $PythonCommand -m venv .venv
}
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
if ($WithImageAnalysis) {
    & $venvPython -m pip install -r requirements-image-analysis.txt
}
& $venvPython -m unittest discover -s tests -p "test_*.py" -v
& $venvPython -m tests.smoke_test
Write-Host "Setup complete. Use .\.venv\Scripts\python.exe run_workflow.py --help"
