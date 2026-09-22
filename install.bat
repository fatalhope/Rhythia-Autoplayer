@echo off
title Rhythia Auto - Installer

echo ============================================
echo           Dependency Installer
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.10+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detected:
python --version
echo.

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available.
    echo Try reinstalling Python with pip included.
    pause
    exit /b 1
)

echo [OK] pip detected.
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found in the current folder.
    echo Make sure you run this script from the project root.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies from requirements.txt...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Installation complete!
echo ============================================
echo.
echo You can now run the tool with:
echo    python rhythia_auto.py
echo.
echo Remember to run it as Administrator.
echo.

pause