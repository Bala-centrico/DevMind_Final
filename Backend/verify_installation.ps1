# Installation Verification Script
# Checks if DevMindAPI is properly set up

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DevMindAPI Installation Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "C:\Users\GBS09281\Hackathon\DevMindAPI"
$extensionPath = "$projectRoot\vscode-copilot-bridge"
$allChecks = @()

# Helper function
function Test-Check {
    param($name, $condition, $successMsg, $failMsg)
    Write-Host "Checking: $name..." -NoNewline
    if ($condition) {
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "  → $successMsg" -ForegroundColor Gray
        return $true
    } else {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "  → $failMsg" -ForegroundColor Yellow
        return $false
    }
}

# Check 1: Python Installation
$pythonCheck = $false
try {
    $pythonVersion = python --version 2>&1
    $pythonCheck = Test-Check "Python Installation" $true "Found: $pythonVersion" ""
} catch {
    $pythonCheck = Test-Check "Python Installation" $false "" "Python not found. Install Python 3.8+"
}
$allChecks += $pythonCheck

# Check 2: Node.js Installation
$nodeCheck = $false
try {
    $nodeVersion = node --version 2>&1
    $nodeCheck = Test-Check "Node.js Installation" $true "Found: Node.js $nodeVersion" ""
} catch {
    $nodeCheck = Test-Check "Node.js Installation" $false "" "Node.js not found. Install Node.js 16+"
}
$allChecks += $nodeCheck

# Check 3: Project Files
$mainExists = Test-Path "$projectRoot\main.py"
$mainCheck = Test-Check "Main API File" $mainExists "main.py exists" "main.py not found"
$allChecks += $mainCheck

# Check 4: Requirements File
$reqExists = Test-Path "$projectRoot\requirements.txt"
$reqCheck = Test-Check "Requirements File" $reqExists "requirements.txt exists" "requirements.txt not found"
$allChecks += $reqCheck

# Check 5: Extension Files
$extExists = Test-Path "$extensionPath\src\extension.ts"
$extCheck = Test-Check "Extension Source" $extExists "extension.ts exists" "extension.ts not found"
$allChecks += $extCheck

# Check 6: Extension Package.json
$pkgExists = Test-Path "$extensionPath\package.json"
$pkgCheck = Test-Check "Extension Manifest" $pkgExists "package.json exists" "package.json not found"
$allChecks += $pkgCheck

# Check 7: Python Dependencies
$pipCheck = $false
try {
    Set-Location $projectRoot
    $installed = pip list 2>&1 | Select-String "fastapi"
    $pipCheck = Test-Check "Python Dependencies" ($null -ne $installed) "FastAPI is installed" "Run: pip install -r requirements.txt"
} catch {
    $pipCheck = Test-Check "Python Dependencies" $false "" "Could not verify Python packages"
}
$allChecks += $pipCheck

# Check 8: Node Modules
$nmExists = Test-Path "$extensionPath\node_modules"
$nmCheck = Test-Check "Node.js Dependencies" $nmExists "node_modules exists" "Run: cd vscode-copilot-bridge && npm install"
$allChecks += $nmCheck

# Check 9: Compiled Extension
$outExists = Test-Path "$extensionPath\out\extension.js"
$outCheck = Test-Check "Compiled Extension" $outExists "extension.js compiled" "Run: cd vscode-copilot-bridge && npm run compile"
$allChecks += $outCheck

# Check 10: Documentation Files
$docsExist = (Test-Path "$projectRoot\README.md") -and (Test-Path "$projectRoot\QUICKSTART.md")
$docsCheck = Test-Check "Documentation" $docsExist "Documentation files present" "Documentation missing"
$allChecks += $docsCheck

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passed = ($allChecks | Where-Object { $_ -eq $true }).Count
$total = $allChecks.Count
$percentage = [math]::Round(($passed / $total) * 100)

Write-Host "Passed: $passed / $total ($percentage%)" -ForegroundColor $(if ($percentage -eq 100) { "Green" } else { "Yellow" })
Write-Host ""

if ($percentage -eq 100) {
    Write-Host "✓ All checks passed! Installation is complete." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Start VS Code Insiders: code-insiders $extensionPath" -ForegroundColor White
    Write-Host "2. Press F5 to run the extension" -ForegroundColor White
    Write-Host "3. Start the API: python main.py" -ForegroundColor White
    Write-Host "4. Test: .\test_api.ps1" -ForegroundColor White
} else {
    Write-Host "⚠ Some checks failed. Please fix the issues above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick Fix:" -ForegroundColor Cyan
    Write-Host "Run the setup script: .\setup.ps1" -ForegroundColor White
}

Write-Host ""
Set-Location $projectRoot
