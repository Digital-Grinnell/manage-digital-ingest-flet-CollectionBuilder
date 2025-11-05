@echo off
REM run.bat - Launch script for Manage Digital Ingest Flet application
REM This script handles virtual environment setup and app launch for Windows

setlocal enabledelayedexpansion

echo === Manage Digital Ingest - Launcher ===
echo.

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=.venv"
set "REQUIREMENTS_FILE=python-requirements.txt"

REM Check if virtual environment exists
if not exist "%VENV_DIR%\" (
    echo Virtual environment not found. Creating .venv...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Please ensure Python 3 is installed and in your PATH
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements need to be installed
if exist "%REQUIREMENTS_FILE%" (
    echo Checking dependencies...
    
    REM Check if flet is already installed
    pip show flet >nul 2>&1
    if errorlevel 1 (
        echo Installing dependencies from %REQUIREMENTS_FILE%...
        python -m pip install --upgrade pip
        pip install -r "%REQUIREMENTS_FILE%"
        if errorlevel 1 (
            echo Error: Failed to install dependencies
            pause
            exit /b 1
        )
        echo [OK] Dependencies installed
    ) else (
        echo [OK] Dependencies already installed
    )
    echo.
) else (
    echo Warning: %REQUIREMENTS_FILE% not found
    echo.
)

REM Launch the app
echo === Launching Manage Digital Ingest ===
echo.
flet run app.py

REM Deactivate virtual environment on exit
call "%VENV_DIR%\Scripts\deactivate.bat" 2>nul

echo.
echo Application closed.
pause
