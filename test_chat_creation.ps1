# Test Chat Creation Endpoint
# First login, then create a chat

$API_URL = "http://localhost:8000"

Write-Host "Testing Chat Creation Flow..." -ForegroundColor Cyan

# Step 1: Login
Write-Host "`n1. Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        email = "test@example.com"
        password = "password123"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$API_URL/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody

    $token = $loginResponse.access_token
    Write-Host "✓ Login successful! Token: $($token.Substring(0,20))..." -ForegroundColor Green
} catch {
    Write-Host "✗ Login failed: $_" -ForegroundColor Red
    Write-Host "Please register first or check credentials" -ForegroundColor Yellow
    exit 1
}

# Step 2: Create Chat
Write-Host "`n2. Creating hybrid chat..." -ForegroundColor Yellow
try {
    $chatBody = @{
        mode = "HYBRID"
    } | ConvertTo-Json

    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }

    $chatResponse = Invoke-RestMethod -Uri "$API_URL/api/v1/chats" `
        -Method POST `
        -Headers $headers `
        -Body $chatBody

    Write-Host "✓ Chat created successfully!" -ForegroundColor Green
    Write-Host "  Chat ID: $($chatResponse.id)" -ForegroundColor Gray
    Write-Host "  Title: $($chatResponse.title)" -ForegroundColor Gray
    Write-Host "  Mode: $($chatResponse.mode)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Chat creation failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nResponse:" -ForegroundColor Yellow
    Write-Host $_.ErrorDetails.Message -ForegroundColor Red
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
