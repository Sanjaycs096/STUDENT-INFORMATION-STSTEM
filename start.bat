@echo off
title Student Information System
color 0A

echo =====================================================
echo    Student Information System - Local Server
echo =====================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: ---- Check Python installation ----
py --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  ERROR: Python is not installed or not in PATH.
    echo  Download Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('py --version 2^>^&1') do set PY_VER=%%v
echo  Py detected: %PY_VER%

:: ---- Check .env file ----
if not exist ".env" (
    echo.
    echo  WARNING: .env file not found.
    if exist ".env.example" (
        echo  Creating .env from .env.example ...
        copy ".env.example" ".env" >nul
        echo  .env created. Please update SUPABASE_URL and SUPABASE_KEY in .env
    ) else (
        echo  Please create a .env file with SUPABASE_URL and SUPABASE_KEY
    )
    echo.
)

:: ---- Install / upgrade dependencies ----
echo  Installing dependencies from requirements.txt ...
py -m pip install --upgrade -r requirements.txt -q --no-warn-script-location
if errorlevel 1 (
    color 0C
    echo  ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo  Dependencies OK.

:: ---- Create uploads folder if missing ----
if not exist "uploads" (
    mkdir uploads
    echo  Created uploads/ folder.
)

echo.
echo =====================================================
echo   Demo Login Credentials
echo =====================================================
echo.
echo   [ADMIN / FACULTY]
echo     ID       : admin
echo     Password : 123@Admin
echo.
echo   [STUDENT]
echo     Reg No   : DEMO001
echo     Password : demo001
echo.
echo =====================================================
echo   Server starting at http://localhost:5000
echo   Press Ctrl+C to stop the server
echo =====================================================
echo.

:: ---- Start Flask app ----
py app.py

echo.
echo  Server stopped.
pause
