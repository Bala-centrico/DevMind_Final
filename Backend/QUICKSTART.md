# Quick Start Guide - DevMindAPI

## Overview

DevMindAPI is a FastAPI service that bridges with VS Code Copilot Chat, allowing you to interact with GitHub Copilot programmatically through REST API calls.

## Prerequisites

- Python 3.8 or higher
- VS Code Insiders (recommended) or VS Code
- Node.js 16 or higher
- GitHub Copilot subscription
- GitHub Copilot extension installed in VS Code

## Installation Steps

### Step 1: Install Python Dependencies

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI
pip install -r requirements.txt
```

### Step 2: Set Up VS Code Extension

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI\vscode-copilot-bridge
npm install
npm run compile
```

## Running the System

### Option A: Quick Start (Recommended for Testing)

1. **Start VS Code Extension (Method 1 - Debug Mode)**
   - Open the folder `vscode-copilot-bridge` in VS Code Insiders
   - Press `F5` - this will open a new Extension Development Host window
   - The bridge server will auto-start

2. **Start the FastAPI Service**
   ```powershell
   cd C:\Users\GBS09281\Hackathon\DevMindAPI
   python main.py
   ```
   
   Or use the batch file:
   ```powershell
   .\start_api.bat
   ```

3. **The API will be available at:** `http://localhost:8000`

### Option B: Production Setup

1. **Install the Extension Permanently**
   ```powershell
   cd C:\Users\GBS09281\Hackathon\DevMindAPI\vscode-copilot-bridge
   npm install -g @vscode/vsce
   vsce package
   code-insiders --install-extension vscode-copilot-bridge-1.0.0.vsix
   ```

2. **Start VS Code Insiders** - the extension will auto-start

3. **Start the API** (same as above)

## Testing the API

### Method 1: Using PowerShell Test Script

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI
.\test_api.ps1
```

### Method 2: Using Python Test Script

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI
python test_api.py
```

### Method 3: Using cURL

```powershell
# Health check
curl http://localhost:8000/health

# Send a prompt to Copilot
curl -X POST "http://localhost:8000/api/v1/copilot/chat" `
  -H "Content-Type: application/json" `
  -d '{\"prompt\": \"What is FastAPI?\"}'
```

### Method 4: Using Python Requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/copilot/chat",
    json={"prompt": "Explain recursion in simple terms"}
)

print(response.json())
```

### Method 5: Interactive API Docs

Open your browser and go to: `http://localhost:8000/docs`

## API Endpoints

### 1. GET /health
Check API and bridge status

**Response:**
```json
{
  "status": "healthy",
  "bridge_connected": true,
  "timestamp": "2025-10-17T10:30:00"
}
```

### 2. POST /api/v1/copilot/chat
Send a prompt to Copilot

**Request:**
```json
{
  "prompt": "Your question here",
  "timeout": 60
}
```

**Response:**
```json
{
  "success": true,
  "response": "Copilot's answer...",
  "prompt": "Your question here",
  "timestamp": "2025-10-17T10:30:00",
  "error": null
}
```

## Troubleshooting

### Issue: "Bridge not connected" error

**Solution:**
1. Ensure VS Code Insiders is running
2. Check that the extension is activated:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Run: "Copilot Bridge Status"
3. Check VS Code Output panel:
   - View → Output → Select "Copilot Bridge"
4. Manually start the bridge:
   - Command Palette → "Start Copilot Bridge Server"

### Issue: "GitHub Copilot Chat extension not found"

**Solution:**
1. Install GitHub Copilot Chat extension:
   - Extensions → Search "GitHub Copilot Chat"
   - Install the extension
2. Ensure you're signed into GitHub
3. Verify your Copilot subscription is active

### Issue: Port 8765 already in use

**Solution:**
1. Open VS Code Settings (`Ctrl+,`)
2. Search: "copilot bridge port"
3. Change to a different port (e.g., 8766)
4. Update `main.py` to match:
   ```python
   WS_PORT = 8766  # Match your VS Code setting
   ```

### Issue: API returns 504 timeout

**Solution:**
1. Increase timeout in your request:
   ```json
   {"prompt": "...", "timeout": 120}
   ```
2. Check if Copilot is responding in VS Code
3. Try a simpler prompt first

## Example Use Cases

### 1. Code Explanation
```python
import requests

prompt = "Explain this code: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
response = requests.post(
    "http://localhost:8000/api/v1/copilot/chat",
    json={"prompt": prompt}
)
print(response.json()["response"])
```

### 2. Code Generation
```python
prompt = "Write a Python function to validate email addresses using regex"
response = requests.post(
    "http://localhost:8000/api/v1/copilot/chat",
    json={"prompt": prompt}
)
print(response.json()["response"])
```

### 3. Debugging Help
```python
prompt = "Why does this give an error: print(my_list[10]) when my_list only has 5 items?"
response = requests.post(
    "http://localhost:8000/api/v1/copilot/chat",
    json={"prompt": prompt}
)
print(response.json()["response"])
```

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│   Your App      │         │   VS Code Insiders   │
│                 │         │                      │
│  HTTP Request   │         │  ┌────────────────┐  │
└────────┬────────┘         │  │ Copilot Bridge │  │
         │                  │  │   Extension    │  │
         │                  │  └────────┬───────┘  │
         │                  │           │          │
         ▼                  │           │          │
┌─────────────────┐         │           │          │
│   DevMindAPI    │         │           │          │
│   (FastAPI)     │◄────────┼───────────┘          │
│   Port 8000     │ WebSocket (Port 8765)          │
└─────────────────┘         │                      │
                            │  ┌────────────────┐  │
                            │  │ GitHub Copilot │  │
                            │  │     Chat       │  │
                            │  └────────────────┘  │
                            └──────────────────────┘
```

## Next Steps

1. ✅ Basic setup and testing
2. 🔄 Integrate into your application
3. 📊 Add logging and monitoring
4. 🔒 Add authentication (if needed)
5. 🚀 Deploy to production

## Support

For issues or questions:
1. Check the logs in VS Code Output panel
2. Check the FastAPI logs in terminal
3. Review the README files in both directories
4. Test with simple prompts first

Happy coding! 🚀
