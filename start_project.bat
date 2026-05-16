@echo off
echo =========================================
echo    Starting Network Analyzer Services
echo =========================================
echo.

:: Start Backend
echo Starting Backend...
start cmd /k "title Backend Server && cd backend && call venv\Scripts\activate && pip install -r requirements.txt && uvicorn main:app --reload --port 8888"

:: Start Capture Engine
echo Starting Capture Engine...
start cmd /k "title Capture Engine && cd capture && call ..\backend\venv\Scripts\activate && pip install -r requirements.txt && python main.py"

:: Start Frontend
echo Starting Frontend...
start cmd /k "title Frontend React && cd frontend && call npm install && call npm run dev"

echo.
echo All services have been launched in separate windows!
echo Please wait a few seconds for them to load.
echo The dashboard will be available at: http://localhost:3000
echo.
pause
