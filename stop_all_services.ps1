# DevMind System - Stop All Services Script
# Date: October 31, 2025
# Version: 1.0.0

Write-Host "======================================"
Write-Host "  DevMind System Shutdown"
Write-Host "======================================"
Write-Host ""

# Function to stop processes by port
function Stop-ProcessByPort {
    param([int]$Port, [string]$ServiceName)
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        
        if ($connection) {
            $processId = $connection.OwningProcess
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            
            if ($process) {
                Write-Host "🛑 Stopping $ServiceName (PID: $processId, Port: $Port)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Write-Host "✅ $ServiceName stopped" -ForegroundColor Green
            }
        } else {
            Write-Host "ℹ️  $ServiceName not running (Port: $Port)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠️  Could not stop $ServiceName : $_" -ForegroundColor Yellow
    }
}

# Stop all services
Write-Host "Stopping all DevMind services..." -ForegroundColor Cyan
Write-Host ""

Stop-ProcessByPort -Port 3000 -ServiceName "React Dashboard"
Stop-ProcessByPort -Port 8001 -ServiceName "Backend API"
Stop-ProcessByPort -Port 5002 -ServiceName "Monitoring Service"
Stop-ProcessByPort -Port 8765 -ServiceName "VS Code Extension WebSocket"

# Also stop any node/python processes related to DevMind
Write-Host ""
Write-Host "Cleaning up any remaining DevMind processes..." -ForegroundColor Cyan

Get-Process | Where-Object {
    $_.ProcessName -in @('node', 'python', 'pythonw') -and
    $_.MainWindowTitle -like "*DevMind*"
} | ForEach-Object {
    Write-Host "🛑 Stopping process: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Yellow
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "======================================"
Write-Host "  All Services Stopped!"
Write-Host "======================================"
Write-Host ""
Write-Host "✅ DevMind system shutdown complete" -ForegroundColor Green
Write-Host ""
