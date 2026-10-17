# OGCAI Desktop Application Launcher
$ErrorActionPreference = "SilentlyContinue"
$WorkspaceRoot = "D:\OGCAI"
Set-Location $WorkspaceRoot
$env:OLLAMA_MODELS = "D:\ollama\models"

# 1. Verify or Start Ollama Server
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
} catch {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
}

# 2. Check if Backend is already alive
$backendOnline = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    if ($res.status -eq "online") {
        $backendOnline = $true
    }
} catch {
    $backendOnline = $false
}

# 3. Start Backend if not already running
if (-not $backendOnline) {
    Start-Process -FilePath "$WorkspaceRoot\backend\.venv\Scripts\python.exe" `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory "$WorkspaceRoot\backend" `
        -WindowStyle Hidden

    # Poll until backend is responsive (max 30s)
    $retries = 35
    while ($retries -gt 0) {
        Start-Sleep -Milliseconds 800
        try {
            $check = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($check.status -eq "online") {
                break
            }
        } catch {
            $retries--
        }
    }
}

# 4. Launch Standalone Native Window (App Mode)
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edgePath)) {
    $edgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
}

if (Test-Path $edgePath) {
    Start-Process -FilePath $edgePath -ArgumentList "--app=http://127.0.0.1:8000"
} else {
    Start-Process "http://127.0.0.1:8000"
}
