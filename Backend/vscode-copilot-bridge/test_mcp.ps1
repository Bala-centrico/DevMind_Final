# Test MCP Integration with VS Code Copilot Bridge

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing MCP Integration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if extension is compiled
Write-Host "1. Checking extension compilation..." -ForegroundColor Yellow
if (Test-Path "out\extension.js") {
    Write-Host "   OK Extension compiled" -ForegroundColor Green
} else {
    Write-Host "   ERROR Extension not compiled. Run: npm run compile" -ForegroundColor Red
    exit 1
}

# Step 2: Check MCP configuration
Write-Host ""
Write-Host "2. Checking MCP configuration..." -ForegroundColor Yellow
if (Test-Path ".vscode\mcp.json") {
    Write-Host "   OK MCP config found" -ForegroundColor Green
    $mcpConfig = Get-Content ".vscode\mcp.json" | ConvertFrom-Json
    Write-Host "   Servers configured:" -ForegroundColor Cyan
    foreach ($server in $mcpConfig.servers.PSObject.Properties) {
        Write-Host "     - $($server.Name)" -ForegroundColor White
    }
} else {
    Write-Host "   WARNING No MCP config found (.vscode\mcp.json)" -ForegroundColor Yellow
    Write-Host "   MCP integration will not work without configuration" -ForegroundColor Yellow
}

# Step 3: Check weather MCP server
Write-Host ""
Write-Host "3. Checking weather MCP server..." -ForegroundColor Yellow
$weatherPath = "C:\Thiru\MCP_Workplace\weather.py"
if (Test-Path $weatherPath) {
    Write-Host "   OK Weather server found at: $weatherPath" -ForegroundColor Green
} else {
    Write-Host "   ERROR Weather server not found at: $weatherPath" -ForegroundColor Red
}

# Step 4: List modified files
Write-Host ""
Write-Host "4. Modified/Created files:" -ForegroundColor Yellow
$files = @(
    "src\extension.ts",
    "package.json",
    "README.md",
    "MCP_INTEGRATION.md",
    "CHANGES.md",
    ".vscode\mcp.json"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   OK $file" -ForegroundColor Green
    } else {
        Write-Host "   ERROR $file" -ForegroundColor Red
    }
}

# Step 5: Instructions
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To test the MCP integration:" -ForegroundColor Yellow
Write-Host "1. Press F5 in VS Code to start Extension Development Host" -ForegroundColor White
Write-Host "2. Open Output panel: View -> Output -> Select 'Copilot Bridge'" -ForegroundColor White
Write-Host "3. Run command: Ctrl+Shift+P -> 'Copilot Bridge - MCP Server Status'" -ForegroundColor White
Write-Host ""

Write-Host "Expected log output:" -ForegroundColor Yellow
Write-Host "  OK Initialized 1 MCP server(s)" -ForegroundColor Green
Write-Host "  OK MCP server 'weather' started successfully" -ForegroundColor Green
Write-Host "  Querying MCP servers for context..." -ForegroundColor White
Write-Host "  [weather] Response: The weather is hot and dry" -ForegroundColor White
Write-Host "  OK Enhanced prompt with MCP context" -ForegroundColor Green
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - README.md - Updated with MCP features" -ForegroundColor White
Write-Host "  - MCP_INTEGRATION.md - Comprehensive MCP guide" -ForegroundColor White
Write-Host "  - CHANGES.md - Summary of all changes" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

