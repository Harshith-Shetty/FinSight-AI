# Test Backend API Connection

Write-Host "Testing FinSight AI Backend..." -ForegroundColor Cyan

# Test 1: Check if backend is running
Write-Host "`n1. Checking if backend is running on port 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | findstr ":8000.*LISTENING"
if ($port8000) {
    Write-Host "✓ Backend is running on port 8000" -ForegroundColor Green
} else {
    Write-Host "✗ Backend is NOT running on port 8000" -ForegroundColor Red
    exit 1
}

# Test 2: Test root endpoint
Write-Host "`n2. Testing root endpoint (/)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -Method GET -UseBasicParsing
    Write-Host "✓ Root endpoint accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Root endpoint failed: $_" -ForegroundColor Red
}

# Test 3: Test docs endpoint
Write-Host "`n3. Testing docs endpoint (/docs)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -Method GET -UseBasicParsing
    Write-Host "✓ Docs endpoint accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Docs endpoint failed: $_" -ForegroundColor Red
}

# Test 4: Test CORS with OPTIONS request
Write-Host "`n4. Testing CORS preflight (OPTIONS)..." -ForegroundColor Yellow
try {
    $headers = @{
        "Origin" = "http://localhost:3000"
        "Access-Control-Request-Method" = "POST"
        "Access-Control-Request-Headers" = "content-type,authorization"
    }
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/chats" -Method OPTIONS -Headers $headers -UseBasicParsing
    Write-Host "✓ CORS preflight successful (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "  CORS Headers:" -ForegroundColor Gray
    $response.Headers.GetEnumerator() | Where-Object { $_.Key -like "*Access-Control*" } | ForEach-Object {
        Write-Host "    $($_.Key): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ CORS preflight failed: $_" -ForegroundColor Red
}

Write-Host "`n" -NoNewline
Write-Host "Testing complete!" -ForegroundColor Cyan
