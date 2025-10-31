# DevMindAPI Multi-Model Setup Script
# Run this script to set up the multi-model environment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DevMindAPI Multi-Model Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements_multi_model.txt") {
    pip install -r requirements_multi_model.txt
} elseif (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    pip install openai anthropic aiohttp
} else {
    Write-Host "WARNING: No requirements file found" -ForegroundColor Yellow
    pip install fastapi uvicorn websockets openai anthropic aiohttp python-dotenv
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "`nCreating .env file from example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file - Please edit it with your API keys" -ForegroundColor Green
    } else {
        Write-Host "WARNING: .env.example not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n.env file already exists" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys" -ForegroundColor White
Write-Host "2. Run: python main_multi_model.py" -ForegroundColor White
Write-Host "3. Or use: .\start_multi_model.ps1`n" -ForegroundColor White

Write-Host "To test the API:" -ForegroundColor Yellow
Write-Host "python test_multi_model.py --quick`n" -ForegroundColor White

Write-Host "Available API Keys to configure:" -ForegroundColor Yellow
Write-Host "- OPENAI_API_KEY: https://platform.openai.com/api-keys" -ForegroundColor White
Write-Host "- ANTHROPIC_API_KEY: https://console.anthropic.com/" -ForegroundColor White
Write-Host "- GOOGLE_API_KEY: https://makersuite.google.com/app/apikey`n" -ForegroundColor White
