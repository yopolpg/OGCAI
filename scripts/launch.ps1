# OGCAI Orchestrator & Launcher (PowerShell)
$ErrorActionPreference = "Continue"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "            🚀 Starting OGCAI Personal Copilot                   " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

$WorkspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $WorkspaceRoot

# 1. Run Pre-flight Healthcheck
Write-Host "`n[1/4] Running System Pre-flight Inspector..." -ForegroundColor Cyan
& "$WorkspaceRoot\backend\.venv\Scripts\python.exe" "$WorkspaceRoot\scripts\healthcheck.py"

# 2. Check & Start Ollama if needed
Write-Host "[2/4] Verifying Ollama Local Server..." -ForegroundColor Cyan
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✅ Ollama is running on port 11434" -ForegroundColor Green
} catch {
    Write-Host "  ⚡ Starting Ollama Server in background..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 3. Start FastAPI Backend Server
Write-Host "[3/4] Starting FastAPI Core Engine Backend (Port 8000)..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "$WorkspaceRoot\backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload" `
    -WorkingDirectory "$WorkspaceRoot\backend" `
    -PassThru

# 4. Start Frontend UI
Write-Host "[4/4] Starting Frontend Dev Server (Port 5173)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory "$WorkspaceRoot\frontend" `
    -PassThru

Start-Sleep -Seconds 3

# 5. Open Browser
Write-Host "`n🌐 Opening OGCAI in default browser: http://localhost:5173" -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  🎉 OGCAI is now running!" -ForegroundColor Green
Write-Host "  • Frontend UI: http://localhost:5173" -ForegroundColor White
Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or close the terminal window to exit."
