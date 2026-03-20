@echo off
title Dead Network Society - Server
cd /d "%~dp0server"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found. Run: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo [Server] Starting FastAPI on http://localhost:8000
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
pause
