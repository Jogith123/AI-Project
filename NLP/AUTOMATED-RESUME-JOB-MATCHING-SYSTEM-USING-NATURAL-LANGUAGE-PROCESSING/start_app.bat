@echo off
echo Starting Resume-Job Matching System...

echo.
echo [1/2] Starting Python FastAPI Backend (Port 8000)...
start "Backend API" cmd /k "cd /d e:\NLP-Project\backend && .\venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo.
echo [2/2] Starting React Frontend (Port 5173)...
start "Frontend Web App" cmd /k "cd /d e:\NLP-Project\frontend && npm run dev"

echo.
echo Both servers are starting in separate windows.
echo - Backend API will be available at: http://localhost:8000
echo - Frontend Web App will be available at: http://localhost:5173
echo.
echo Please wait a moment for the React development server to initialize.
pause
