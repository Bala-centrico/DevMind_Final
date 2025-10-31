# DevMind System - Automated Startup Script
# Date: October 31, 2025
# Version: 1.0.0

Write-Host "======================================"
Write-Host "  DevMind System Startup"
Write-Host "======================================"
Write-Host ""

# Set base path
$BasePath = "C:\CentricoINshared\DevMind_Final"

# Check if base directory exists
if (-not (Test-Path $BasePath)) {
    Write-Host "❌ ERROR: DevMind_Final directory not found at $BasePath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Base directory found: $BasePath" -ForegroundColor Green
Write-Host ""

# Function to start a process in a new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )
    
    Write-Host "🚀 Starting $Title..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$WorkingDirectory'; Write-Host '=== $Title ===' -ForegroundColor Yellow; $Command"
    )
    
    Start-Sleep -Seconds 2
}

# 1. Start Monitoring Service (Port 5002)
Write-Host ""
Write-Host "Step 1: Starting Monitoring Service..." -ForegroundColor Yellow
Start-ServiceWindow -Title "Monitoring Service (Port 5002)" `
                     -Command "python monitoring_service.py" `
                     -WorkingDirectory "$BasePath\Services"

# 2. Start Backend API (Port 8001)
Write-Host "Step 2: Starting Backend API..." -ForegroundColor Yellow
Start-ServiceWindow -Title "Backend API (Port 8001)" `
                     -Command "python main.py" `
                     -WorkingDirectory "$BasePath\Backend"

# 3. Start Dashboard (Port 3000)
Write-Host "Step 3: Starting React Dashboard..." -ForegroundColor Yellow
Start-ServiceWindow -Title "React Dashboard (Port 3000)" `
                     -Command "npm start" `
                     -WorkingDirectory "$BasePath\Dashboard"

Write-Host ""
Write-Host "======================================"
Write-Host "  All Services Started!"
Write-Host "======================================"
Write-Host ""
Write-Host "📋 Service Status:" -ForegroundColor Green
Write-Host "  • Monitoring Service: http://localhost:5002" -ForegroundColor White
Write-Host "  • Backend API:        http://localhost:8001" -ForegroundColor White
Write-Host "  • Dashboard:          http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  NOTE: VS Code Extension must be started manually:" -ForegroundColor Yellow
Write-Host "    1. Open VS Code" -ForegroundColor White
Write-Host "    2. The extension should auto-start (port 8765)" -ForegroundColor White
Write-Host "    3. Check Output panel → 'Copilot Bridge'" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Verification Commands:" -ForegroundColor Cyan
Write-Host '  Get-NetTCPConnection -LocalPort 5002,8001,3000,8765 -State Listen' -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to open Dashboard in browser..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open Dashboard in default browser
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "✅ DevMind System is now running!" -ForegroundColor Green
Write-Host "   Close this window to keep services running." -ForegroundColor Gray
Write-Host ""
