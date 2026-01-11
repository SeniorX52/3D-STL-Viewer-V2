@echo off
REM ============================================
REM Build Script for 3D Insole Adapter
REM ============================================
REM This script builds a standalone Windows executable
REM using PyInstaller. Run from the project root directory.
REM
REM Prerequisites:
REM   - Python 3.10+ installed
REM   - pip install -r requirements.txt
REM
REM The resulting executable requires NO Python or
REM development environment to run.
REM ============================================

echo.
echo ========================================
echo   3D Insole Adapter - Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or later
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

REM Check for virtual environment
if exist ".venv" (
    echo.
    echo [2/5] Activating existing virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv" (
    echo.
    echo [2/5] Activating existing virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo.
    echo [2/5] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo.
echo [3/5] Installing/updating dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.

REM Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo [4/5] Building executable with PyInstaller...
echo This may take several minutes...
echo.

REM Build using spec file (more control)
pyinstaller build.spec --clean

echo.
if exist "dist\InsoleAdapter.exe" (
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\InsoleAdapter.exe
    echo.
    echo The executable is fully standalone:
    echo   - No Python required
    echo   - No Blender required
    echo   - No development environment needed
    echo.
    
    REM Check if Inno Setup is installed
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        echo.
        echo [5/5] Creating Windows installer...
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
        
        if exist "installer_output\InsoleAdapter_Setup_1.0.0.exe" (
            echo.
            echo ========================================
            echo   INSTALLER CREATED!
            echo ========================================
            echo.
            echo Installer: installer_output\InsoleAdapter_Setup_1.0.0.exe
            echo.
            echo This installer can be distributed to end users.
            echo.
        )
    ) else (
        echo.
        echo [5/5] Skipping installer creation
        echo       Inno Setup not found at:
        echo       C:\Program Files ^(x86^)\Inno Setup 6\ISCC.exe
        echo.
        echo       To create an installer:
        echo       1. Download Inno Setup from: https://jrsoftware.org/isdl.php
        echo       2. Install it
        echo       3. Run this build script again
        echo       OR run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
        echo.
    )
    
    echo Distribution options:
    echo   1. dist\InsoleAdapter.exe - Single portable executable
    echo   2. installer_output\InsoleAdapter_Setup_*.exe - Windows installer
    echo.
) else (
    echo ========================================
    echo   BUILD FAILED
    echo ========================================
    echo.
    echo Check the output above for errors.
    echo Common issues:
    echo   - Missing dependencies
    echo   - Import errors in code
    echo   - Antivirus blocking PyInstaller
    echo.
)

pause
