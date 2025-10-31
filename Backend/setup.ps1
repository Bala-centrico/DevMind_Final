# DevMindAPI Setup Script
# Automated setup for FastAPI and VS Code Extension

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   DevMindAPI Setup Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "C:\Users\GBS09281\Hackathon\DevMindAPI"
$extensionPath = "$projectRoot\vscode-copilot-bridge"

# Step 1: Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Check Node.js
Write-Host "[2/5] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Found: Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found! Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

# Step 3: Install Python dependencies
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $projectRoot
try {
    pip install -r requirements.txt | Out-Null
    Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to install Python dependencies" -ForegroundColor Red
    Write-Host "  Try manually: pip install -r requirements.txt" -ForegroundColor Yellow
}

# Step 4: Install Node.js dependencies
Write-Host "[4/5] Installing Node.js dependencies..." -ForegroundColor Yellow
Set-Location $extensionPath
try {
    npm install 2>&1 | Out-Null
    Write-Host "  ✓ Node.js dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to install Node.js dependencies" -ForegroundColor Red
    Write-Host "  Try manually: cd vscode-copilot-bridge && npm install" -ForegroundColor Yellow
}

# Step 5: Compile extension
Write-Host "[5/5] Compiling VS Code extension..." -ForegroundColor Yellow
try {
    npm run compile 2>&1 | Out-Null
    Write-Host "  ✓ Extension compiled successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to compile extension" -ForegroundColor Red
    Write-Host "  Try manually: npm run compile" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start VS Code Insiders and open the extension folder:" -ForegroundColor White
Write-Host "   code-insiders $extensionPath" -ForegroundColor Gray
Write-Host ""
Write-Host "2. In VS Code, press F5 to run the extension" -ForegroundColor White
Write-Host ""
Write-Host "3. In a new terminal, start the FastAPI service:" -ForegroundColor White
Write-Host "   cd $projectRoot" -ForegroundColor Gray
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test the API:" -ForegroundColor White
Write-Host "   .\test_api.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - Quick Start: QUICKSTART.md" -ForegroundColor Gray
Write-Host "  - Architecture: ARCHITECTURE.md" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/docs (after starting API)" -ForegroundColor Gray
Write-Host ""

Set-Location $projectRoot
