# DevMind System - Quick Start Guide

## Starting All Services

### Method 1: Double-Click (Easiest)
Simply double-click `START_DEVMIND.bat` in the DevMind_Final directory.

### Method 2: Python Script
```powershell
cd C:\CentricoINshared\DevMind_Final
python start_all_services.py
```

### Method 3: PowerShell (Advanced)
```powershell
cd C:\CentricoINshared\DevMind_Final
.\start_all_services.ps1
```

## What Gets Started

The launcher starts three services in separate terminal windows:

1. **Monitoring Service** (Port 5002)
   - Real-time WebSocket monitoring
   - Progress tracking
   - Database change notifications

2. **Backend API** (Port 8001)
   - FastAPI service
   - VS Code Copilot bridge
   - JIRA card management
   - Prompt injection

3. **Dashboard** (Port 3000)
   - React frontend
   - JIRA dashboard UI
   - Real-time progress monitoring

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Monitoring | http://localhost:5002 | Monitoring service API |
| Backend | http://localhost:8001 | Backend API |
| Backend Docs | http://localhost:8001/docs | Interactive API documentation |
| Dashboard | http://localhost:3000 | Main dashboard UI |

## Verifying Services

### Check if services are running:
```powershell
# Check ports
netstat -ano | findstr "5002 8001 3000"

# Or use PowerShell
Get-NetTCPConnection -LocalPort 5002,8001,3000 -State Listen
```

### Health Checks:
```powershell
# Backend API
curl http://localhost:8001/health

# Monitoring Service
curl http://localhost:5002/api/health

# Dashboard (should return HTML)
curl http://localhost:3000
```

## Stopping Services

### Method 1: From Python Launcher
Press `Ctrl+C` in the terminal where you started the Python script.

### Method 2: Manual
Close each terminal window individually.

### Method 3: PowerShell Kill Script
```powershell
cd C:\CentricoINshared\DevMind_Final
.\stop_all_services.ps1
```

## Troubleshooting

### Port Already in Use
If you see "port already in use" errors:

```powershell
# Find what's using the port (example for port 8001)
netstat -ano | findstr :8001

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Service Won't Start

1. **Check Python is installed:**
   ```powershell
   python --version
   ```

2. **Check Node.js is installed (for Dashboard):**
   ```powershell
   node --version
   npm --version
   ```

3. **Check dependencies:**
   ```powershell
   # Backend dependencies
   cd Backend
   pip install -r requirements.txt

   # Dashboard dependencies
   cd Dashboard
   npm install
   ```

### Database Connection Issues

If you see database errors:
1. Verify database path: `Z:\mcp_dashboard.db`
2. Check network connection to NAS
3. Verify database file permissions

### VS Code Extension

**Note:** The VS Code extension (port 8765) must be started manually:
1. Open VS Code
2. The extension should auto-start
3. Check Output panel → "Copilot Bridge"

## Log Files

Each service outputs logs to its terminal window. To save logs:

```powershell
# Example: Save backend logs
cd Backend
python main.py > backend.log 2>&1
```

## Development Mode

For development with auto-reload:

### Backend:
Already runs with `reload=True` in `main.py`

### Dashboard:
```powershell
cd Dashboard
npm start
```
Changes will auto-reload in browser.

## Architecture Overview

```
┌─────────────────┐
│   Dashboard     │ (Port 3000)
│   (React UI)    │
└────────┬────────┘
         │
         ├──HTTP──→ ┌─────────────────┐
         │          │  Backend API    │ (Port 8001)
         │          │  (FastAPI)      │
         │          └────────┬────────┘
         │                   │
         ├──WS────→ ┌────────┴────────┐
         │          │  Monitoring     │ (Port 5002)
         │          │  Service        │
         │          └─────────────────┘
         │
         └──WS────→ ┌─────────────────┐
                    │  VS Code        │ (Port 8765)
                    │  Extension      │
                    └─────────────────┘
```

## Environment Variables

The system uses the following key environment variables:

- `NODE_OPTIONS=--openssl-legacy-provider` (for Dashboard)
- Database path: `Z:\mcp_dashboard.db`

## Next Steps

After all services are running:

1. Open Dashboard: http://localhost:3000
2. Check Backend API docs: http://localhost:8001/docs
3. Verify health endpoints
4. Start VS Code extension
5. Begin working with JIRA cards

## Support

For issues or questions:
- Check logs in each service terminal
- Review `DEPLOYMENT_SUMMARY.md`
- Check `TROUBLESHOOTING.md`

---

**Last Updated:** October 31, 2025  
**Version:** 1.0.0
