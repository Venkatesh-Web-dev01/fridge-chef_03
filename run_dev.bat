@echo off
echo ========================================================
echo Starting FridgeChef AI (FastAPI Backend + Vite Frontend)
echo ========================================================

start cmd /k "python -m uvicorn backend.main:app --reload --port 8000"
start cmd /k "cd frontend && npm run dev"

echo Backend running on http://127.0.0.1:8000
echo Frontend running on http://localhost:5173
pause
