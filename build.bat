@echo off
REM ============================================
REM Build Script for 3D Insole Adapter
REM ============================================
REM This script builds a standalone Windows executable
REM using PyInstaller. Run from the project root directory.
REM
REM Prerequisites:
REM   - Python 3.10+ installed (or existing .venv)
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

REM First check if virtual environment exists and use its Python
set PYTHON_CMD=
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    echo Found existing virtual environment
    goto :python_found
)
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
    echo Found existing virtual environment
    goto :python_found
)

REM Check if Python is available in PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_found
)

REM Check common Python installation locations
if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    goto :python_found
)
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto :python_found
)
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :python_found
)
if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto :python_found
)
REM Check for Python installed via Microsoft Store / pythoncore
for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do (
    if exist "%%D\python.exe" (
        set PYTHON_CMD=%%D\python.exe
        goto :python_found
    )
)

REM No Python found
echo ERROR: Python is not installed or not found
echo.
echo Please either:
echo   1. Create a virtual environment first:
echo      python -m venv .venv
echo      .venv\Scripts\activate
echo      pip install -r requirements.txt
echo   2. Or install Python 3.10+ and add to PATH
echo.
pause
exit /b 1

:python_found
echo [1/5] Checking Python version...
%PYTHON_CMD% --version

REM Check for virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo.
    echo [2/5] Activating existing virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo.
    echo [2/5] Activating existing virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo.
    echo [2/5] Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
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
