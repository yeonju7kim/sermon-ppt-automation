@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo  SermonPPT  Windows Build
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         IMPORTANT: check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Virtual env
if not exist .venv (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [2/3] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pyinstaller PyQt6 python-pptx python-docx requests beautifulsoup4 lxml
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

echo [3/3] Running PyInstaller...
pyinstaller --clean --noconfirm ppt_automation.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Build complete!
echo  Output: dist\SermonPPT.exe
echo ==========================================
echo.
echo (Optional) Build an installer with Inno Setup:
echo   1. Install Inno Setup from https://jrsoftware.org/isdl.php
echo   2. Open installer.iss in Inno Setup Compiler, then Build, then Compile
echo   3. dist\SermonPPT-Setup.exe will be created
echo.
pause
