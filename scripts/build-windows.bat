@echo off
REM Build script for Windows

echo ==========================================
echo  Building JD Automation System - Windows
echo ==========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Installing npm dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install npm dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Bundling Python runtime...
python scripts\bundle-python.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to bundle Python
    pause
    exit /b 1
)

echo.
echo [3/4] Building Electron app for Windows...
call npm run build:win
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Electron app
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo ==========================================
echo  Build successful!
echo ==========================================
echo.
echo Your installers are in the 'dist' folder:
dir /b dist\*.exe 2>nul
echo.
pause
