# Run Celery Worker

Write-Host "⚙️ Starting Celery Worker..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Worker will process tasks from Redis queue" -ForegroundColor Yellow
Write-Host "Using LLM Provider: $env:LLM_PROVIDER" -ForegroundColor White
Write-Host ""

celery -A app.worker.celery_app worker --loglevel=info --pool=solo
