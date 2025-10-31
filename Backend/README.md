# DevMindAPI - VS Code Copilot Bridge

A FastAPI service that bridges with VS Code Insiders Copilot Chat, allowing external applications to interact with GitHub Copilot programmatically.

## Architecture

This solution consists of two components:

1. **FastAPI Service** (`main.py`): REST API that receives prompts and returns Copilot responses
2. **VS Code Extension** (`vscode-copilot-bridge`): VS Code Insiders extension that acts as a bridge between the API and Copilot Chat

## Components

### 1. FastAPI Service

The API runs on `http://localhost:8000` and provides the following endpoints:

- `POST /api/v1/copilot/chat` - Send a prompt to Copilot and get response
- `GET /health` - Check API and bridge connection status
- `GET /docs` - Interactive API documentation (Swagger UI)

### 2. VS Code Extension Bridge

The extension runs a WebSocket server on `ws://localhost:8765` that:
- Receives prompts from the FastAPI service
- Injects them into VS Code Copilot Chat
- Captures Copilot's response
- Sends the response back to the API

## Installation

### Step 1: Install Python Dependencies

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI
pip install -r requirements.txt
```

### Step 2: Install VS Code Extension

1. Open VS Code Insiders
2. Open the extension folder:
   ```powershell
   cd C:\Users\GBS09281\Hackathon\DevMindAPI\vscode-copilot-bridge
   ```
3. Install dependencies:
   ```powershell
   npm install
   ```
4. Press F5 to run the extension in debug mode, or:
   ```powershell
   npm run compile
   code-insiders --install-extension .
   ```

## Usage

### Start the FastAPI Service

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI
python main.py
```

The API will be available at `http://localhost:8000`

### Start the VS Code Extension

1. Open VS Code Insiders
2. The extension should auto-start if installed
3. Or run it in debug mode (F5) from the extension folder

### Make API Requests

**Using cURL:**

```powershell
curl -X POST "http://localhost:8000/api/v1/copilot/chat" `
  -H "Content-Type: application/json" `
  -d '{"prompt": "Explain what is FastAPI in simple terms"}'
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/copilot/chat",
    json={"prompt": "Write a Python function to calculate fibonacci numbers"}
)

print(response.json())
```

**Response Format:**

```json
{
  "success": true,
  "response": "FastAPI is a modern, fast web framework for building APIs...",
  "prompt": "Explain what is FastAPI in simple terms",
  "timestamp": "2025-10-17T10:30:00.123456",
  "error": null
}
```

## API Endpoints

### POST /api/v1/copilot/chat

Send a prompt to Copilot Chat and get the response.

**Request Body:**
```json
{
  "prompt": "Your question or prompt here",
  "timeout": 60
}
```

**Response:**
```json
{
  "success": true,
  "response": "Copilot's response",
  "prompt": "Your original prompt",
  "timestamp": "2025-10-17T10:30:00",
  "error": null
}
```

### GET /health

Check the health status of the API and VS Code bridge connection.

**Response:**
```json
{
  "status": "healthy",
  "bridge_connected": true,
  "timestamp": "2025-10-17T10:30:00"
}
```

## Configuration

Edit the WebSocket configuration in `main.py`:

```python
WS_HOST = "localhost"
WS_PORT = 8765
REQUEST_TIMEOUT = 60  # seconds
```

## Error Handling

The API handles various error scenarios:

- **Empty Prompt**: Returns 422 validation error
- **Bridge Not Available**: Returns 503 Service Unavailable
- **Timeout**: Returns 504 Gateway Timeout
- **Bridge Connection Closed**: Returns 503 Service Unavailable

## Development

### Run in Development Mode

```powershell
# API with auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Interactive Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Bridge Not Connecting

1. Ensure VS Code Insiders is running
2. Check that the extension is activated
3. Verify WebSocket server is running on port 8765
4. Check VS Code extension logs (View -> Output -> Select "Copilot Bridge")

### Copilot Not Responding

1. Ensure GitHub Copilot is enabled in VS Code
2. Check your Copilot subscription is active
3. Verify Copilot Chat is accessible in VS Code
4. Check the timeout setting (increase if needed)

## License

MIT License
