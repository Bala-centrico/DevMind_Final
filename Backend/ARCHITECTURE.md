# DevMindAPI Architecture

## System Overview

DevMindAPI is a bridge system that enables programmatic access to VS Code's GitHub Copilot Chat through a REST API.

## Components

### 1. FastAPI Service (`main.py`)
- **Language**: Python 3.8+
- **Framework**: FastAPI
- **Port**: 8000 (HTTP)
- **Purpose**: Provides REST API endpoints for external applications

**Key Features**:
- Request validation using Pydantic models
- WebSocket client to communicate with VS Code extension
- Async/await for non-blocking operations
- CORS support for web applications
- Comprehensive error handling

**Endpoints**:
- `GET /` - API information
- `GET /health` - Health check and bridge status
- `POST /api/v1/copilot/chat` - Send prompt to Copilot

### 2. VS Code Extension (`vscode-copilot-bridge/`)
- **Language**: TypeScript
- **Platform**: VS Code Insiders Extension
- **Port**: 8765 (WebSocket)
- **Purpose**: Bridge between API and VS Code Copilot

**Key Features**:
- WebSocket server for API communication
- Integration with VS Code Language Model API
- Auto-start on VS Code launch
- Configuration through VS Code settings
- Detailed logging to Output panel

**Commands**:
- Start Copilot Bridge Server
- Stop Copilot Bridge Server
- Copilot Bridge Status

## Communication Flow

```
┌─────────────────┐
│  External App   │
│  (Your Code)    │
└────────┬────────┘
         │
         │ HTTP POST
         │ {"prompt": "..."}
         │
         ▼
┌─────────────────────────┐
│   DevMindAPI (FastAPI)  │
│   Port 8000             │
├─────────────────────────┤
│ 1. Validate prompt      │
│ 2. Create WebSocket     │
│    connection           │
│ 3. Send request         │
│ 4. Wait for response    │
│ 5. Return to client     │
└────────┬────────────────┘
         │
         │ WebSocket
         │ ws://localhost:8765
         │
         ▼
┌─────────────────────────────┐
│  VS Code Extension          │
│  (Copilot Bridge)           │
├─────────────────────────────┤
│ 1. Receive prompt           │
│ 2. Call Language Model API  │
│ 3. Send to Copilot          │
│ 4. Capture response         │
│ 5. Return via WebSocket     │
└────────┬────────────────────┘
         │
         │ VS Code API
         │
         ▼
┌─────────────────────────┐
│  GitHub Copilot Chat    │
│  (Language Model)       │
├─────────────────────────┤
│ - Process prompt        │
│ - Generate response     │
│ - Return answer         │
└─────────────────────────┘
```

## Data Flow

### Request Flow

1. **Client → FastAPI**
   ```json
   POST /api/v1/copilot/chat
   {
     "prompt": "What is Python?",
     "timeout": 60
   }
   ```

2. **FastAPI → VS Code Extension** (WebSocket)
   ```json
   {
     "type": "copilot_request",
     "requestId": "2025-10-17T10:30:00.123",
     "prompt": "What is Python?",
     "timestamp": "2025-10-17T10:30:00.123"
   }
   ```

3. **VS Code Extension → Copilot** (Language Model API)
   ```typescript
   messages = [LanguageModelChatMessage.User("What is Python?")]
   response = await model.sendRequest(messages, {}, token)
   ```

### Response Flow

1. **Copilot → VS Code Extension**
   ```
   Stream of text fragments
   "Python is a high-level..."
   ```

2. **VS Code Extension → FastAPI** (WebSocket)
   ```json
   {
     "type": "copilot_response",
     "requestId": "2025-10-17T10:30:00.123",
     "response": "Python is a high-level programming language...",
     "timestamp": "2025-10-17T10:30:00.456"
   }
   ```

3. **FastAPI → Client**
   ```json
   {
     "success": true,
     "response": "Python is a high-level programming language...",
     "prompt": "What is Python?",
     "timestamp": "2025-10-17T10:30:00.789",
     "error": null
   }
   ```

## Error Handling

### Validation Errors (422)
- Empty or whitespace-only prompts
- Invalid request format
- Missing required fields

### Service Errors (503)
- VS Code extension not running
- WebSocket connection failed
- Bridge not connected

### Timeout Errors (504)
- Copilot response exceeds timeout
- Default timeout: 60 seconds
- Configurable per request

### Internal Errors (500)
- Unexpected exceptions
- WebSocket communication errors
- Copilot API errors

## Security Considerations

### Current Implementation
- No authentication (local use only)
- CORS enabled for all origins
- WebSocket on localhost only
- No rate limiting

### Production Recommendations
1. **Add Authentication**
   - API keys or OAuth tokens
   - JWT-based authentication
   
2. **Restrict CORS**
   - Whitelist specific origins
   - Remove `allow_origins=["*"]`
   
3. **Add Rate Limiting**
   - Prevent abuse
   - Use libraries like `slowapi`
   
4. **Secure WebSocket**
   - Use WSS (WebSocket Secure)
   - Add authentication tokens
   
5. **Input Sanitization**
   - Additional prompt validation
   - Content filtering

## Scalability

### Current Limitations
- Single WebSocket connection
- Synchronous request handling (one at a time)
- Local deployment only

### Scaling Options

1. **Connection Pooling**
   ```python
   # Multiple WebSocket connections
   connection_pool = []
   ```

2. **Message Queue**
   ```python
   # Use Redis or RabbitMQ
   # Decouple API from extension
   ```

3. **Multiple VS Code Instances**
   ```python
   # Load balance across instances
   # Different ports per instance
   ```

## Configuration

### FastAPI Configuration
```python
# main.py
WS_HOST = "localhost"
WS_PORT = 8765
REQUEST_TIMEOUT = 60
```

### Extension Configuration
```json
// VS Code settings.json
{
  "copilotBridge.port": 8765,
  "copilotBridge.autoStart": true
}
```

## Monitoring & Logging

### FastAPI Logs
- Request/response logging
- WebSocket connection status
- Error tracking

### Extension Logs
- View → Output → "Copilot Bridge"
- Connection events
- Copilot interactions
- Error messages

## Dependencies

### Python (FastAPI)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket client
- `pydantic` - Data validation

### TypeScript (Extension)
- `@types/vscode` - VS Code API types
- `ws` - WebSocket server
- `typescript` - Language compiler

## Deployment Options

### Development
- Local machine
- VS Code debug mode
- Hot reload enabled

### Production
- Package extension as VSIX
- Run FastAPI with gunicorn
- Use process manager (PM2, systemd)
- Deploy behind reverse proxy (nginx)

## Future Enhancements

1. **Multiple Model Support**
   - GPT-3.5, GPT-4, Claude
   - Model selection per request

2. **Conversation History**
   - Multi-turn conversations
   - Context preservation

3. **Streaming Responses**
   - Server-Sent Events (SSE)
   - WebSocket for clients

4. **Caching**
   - Cache common prompts
   - Reduce Copilot API calls

5. **Analytics**
   - Usage statistics
   - Performance metrics
   - Cost tracking

## Testing

### Unit Tests
- FastAPI endpoint tests
- Request validation tests
- WebSocket communication tests

### Integration Tests
- End-to-end flow tests
- Error scenario tests
- Timeout handling tests

### Load Tests
- Concurrent request handling
- Performance benchmarks
- Stress testing

## Troubleshooting

### Common Issues

1. **Bridge Not Connected**
   - Check VS Code extension is running
   - Verify port 8765 is available
   - Check WebSocket logs

2. **Copilot Not Responding**
   - Verify Copilot subscription
   - Check Copilot extension status
   - Review VS Code logs

3. **Timeout Errors**
   - Increase timeout value
   - Check network connectivity
   - Simplify complex prompts

## License

MIT License - Free to use and modify
