# DevMindAPI - Visual Setup Guide

## 🎯 Complete Solution Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DevMindAPI System                         │
│                  FastAPI + VS Code Copilot Bridge               │
└─────────────────────────────────────────────────────────────────┘

   External Application                    VS Code Insiders
         (Your Code)                      (Extension Host)
              │                                   │
              │                                   │
              ▼                                   ▼
    ┌──────────────────┐              ┌──────────────────────┐
    │   HTTP Client    │              │  Copilot Bridge Ext  │
    │                  │              │                      │
    │  POST /api/v1/   │              │  WebSocket Server    │
    │  copilot/chat    │              │  Port: 8765          │
    └────────┬─────────┘              └──────────┬───────────┘
             │                                   │
             │  {"prompt": "..."}                │
             ▼                                   │
    ┌──────────────────────────┐                │
    │     FastAPI Service      │                │
    │     Port: 8000           │                │
    ├──────────────────────────┤                │
    │ • Validate Prompt        │                │
    │ • Connect WebSocket ─────┼────────────────┘
    │ • Send Request           │
    │ • Wait for Response      │
    │ • Return JSON            │
    └──────────────────────────┘
                 │
                 │ WebSocket Message
                 │ {"type": "copilot_request", ...}
                 ▼
    ┌──────────────────────────┐
    │  VS Code Extension       │
    ├──────────────────────────┤
    │ • Receive Prompt         │
    │ • Call Language Model    │
    │ • Send to Copilot ───────┼───┐
    │ • Capture Response       │   │
    │ • Return via WebSocket   │   │
    └──────────────────────────┘   │
                 ▲                 │
                 │                 │
                 │ Response        │ Prompt
                 │                 │
                 │                 ▼
              ┌─────────────────────────┐
              │   GitHub Copilot Chat   │
              │   (Language Model)      │
              └─────────────────────────┘
```

---

## 📋 Installation Checklist

### Prerequisites
- [ ] Python 3.8 or higher installed
- [ ] Node.js 16 or higher installed
- [ ] VS Code Insiders installed
- [ ] GitHub Copilot extension installed
- [ ] Active GitHub Copilot subscription
- [ ] Git (optional, for version control)

### Setup Steps
- [ ] Run `.\setup.ps1` (automated setup)
- [ ] OR manually:
  - [ ] Install Python dependencies: `pip install -r requirements.txt`
  - [ ] Install Node dependencies: `cd vscode-copilot-bridge && npm install`
  - [ ] Compile extension: `npm run compile`
- [ ] Verify installation: `.\verify_installation.ps1`

### First Run
- [ ] Open extension in VS Code Insiders
- [ ] Press F5 to run extension (opens new window)
- [ ] Start FastAPI: `python main.py`
- [ ] Check health: `curl http://localhost:8000/health`
- [ ] Run tests: `.\test_api.ps1`

---

## 🚀 Quick Start Commands

### Terminal 1: VS Code Extension
```powershell
# Navigate to extension folder
cd C:\Users\GBS09281\Hackathon\DevMindAPI\vscode-copilot-bridge

# Open in VS Code Insiders
code-insiders .

# Then press F5 in VS Code to run
```

### Terminal 2: FastAPI Service
```powershell
# Navigate to project root
cd C:\Users\GBS09281\Hackathon\DevMindAPI

# Start the API
python main.py

# Or use batch file
.\start_api.bat
```

### Terminal 3: Testing
```powershell
# Quick test
.\test_api.ps1

# Detailed tests
python test_api.py

# Examples
python example_usage.py
```

---

## 📊 Request/Response Flow

### Step-by-Step Flow

```
1. Client Sends Request
   ↓
   POST http://localhost:8000/api/v1/copilot/chat
   {
     "prompt": "What is Python?",
     "timeout": 60
   }

2. FastAPI Validates
   ↓
   ✓ Prompt not empty
   ✓ Timeout is valid

3. FastAPI → WebSocket → Extension
   ↓
   {
     "type": "copilot_request",
     "requestId": "2025-10-17T10:30:00",
     "prompt": "What is Python?"
   }

4. Extension → Copilot
   ↓
   Uses VS Code Language Model API
   Sends prompt to GitHub Copilot

5. Copilot → Extension
   ↓
   Streams response text
   "Python is a high-level programming language..."

6. Extension → WebSocket → FastAPI
   ↓
   {
     "type": "copilot_response",
     "requestId": "2025-10-17T10:30:00",
     "response": "Python is a high-level programming language..."
   }

7. FastAPI → Client
   ↓
   {
     "success": true,
     "response": "Python is a high-level programming language...",
     "prompt": "What is Python?",
     "timestamp": "2025-10-17T10:30:01",
     "error": null
   }
```

---

## 🎨 API Endpoints Visual Guide

### GET /health
```
Request:  GET http://localhost:8000/health

Response: {
            "status": "healthy",
            "bridge_connected": true,
            "timestamp": "2025-10-17T10:30:00"
          }

Status:   200 OK
```

### POST /api/v1/copilot/chat
```
Request:  POST http://localhost:8000/api/v1/copilot/chat
          Content-Type: application/json
          
          {
            "prompt": "Your question here",
            "timeout": 60
          }

Response: {
            "success": true,
            "response": "Copilot's answer...",
            "prompt": "Your question here",
            "timestamp": "2025-10-17T10:30:00",
            "error": null
          }

Status:   200 OK (success)
          422 Unprocessable Entity (validation error)
          503 Service Unavailable (bridge not connected)
          504 Gateway Timeout (timeout exceeded)
```

---

## 🔧 Configuration Options

### FastAPI (main.py)
```python
# WebSocket Configuration
WS_HOST = "localhost"     # Change for remote extension
WS_PORT = 8765           # Match VS Code extension port
REQUEST_TIMEOUT = 60      # Default timeout in seconds

# Server Configuration
# In uvicorn.run():
host = "0.0.0.0"         # Listen on all interfaces
port = 8000              # API port
reload = True            # Auto-reload on code changes
```

### VS Code Extension (Settings)
```json
{
  // WebSocket server port
  "copilotBridge.port": 8765,
  
  // Auto-start server on VS Code launch
  "copilotBridge.autoStart": true
}
```

---

## 📈 Usage Examples Visual

### Example 1: Simple Question
```
┌──────────────────────────────────────┐
│  YOUR CODE                           │
├──────────────────────────────────────┤
│  import requests                     │
│                                      │
│  r = requests.post(                  │
│      "http://localhost:8000/api/v1/  │
│       copilot/chat",                 │
│      json={                          │
│          "prompt": "What is Python?" │
│      }                               │
│  )                                   │
│                                      │
│  print(r.json()["response"])         │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  OUTPUT                              │
├──────────────────────────────────────┤
│  Python is a high-level, interpreted │
│  programming language known for its  │
│  simplicity and readability...       │
└──────────────────────────────────────┘
```

### Example 2: Code Generation
```
┌──────────────────────────────────────┐
│  PROMPT                              │
├──────────────────────────────────────┤
│  "Write a Python function to reverse │
│   a string"                          │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  COPILOT RESPONSE                    │
├──────────────────────────────────────┤
│  def reverse_string(s):              │
│      return s[::-1]                  │
│                                      │
│  # Example usage:                    │
│  # reverse_string("hello")           │
│  # Output: "olleh"                   │
└──────────────────────────────────────┘
```

---

## 🐛 Troubleshooting Visual

```
┌─────────────────────────────────────────────────────────┐
│  PROBLEM: "Bridge not connected"                        │
├─────────────────────────────────────────────────────────┤
│  SYMPTOMS:                                              │
│    • API returns 503 error                              │
│    • Health check shows bridge_connected: false         │
│                                                         │
│  SOLUTION:                                              │
│    1. Check VS Code Insiders is running                 │
│    2. Verify extension is activated:                    │
│       Ctrl+Shift+P → "Copilot Bridge Status"            │
│    3. Check Output panel:                               │
│       View → Output → Select "Copilot Bridge"           │
│    4. Manually start:                                   │
│       Ctrl+Shift+P → "Start Copilot Bridge Server"      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PROBLEM: "Timeout waiting for response"                │
├─────────────────────────────────────────────────────────┤
│  SYMPTOMS:                                              │
│    • API returns 504 error                              │
│    • Long wait before error                             │
│                                                         │
│  SOLUTION:                                              │
│    1. Increase timeout in request:                      │
│       {"prompt": "...", "timeout": 120}                 │
│    2. Simplify the prompt                               │
│    3. Check Copilot is responding in VS Code            │
│    4. Verify internet connection                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PROBLEM: "Empty prompt validation error"               │
├─────────────────────────────────────────────────────────┤
│  SYMPTOMS:                                              │
│    • API returns 422 error                              │
│    • Error: "Prompt cannot be empty"                    │
│                                                         │
│  SOLUTION:                                              │
│    1. Check prompt is not empty string                  │
│    2. Check prompt is not whitespace only               │
│    3. Ensure "prompt" field is included in JSON         │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 File Organization

```
DevMindAPI/
│
├── 🚀 GETTING STARTED
│   ├── QUICKSTART.md              ← Start here!
│   ├── setup.ps1                  ← Run this first
│   └── verify_installation.ps1    ← Check setup
│
├── 📖 DOCUMENTATION
│   ├── README.md                  ← Main docs
│   ├── ARCHITECTURE.md            ← System design
│   ├── PROJECT_STRUCTURE.md       ← File organization
│   ├── IMPLEMENTATION_SUMMARY.md  ← What's included
│   └── VISUAL_GUIDE.md            ← This file
│
├── 💻 SOURCE CODE
│   ├── main.py                    ← FastAPI app
│   └── vscode-copilot-bridge/     ← VS Code extension
│       └── src/extension.ts
│
├── 🧪 TESTING
│   ├── test_api.py                ← Python tests
│   ├── test_api.ps1               ← PowerShell tests
│   └── example_usage.py           ← Usage examples
│
├── 🔧 UTILITIES
│   ├── start_api.bat              ← Start API (Windows)
│   ├── requirements.txt           ← Python deps
│   └── .gitignore                 ← Git config
│
└── 📦 DEPENDENCIES
    ├── venv/                      ← Python virtual env
    └── node_modules/              ← Node packages
```

---

## ✅ Success Checklist

After setup, you should have:

- [x] ✓ FastAPI running on http://localhost:8000
- [x] ✓ Extension running in VS Code Insiders
- [x] ✓ WebSocket connection established on port 8765
- [x] ✓ Health endpoint returns "bridge_connected": true
- [x] ✓ Can send prompts and receive responses
- [x] ✓ Interactive API docs at /docs
- [x] ✓ Tests passing successfully

---

## 🎓 Learning Path

1. **Understand the basics**
   - Read QUICKSTART.md
   - Run setup.ps1

2. **Explore the code**
   - Review main.py
   - Review extension.ts

3. **Test the system**
   - Run test_api.ps1
   - Try example_usage.py

4. **Read architecture**
   - Study ARCHITECTURE.md
   - Understand data flow

5. **Build your integration**
   - Use the API in your app
   - Customize as needed

---

## 🌟 What You Can Do Now

### ✅ Implemented Features

1. **Ask Questions**
   - "What is Python?"
   - "Explain recursion"
   - "What are design patterns?"

2. **Generate Code**
   - "Write a function to sort a list"
   - "Create a REST API endpoint"
   - "Implement binary search"

3. **Debug Code**
   - "Why does this code fail?"
   - "How to fix this error?"
   - "What's wrong with my logic?"

4. **Learn Concepts**
   - "Explain async/await"
   - "What is dependency injection?"
   - "How does FastAPI work?"

5. **Code Review**
   - "Review this function"
   - "Suggest improvements"
   - "Is this code efficient?"

---

**Ready to start coding? Follow QUICKSTART.md!** 🚀
