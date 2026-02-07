# FinSight AI - Run Scripts

Write-Host "🚀 Starting FinSight AI Infrastructure..." -ForegroundColor Cyan
Write-Host ""

# Start Docker services
Write-Host "📦 Starting Docker Compose..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "✅ Infrastructure ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "  - Redis: localhost:6379" -ForegroundColor White
Write-Host "  - Qdrant: localhost:6333" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: python -m uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  2. Run: celery -A app.worker.celery_app worker --loglevel=info" -ForegroundColor White
Write-Host ""
