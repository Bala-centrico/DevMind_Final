# DevMind System - Quick Reference Guide

## 🚀 Quick Start Commands

### Start All Services
```powershell
cd C:\CentricoINshared\DevMind_Final
.\start_all_services.ps1
```

### Stop All Services
```powershell
cd C:\CentricoINshared\DevMind_Final
.\stop_all_services.ps1
```

---

## 📍 Service URLs

| Service | URL | Status Check |
|---------|-----|--------------|
| Dashboard | http://localhost:3000 | Open in browser |
| Backend API | http://localhost:8001/docs | Swagger UI |
| Monitoring | http://localhost:5002 | WebSocket only |
| Extension | ws://127.0.0.1:8765 | Check VS Code Output |

---

## 🔧 Common Commands

### Check Running Services
```powershell
Get-NetTCPConnection -LocalPort 3000,8001,5002,8765 -State Listen
```

### View Logs
```powershell
# Backend logs
cd C:\CentricoINshared\DevMind_Final\Backend
Get-Content -Path backend.log -Tail 50 -Wait

# Monitoring logs
cd C:\CentricoINshared\DevMind_Final\Services
Get-Content -Path monitoring.log -Tail 50 -Wait

# Extension logs
# VS Code: View → Output → Select "Copilot Bridge"
```

### Restart Individual Service

**Dashboard:**
```powershell
# Stop
Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
# Start
cd C:\CentricoINshared\DevMind_Final\Dashboard; npm start
```

**Backend:**
```powershell
# Stop
Get-NetTCPConnection -LocalPort 8001 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
# Start
cd C:\CentricoINshared\DevMind_Final\Backend; python main.py
```

**Monitoring:**
```powershell
# Stop
Get-NetTCPConnection -LocalPort 5002 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
# Start
cd C:\CentricoINshared\DevMind_Final\Services; python monitoring_service.py
```

**Extension:**
```
1. Restart VS Code
2. Extension auto-starts
```

---

## 🗄️ Database Operations

### View Database Content
```powershell
cd C:\CentricoINshared\DevMind_Final\Database

# Using SQLite CLI
sqlite3 mcp_dashboard.db "SELECT * FROM jira_dashboard;"

# Or using Python
python -c "import sqlite3; conn = sqlite3.connect('mcp_dashboard.db'); print(conn.execute('SELECT COUNT(*) FROM jira_dashboard').fetchone())"
```

### Backup Database
```powershell
cd C:\CentricoINshared\DevMind_Final\Database
Copy-Item mcp_dashboard.db "mcp_dashboard_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### Reset Database
```powershell
cd C:\CentricoINshared\DevMind_Final\Services
python init_mcp_dashboard_db.py
```

---

## 🧪 Testing Commands

### Test Backend API
```powershell
# Get all tasks
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/jiraCards"

# Test analyze endpoint
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/analyze" -Method POST -ContentType "application/json" -Body '{"jira_id":"GDPR-58"}'
```

### Test Monitoring Service
```powershell
# Send progress update
Invoke-RestMethod -Uri "http://localhost:5002/api/progress" -Method POST -ContentType "application/json" -Body '{"jiraNumber":"TEST-1","stage":"fetching_jira","status":"in-progress","message":"Test","progress":25,"timestamp":"2025-10-31T10:00:00Z"}'
```

### Test WebSocket Connection
```powershell
# Install wscat if not available
npm install -g wscat

# Connect to extension
wscat -c ws://127.0.0.1:8765

# Connect to monitoring
wscat -c ws://localhost:5002/ws/monitor/GDPR-58
```

---

## 🐛 Troubleshooting Quick Fixes

### "Port already in use"
```powershell
# Find process using port
Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess

# Kill process
Stop-Process -Id <PID> -Force
```

### "Cannot connect to backend"
```powershell
# Check if backend is running
Get-NetTCPConnection -LocalPort 8001 -State Listen

# Check backend logs
cd C:\CentricoINshared\DevMind_Final\Backend
Get-Content -Path backend.log -Tail 20
```

### "Extension not responding"
```
1. Open VS Code Command Palette (Ctrl+Shift+P)
2. Type: "Developer: Reload Window"
3. Check Output panel → "Copilot Bridge"
```

### "Database locked"
```powershell
# Close all connections
cd C:\CentricoINshared\DevMind_Final\Services
python -c "import sqlite3; conn = sqlite3.connect('../Database/mcp_dashboard.db'); conn.close()"

# Or restart all services
```

### "npm start fails"
```powershell
# Clear cache and reinstall
cd C:\CentricoINshared\DevMind_Final\Dashboard
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm cache clean --force
npm install
npm start
```

---

## 📂 Important File Locations

### Configuration Files
```
Backend Config:       Backend/main.py
Monitoring Config:    Services/monitoring_service.py
Dashboard Config:     Dashboard/package.json
Extension Config:     Extension/package.json
MCP Config:           %APPDATA%\Code\User\mcp.json
Jira Credentials:     %USERPROFILE%\.devmind\credentials.ini
```

### Log Files
```
Backend:              Backend/backend.log
Monitoring:           Services/monitoring.log
Extension:            VS Code Output → "Copilot Bridge"
Dashboard:            Browser Console (F12)
```

### Database Files
```
Main DB:              Database/mcp_dashboard.db
Oracle Standards:     Z:\oracle_standards.db (optional)
```

---

## 🔑 Key Keyboard Shortcuts

### VS Code
- `Ctrl+Shift+P` - Command Palette
- `Ctrl+Shift+I` - Copilot Chat
- `Ctrl+`` - Toggle Terminal
- `F5` - Run extension in debug mode

### Dashboard (Browser)
- `F12` - Developer Tools
- `Ctrl+Shift+R` - Hard Refresh
- `F5` - Refresh page

---

## 📊 System Status Check Script

```powershell
# Save as: check_system_status.ps1
Write-Host "DevMind System Status Check" -ForegroundColor Cyan
Write-Host "======================================"

$ports = @{
    3000 = "Dashboard"
    8001 = "Backend API"
    5002 = "Monitoring"
    8765 = "Extension"
}

foreach ($port in $ports.Keys) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "✅ $($ports[$port]) (Port $port)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($ports[$port]) (Port $port) - NOT RUNNING" -ForegroundColor Red
    }
}

Write-Host "======================================"
```

---

## 🆘 Emergency Commands

### Kill All DevMind Processes
```powershell
Get-Process | Where-Object { $_.Path -like "*DevMind_Final*" } | Stop-Process -Force
```

### Full System Reset
```powershell
# 1. Stop all services
.\stop_all_services.ps1

# 2. Clear logs
Remove-Item Backend/*.log -Force -ErrorAction SilentlyContinue
Remove-Item Services/*.log -Force -ErrorAction SilentlyContinue

# 3. Reset database
cd Services
python init_mcp_dashboard_db.py

# 4. Restart services
cd ..
.\start_all_services.ps1
```

---

## 📞 Support Checklist

When reporting issues, provide:

1. **Service Status:**
   ```powershell
   Get-NetTCPConnection -LocalPort 3000,8001,5002,8765 -State Listen
   ```

2. **Logs:**
   - Backend logs (last 50 lines)
   - Monitoring logs (last 50 lines)
   - Extension output (from VS Code)
   - Browser console errors (F12)

3. **Configuration:**
   - OS version: `systeminfo | findstr /B /C:"OS Name" /C:"OS Version"`
   - Node version: `node --version`
   - Python version: `python --version`
   - VS Code version: Help → About

4. **Error Messages:**
   - Exact error text
   - Stack traces if available
   - Steps to reproduce

---

**Quick Reference Version:** 1.0.0  
**Last Updated:** October 31, 2025
