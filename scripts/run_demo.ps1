$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python run_workflow.py build --spec examples/v42_component_demo.json --output outputs/v42_demo.pptx
& $python run_workflow.py qa outputs/v42_demo.pptx
Write-Host "Demo finished: outputs/v42_demo.pptx"
