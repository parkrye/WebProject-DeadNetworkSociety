@echo off
title Dead Network Society - Stop
echo Stopping Docker services...
cd /d "%~dp0"
docker-compose down
echo Done.
pause
