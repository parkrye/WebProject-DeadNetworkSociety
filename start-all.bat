@echo off
title Dead Network Society - Launcher
echo ========================================
echo  Dead Network Society - Starting All
echo ========================================
echo.

echo [1/3] Starting Docker services (PostgreSQL + Ollama)...
docker-compose up -d
if errorlevel 1 (
    echo [WARN] Docker failed. Make sure Docker Desktop is running.
)

echo.
echo [2/3] Starting Server...
start "" "%~dp0start-server.bat"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Client...
start "" "%~dp0start-client.bat"

echo.
echo ========================================
echo  Server: http://localhost:8000
echo  Client: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to stop Docker services...
pause >nul
docker-compose down
