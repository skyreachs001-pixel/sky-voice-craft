@echo off
title Sky Voice Craft - Launcher
color 0E

echo =====================================================================
echo          🎙️  SKY VOICE CRAFT - LAUNCHER
echo =====================================================================
echo.

cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist "C:\Users\nauma\miniconda3\python.exe" (
    set "PYTHON_EXE=C:\Users\nauma\miniconda3\python.exe"
)

"%PYTHON_EXE%" launch.py --mode desktop
if %errorlevel% neq 0 (
    echo.
    echo [*] Retrying with default python...
    python launch.py --mode desktop
)
pause
