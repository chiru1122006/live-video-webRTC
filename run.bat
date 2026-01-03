@echo off
echo ============================================
echo WebRTC Video Streaming Server
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo Starting server on http://localhost:5000
echo Open this URL in multiple browser tabs to test
echo Press Ctrl+C to stop the server
echo ============================================
echo.

REM Run the server
python app.py
