@echo off
REM Chinese TTS Video Generator - Windows Startup Script

echo.
echo ========================================
echo Chinese TTS Video Generator
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.13+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo Warning: FFmpeg is not installed or not in PATH
    echo Video generation will fail without FFmpeg
    echo Please install FFmpeg from https://ffmpeg.org
    pause
)

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -e .
)

REM Start the Flask application
echo.
echo Starting Flask application...
echo.
echo ========================================
echo Server is running at: http://localhost:5000
echo Press Ctrl+C to stop
echo ========================================
echo.

python app.py

pause
