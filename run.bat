@echo off
title College Event Management System
cd /d "%~dp0"
echo Starting College Event Management System...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
