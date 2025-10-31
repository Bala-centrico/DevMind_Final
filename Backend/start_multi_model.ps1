# Start DevMindAPI Multi-Model Server

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Starting DevMindAPI Multi-Model Server" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "Please edit .env with your API keys and restart`n" -ForegroundColor Yellow
        exit 0
    }
}

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
}

# Check if main_multi_model.py exists
if (-not (Test-Path "main_multi_model.py")) {
    Write-Host "ERROR: main_multi_model.py not found!" -ForegroundColor Red
    Write-Host "Falling back to main.py..." -ForegroundColor Yellow
    
    if (Test-Path "main.py") {
        python main.py
    } else {
        Write-Host "ERROR: No main file found!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Starting server..." -ForegroundColor Green
    Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "Health Check: http://localhost:8000/health`n" -ForegroundColor Cyan
    
    python main_multi_model.py
}
