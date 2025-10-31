@echo off
REM Start DevMindAPI FastAPI Service
echo Starting DevMindAPI...
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the API
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python main.py

pause
