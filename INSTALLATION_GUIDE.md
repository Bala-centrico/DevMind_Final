# DevMind System - Installation Guide
# Date: October 31, 2025

## 🎯 Complete Installation Steps

### Prerequisites Check

Before starting, ensure you have:

- [ ] **Node.js** v14+ installed
- [ ] **Python 3.13** installed
- [ ] **VS Code** with GitHub Copilot extension
- [ ] **PowerShell** (Windows)
- [ ] **Git** (optional, for version control)

---

## Step 1: Install Node.js Dependencies

### Dashboard

```powershell
cd C:\CentricoINshared\DevMind_Final\Dashboard
npm install

# If you encounter errors, try:
npm install --legacy-peer-deps
```

**Expected packages:**
- react@17.0.2
- react-dom@17.0.2
- typescript@4.4.4
- @types/react
- @types/react-dom

### VS Code Extension

```powershell
cd C:\CentricoINshared\DevMind_Final\Extension
npm install

# Expected packages:
# - ws (WebSocket library)
# - @types/vscode
# - typescript
```

---

## Step 2: Install Python Dependencies

### Backend

```powershell
cd C:\CentricoINshared\DevMind_Final\Backend
pip install fastapi uvicorn websockets python-dotenv

# Or use requirements.txt if available:
pip install -r requirements.txt
```

### Services

```powershell
cd C:\CentricoINshared\DevMind_Final\Services
pip install fastapi uvicorn websockets python-dotenv jira mcp

# Verify installation:
python -c "import fastapi, uvicorn, websockets, jira; print('✅ All packages installed')"
```

---

## Step 3: Database Setup

### Initialize Database

```powershell
cd C:\CentricoINshared\DevMind_Final\Services

# Run initialization script
python init_mcp_dashboard_db.py
```

This will create `C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db` with tables:
- `jira_dashboard`
- `jira_prompts`
- `jira_tmp_prompts`
- `jira_kb`
- `svn_path_mappings`

### Verify Database

```powershell
# Check if database was created
Test-Path "C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db"

# Should output: True
```

---

## Step 4: Configure Jira Credentials

### Create Credentials Directory

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.devmind" -Force
```

### Create Credentials File

Create file: `C:\Users\YourUsername\.devmind\credentials.ini`

```ini
[jira]
url = https://your-company.atlassian.net
username = your.email@company.com
api_token = your_jira_api_token_here
```

**To get Jira API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and paste it in credentials.ini

---

## Step 5: Configure MCP Server

### Update VS Code Settings

Create or edit: `%APPDATA%\Code\User\mcp.json`

```json
{
  "servers": {
    "DevMind_MCP": {
      "command": "C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["DevMind_MCP.py"],
      "cwd": "C:\\CentricoINshared\\DevMind_Final\\Services",
      "env": {
        "JIRA_CREDENTIALS_PATH": "C:\\Users\\YourUsername\\.devmind\\credentials.ini"
      }
    }
  }
}
```

**⚠️ Important:** Update paths with your actual username and Python path.

---

## Step 6: Update Configuration Files

### Backend Configuration

Edit `C:\CentricoINshared\DevMind_Final\Backend\main.py`:

Find these lines and update paths:

```python
# Line ~20-30
DB_PATH = r"C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db"
WS_HOST = "127.0.0.1"
WS_PORT = 8765
```

### MCP Server Configuration

Edit `C:\CentricoINshared\DevMind_Final\Services\DevMind_MCP.py`:

Update database path:

```python
# Line ~50-60
DB_PATH = r"C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db"
```

---

## Step 7: Install VS Code Extension

### Method 1: From Source (Recommended)

```powershell
cd C:\CentricoINshared\DevMind_Final\Extension

# Compile TypeScript
npm run compile

# Package extension
npm install -g vsce
vsce package

# Install the generated .vsix file
code --install-extension vscode-copilot-bridge-1.0.0.vsix
```

### Method 2: Development Mode

```powershell
cd C:\CentricoINshared\DevMind_Final\Extension

# Open in VS Code
code .

# Press F5 to launch Extension Development Host
```

---

## Step 8: Verify Installation

### Check All Dependencies

```powershell
# Run verification script
cd C:\CentricoINshared\DevMind_Final

# Check Node packages
cd Dashboard; npm list --depth=0
cd ..\Extension; npm list --depth=0

# Check Python packages
cd ..\Backend; pip list | Select-String "fastapi|uvicorn|websockets"
cd ..\Services; pip list | Select-String "fastapi|uvicorn|jira"
```

### Test Database Connection

```powershell
cd C:\CentricoINshared\DevMind_Final\Services
python check_tables.py
```

Should output:
```
✅ Database connection successful
✅ Table: jira_dashboard (X rows)
✅ Table: jira_prompts (X rows)
...
```

---

## Step 9: First Launch

### Start Services in Order

**Terminal 1 - Monitoring Service:**
```powershell
cd C:\CentricoINshared\DevMind_Final\Services
python monitoring_service.py
```
Wait for: `✅ Monitoring Service started on port 5002`

**Terminal 2 - Backend:**
```powershell
cd C:\CentricoINshared\DevMind_Final\Backend
python main.py
```
Wait for: `✅ FastAPI backend started on port 8001`

**Terminal 3 - Dashboard:**
```powershell
cd C:\CentricoINshared\DevMind_Final\Dashboard
npm start
```
Wait for: Browser opens to http://localhost:3000

**Terminal 4 - VS Code Extension:**
1. Open VS Code
2. Check Output panel → "Copilot Bridge"
3. Should see: `✅ WebSocket server started on ws://127.0.0.1:8765`

### Verify All Services

```powershell
Get-NetTCPConnection -LocalPort 5002,8001,3000,8765 -State Listen | Format-Table -AutoSize
```

Should show 4 listening ports.

---

## Step 10: Test the System

### 1. Access Dashboard

Open browser: http://localhost:3000

You should see:
- Task list (may be empty initially)
- "Add New Task" button
- Statistics cards

### 2. Test Backend API

```powershell
# Test REST API
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/jiraCards" -Method Get

# Should return JSON array of tasks
```

### 3. Test Extension Connection

In VS Code:
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Copilot Bridge: Start"
3. Check Output panel for connection messages

### 4. Test End-to-End Flow

1. In Dashboard, click "Analyze" on any task
2. Progress monitor should open
3. Watch progress updates (10% → 25% → 40% → ... → 100%)
4. Code should be generated and saved

---

## 🎉 Installation Complete!

You now have a fully functional DevMind system.

### Next Steps

1. **Load Knowledge Base:** Run `Load_knowledge.py` to populate the KB
2. **Add Tasks:** Use dashboard to add Jira tasks
3. **Configure SVN:** Update SVN path mappings if needed
4. **Customize:** Adjust settings in configuration files

---

## 🆘 Troubleshooting

### npm install fails

```powershell
# Clear npm cache
npm cache clean --force

# Try with legacy peer deps
npm install --legacy-peer-deps
```

### Python packages fail to install

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install packages one by one
pip install fastapi
pip install uvicorn
pip install websockets
```

### Extension not starting

1. Check VS Code version (must be 1.85.0+)
2. Verify GitHub Copilot is installed and active
3. Check extension host logs: Help → Toggle Developer Tools

### Database errors

```powershell
# Recreate database
cd C:\CentricoINshared\DevMind_Final\Services
Remove-Item ..\Database\mcp_dashboard.db -Force
python init_mcp_dashboard_db.py
```

### Port conflicts

If ports are already in use:
- Dashboard: Change in `package.json` → `"start": "set PORT=3001 && react-scripts start"`
- Backend: Update `main.py` → `uvicorn.run(app, host="0.0.0.0", port=8002)`
- Monitoring: Update `monitoring_service.py` → `PORT = 5003`
- Extension: Update `package.json` → `"copilotBridge.port": 8766`

---

## 📚 Additional Resources

- `README.md` - System overview and usage guide
- `SYSTEM_ARCHITECTURE.md` - Detailed architecture documentation
- `start_all_services.ps1` - Automated startup script
- `stop_all_services.ps1` - Shutdown script

---

**Installation Guide Version:** 1.0.0  
**Last Updated:** October 31, 2025
