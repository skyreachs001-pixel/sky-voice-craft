@echo off
title Sky Voice Craft - Phone Version
color 0A

echo =====================================================================
echo          📱  SKY VOICE CRAFT - PHONE / MOBILE VERSION
echo =====================================================================
echo.

cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist "C:\Users\nauma\miniconda3\python.exe" (
    set "PYTHON_EXE=C:\Users\nauma\miniconda3\python.exe"
)

"%PYTHON_EXE%" launch.py --mode mobile
if %errorlevel% neq 0 (
    echo.
    echo [*] Retrying with default python...
    python launch.py --mode mobile
)
pause
