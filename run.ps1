# AI-Powered Personalized Learning Platform - Application Startup Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AI-Powered Personalized Learning Platform" -ForegroundColor White
Write-Host "  Starting FastAPI backend & serving interactive React UI..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Set environment
$env:PYTHONPATH = "backend"

# Start uvicorn server
Write-Host "`n[1/2] Launching server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
