@echo off
title OGCAI Launcher
cd /d "%~dp0"
cls

echo =================================================================
echo             [OGCAI] Personal Local AI Assistant Launcher
echo =================================================================
echo.

:: 1. Run Pre-flight Healthcheck
echo [1/3] Checking System Readiness...
call backend\.venv\Scripts\python.exe scripts\healthcheck.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Healthcheck encountered non-critical issues, proceeding...
)

:: 2. Launch Backend in new window
echo [2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "OGCAI Backend (Port 8000)" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload"

:: 3. Launch Frontend
echo [3/3] Launching Frontend UI on http://localhost:5173 ...
start "OGCAI Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait 3 seconds and launch browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo =================================================================
echo   [READY] OGCAI is running in background windows!
echo   - Frontend: http://localhost:5173
echo   - Backend:  http://localhost:8000
echo =================================================================
echo.
pause
