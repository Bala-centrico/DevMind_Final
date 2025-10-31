# Test script for DevMindAPI
Write-Host "Testing DevMindAPI..." -ForegroundColor Cyan

$apiUrl = "http://localhost:8000"

# Test 1: Health Check
Write-Host "`n1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$apiUrl/health" -Method Get
    Write-Host "✓ Health Check: " -NoNewline -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json)
} catch {
    Write-Host "✗ Health Check Failed: $_" -ForegroundColor Red
}

# Test 2: Empty Prompt (Should Fail)
Write-Host "`n2. Testing Empty Prompt Validation..." -ForegroundColor Yellow
try {
    $body = @{
        prompt = ""
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$apiUrl/api/v1/copilot/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✗ Should have failed validation" -ForegroundColor Red
} catch {
    Write-Host "✓ Correctly rejected empty prompt" -ForegroundColor Green
}

# Test 3: Valid Copilot Request
Write-Host "`n3. Testing Valid Copilot Request..." -ForegroundColor Yellow
try {
    $body = @{
        prompt = "Explain what is FastAPI in one sentence"
        timeout = 30
    } | ConvertTo-Json
    
    Write-Host "Sending prompt to Copilot..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "$apiUrl/api/v1/copilot/chat" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "✓ Copilot Response Received:" -ForegroundColor Green
    Write-Host "  Prompt: $($response.prompt)" -ForegroundColor Gray
    Write-Host "  Response: $($response.response)" -ForegroundColor Gray
    Write-Host "  Success: $($response.success)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Request Failed: $_" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode -ForegroundColor Red
}

Write-Host "`nTests Complete!" -ForegroundColor Cyan
