@echo off
title Dead Network Society - Client
cd /d "%~dp0client"

if not exist "node_modules" (
    echo [Client] Installing dependencies...
    npm install
)

echo [Client] Starting Vite dev server on http://localhost:5173
npm run dev
pause
