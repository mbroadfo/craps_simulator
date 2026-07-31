# Starts the craps simulator's backend (FastAPI, :8000) and web UI (Vite, :5173)
# if they aren't already running, then opens the game in your browser. If both
# are already up, it just opens the browser - no restart, no wasted work.
#
# Usage:  .\run_app.ps1
# Each server runs in its own new PowerShell window (left open, -NoExit) so you
# can watch its logs or Ctrl+C it directly. Closing those windows stops it.

$RepoRoot = $PSScriptRoot
$BackendPort = 8000
$FrontendPort = 5173

function Test-PortListening($Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

# --- Backend ---
if (Test-PortListening $BackendPort) {
    Write-Host "Backend already running on http://localhost:$BackendPort" -ForegroundColor Green
} else {
    Write-Host "Starting backend on http://localhost:$BackendPort ..." -ForegroundColor Yellow
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    $pythonCmd = if (Test-Path $venvPython) { "& '$venvPython'" } else { "python" }
    Start-Process -FilePath "powershell" -WindowStyle Normal -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$RepoRoot'; $pythonCmd -m uvicorn craps.server.app:app --reload --host 127.0.0.1 --port $BackendPort"
    )
}

# --- Frontend ---
if (Test-PortListening $FrontendPort) {
    Write-Host "Frontend already running on http://localhost:$FrontendPort" -ForegroundColor Green
} else {
    Write-Host "Starting frontend on http://localhost:$FrontendPort ..." -ForegroundColor Yellow
    $webDir = Join-Path $RepoRoot "web"
    Start-Process -FilePath "powershell" -WindowStyle Normal -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$webDir'; npm run dev"
    )
}

# --- Wait for both, then attach (open the browser) ---
Write-Host "Waiting for servers to come online..." -ForegroundColor Cyan
$timeout = 30
$elapsed = 0
while ((-not (Test-PortListening $BackendPort)) -or (-not (Test-PortListening $FrontendPort))) {
    if ($elapsed -ge $timeout) {
        Write-Host "Timed out waiting for servers to start - check the opened windows for errors." -ForegroundColor Red
        exit 1
    }
    Start-Sleep -Seconds 1
    $elapsed++
}

Write-Host "Both servers are up. Opening the game..." -ForegroundColor Green
Start-Process "http://localhost:$FrontendPort"
