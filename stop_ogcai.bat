@echo off
title OGCAI Shutdown
cd /d "%~dp0"
cls

echo =================================================================
echo             [OGCAI] Stopping OGCAI Services...
echo =================================================================
echo.

:: 1. Stop Backend on Port 8000
echo [1/2] Stopping FastAPI Backend (Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Stop Frontend on Port 5173
echo [2/2] Stopping Frontend Dev Server (Port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo =================================================================
echo   [SUCCESS] OGCAI has been stopped successfully!
echo =================================================================
echo.
timeout /t 2 /nobreak >nul
