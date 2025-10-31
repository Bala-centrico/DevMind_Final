# DevMind System - Configuration Template
# Copy this file and customize for your environment

## ==============================================
## 1. JIRA CREDENTIALS
## ==============================================
# Location: C:\Users\YourUsername\.devmind\credentials.ini

[jira]
url = https://your-company.atlassian.net
username = your.email@company.com
api_token = YOUR_JIRA_API_TOKEN_HERE

# To get Jira API token:
# 1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
# 2. Click "Create API token"
# 3. Copy and paste above


## ==============================================
## 2. MCP SERVER CONFIGURATION
## ==============================================
# Location: %APPDATA%\Code\User\mcp.json
# Or: C:\Users\YourUsername\AppData\Roaming\Code\User\mcp.json

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

# Replace:
# - YourUsername with your Windows username
# - Python313 with your Python version if different


## ==============================================
## 3. BACKEND CONFIGURATION
## ==============================================
# File: Backend/main.py

# Database path (Line ~25)
DB_PATH = r"C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db"

# WebSocket configuration (Line ~30)
WS_HOST = "127.0.0.1"  # Do not change unless you know what you're doing
WS_PORT = 8765

# CORS settings (Line ~35)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Server settings (Line ~200)
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Backend API port
        log_level="info"
    )


## ==============================================
## 4. MONITORING SERVICE CONFIGURATION
## ==============================================
# File: Services/monitoring_service.py

# Server settings (Line ~150)
PORT = 5002  # Monitoring service port
HOST = "0.0.0.0"

# WebSocket settings (Line ~100)
WEBSOCKET_TIMEOUT = 60  # seconds
MAX_CONNECTIONS = 100


## ==============================================
## 5. DASHBOARD CONFIGURATION
## ==============================================
# File: Dashboard/package.json

# Change port (if needed)
{
  "scripts": {
    "start": "set PORT=3000 && react-scripts start",
    ...
  }
}

# File: Dashboard/src/App.tsx (Line ~20)
const API_BASE_URL = "http://localhost:8001/api/v1";
const MONITORING_WS_URL = "ws://localhost:5002/ws/monitor";


## ==============================================
## 6. EXTENSION CONFIGURATION
## ==============================================
# File: Extension/package.json

{
  "contributes": {
    "configuration": {
      "properties": {
        "copilotBridge.port": {
          "type": "number",
          "default": 8765,
          "description": "WebSocket server port"
        },
        "copilotBridge.maxIterations": {
          "type": "number",
          "default": 15,
          "description": "Maximum Copilot iterations"
        },
        "copilotBridge.progressTracking": {
          "type": "boolean",
          "default": true,
          "description": "Enable progress tracking"
        }
      }
    }
  }
}


## ==============================================
## 7. DATABASE PATHS
## ==============================================

# Main database
mcp_dashboard.db: C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db

# Optional Oracle standards database
oracle_standards.db: Z:\oracle_standards.db  # Or your network path


## ==============================================
## 8. SVN CONFIGURATION (Optional)
## ==============================================
# File: Services/DevMind_MCP.py

# SVN repository URL (Line ~80)
SVN_BASE_URL = "https://your-svn-server/repos/trunk"

# SVN credentials (if needed)
SVN_USERNAME = "your-svn-username"
SVN_PASSWORD = "your-svn-password"  # Use environment variable instead!


## ==============================================
## 9. ENVIRONMENT VARIABLES (Recommended)
## ==============================================

# Create a .env file in each directory:

# Backend/.env
DB_PATH=C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db
WS_HOST=127.0.0.1
WS_PORT=8765
JIRA_CREDENTIALS_PATH=C:\Users\YourUsername\.devmind\credentials.ini

# Services/.env
DB_PATH=C:\CentricoINshared\DevMind_Final\Database\mcp_dashboard.db
MONITORING_PORT=5002
JIRA_CREDENTIALS_PATH=C:\Users\YourUsername\.devmind\credentials.ini


## ==============================================
## 10. PORT SUMMARY
## ==============================================

Service              | Port  | Protocol | Configurable
---------------------|-------|----------|-------------
Dashboard            | 3000  | HTTP     | Yes
Backend API          | 8001  | HTTP     | Yes
Monitoring Service   | 5002  | HTTP/WS  | Yes
Extension WebSocket  | 8765  | WS       | Yes


## ==============================================
## 11. FIREWALL RULES (if needed)
## ==============================================

# Allow localhost connections (usually not needed)
# Run as Administrator:

New-NetFirewallRule -DisplayName "DevMind Dashboard" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "DevMind Backend" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "DevMind Monitoring" -Direction Inbound -LocalPort 5002 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "DevMind Extension" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow


## ==============================================
## 12. LOGGING CONFIGURATION
## ==============================================

# Backend logging (main.py)
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)

# Extension logging
# Check: VS Code Output panel → "Copilot Bridge"


## ==============================================
## 13. PERFORMANCE TUNING
## ==============================================

# Backend (main.py)
workers = 1  # Increase for production
timeout_keep_alive = 30
limit_concurrency = 100

# Monitoring Service (monitoring_service.py)
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
PING_INTERVAL = 20  # seconds
PING_TIMEOUT = 10  # seconds


## ==============================================
## NOTES
## ==============================================

1. Always use absolute paths in configuration files
2. Use raw strings (r"path") in Python to avoid escape issues
3. Never commit credentials to version control
4. Test configuration changes one at a time
5. Keep backups of working configurations

---

Last Updated: October 31, 2025
Version: 1.0.0
