@echo off
title Brew Talk Server
cd /d "%~dp0.."

echo.
echo   ____                     _____     _ _    
echo  | __ ) _ __ _____      __|_   _|_ _| | | __
echo  |  _ \| '__/ _ \ \ /\ / /  | |/ _` | | |/ /
echo  | |_) | | |  __/\ V  V /   | | (_| | |   ^< 
echo  |____/|_|  \___| \_/\_/    |_|\__,_|_|_|\_\
echo.
echo  Voice-Order QR Menu for Cafes
echo  ==============================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.12+
    pause
    exit /b 1
)

REM Create venv if missing
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
)

REM Activate and install
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r backend\requirements.txt --quiet

REM Create data directory
if not exist "data" mkdir data

REM Copy .env if needed
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy backend\.env.example backend\.env >nul
        echo [INFO] Created backend\.env from .env.example
    )
)

REM Start server
echo [3/3] Starting Brew Talk on http://localhost:8000
echo.
echo   Customer menu:  http://localhost:8000/m/1
echo   Kitchen board:  http://localhost:8000/kitchen
echo   Admin panel:    http://localhost:8000/admin
echo   API docs:       http://localhost:8000/docs
echo   Health check:   http://localhost:8000/api/health
echo.
echo Press Ctrl+C to stop.
echo.

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
