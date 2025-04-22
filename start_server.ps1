# Optional: Activate virtual environment if you use one
# $venvPath = ".\.venv\Scripts\Activate.ps1"
# if (Test-Path $venvPath) {
#     Write-Host "🔄 Activating virtual environment..."
#     & $venvPath
# }

Write-Host "🚀 Starting Craps API Server on http://localhost:8000"
Write-Host ""

uvicorn craps.api.app:app --reload --host 127.0.0.1 --port 8000
