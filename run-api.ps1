# Run FastAPI Server

Write-Host "🚀 Starting FastAPI Server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "  - http://localhost:8000" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
