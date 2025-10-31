# VS Code Copilot Bridge Extension

This VS Code extension acts as a bridge between the DevMindAPI FastAPI service and GitHub Copilot Chat, with integrated Model Context Protocol (MCP) server support.

## Features

- WebSocket server that receives prompts from the FastAPI service
- Integrates with VS Code Language Model API to interact with Copilot
- **NEW: MCP Server Integration** - Automatically discovers and communicates with MCP servers
- **NEW: Enhanced Context** - Enriches prompts with data from MCP tools and resources
- Returns Copilot responses back to the API
- Auto-starts on VS Code launch (configurable)

## Installation

### 1. Install Dependencies

```powershell
cd C:\Users\GBS09281\Hackathon\DevMindAPI\vscode-copilot-bridge
npm install
```

### 2. Compile the Extension

```powershell
npm run compile
```

### 3. Run in Development Mode

Press `F5` in VS Code to open a new Extension Development Host window with the extension loaded.

### 4. Install the Extension (Optional)

To install permanently:

```powershell
npm run compile
code-insiders --install-extension .
```

Or package it:

```powershell
npm install -g @vscode/vsce
vsce package
code-insiders --install-extension vscode-copilot-bridge-1.0.0.vsix
```

## Configuration

The extension can be configured via VS Code settings:

- `copilotBridge.port`: WebSocket server port (default: 8765)
- `copilotBridge.autoStart`: Auto-start server on VS Code launch (default: true)
- `copilotBridge.enableMCP`: Enable MCP server integration (default: true)
- `copilotBridge.mcpTimeout`: Timeout for MCP queries in milliseconds (default: 5000)

## MCP Server Configuration

To use MCP servers with the bridge, create a `.vscode/mcp.json` file in the `vscode-copilot-bridge` directory:

```json
{
  "servers": {
    "weather": {
      "command": "python",
      "args": ["weather.py"],
      "cwd": "C:\\Thiru\\MCP_Workplace"
    },
    "database": {
      "command": "node",
      "args": ["db-server.js"],
      "cwd": "./mcp-servers"
    }
  }
}
```

The extension will automatically:
1. Discover MCP servers from `vscode-copilot-bridge/.vscode/mcp.json`
2. Start MCP server processes
3. Query relevant tools based on the prompt
4. Enhance the agent's context with MCP data

## Commands

The extension provides the following commands (accessible via Command Palette - `Ctrl+Shift+P`):

- `Start Copilot Bridge Server` - Manually start the WebSocket server
- `Stop Copilot Bridge Server` - Stop the WebSocket server
- `Copilot Bridge Status` - Check if the server is running
- `Copilot Bridge - MCP Server Status` - View active MCP servers and their status

## How It Works

1. The extension starts a WebSocket server on port 8765
2. **The extension discovers and starts MCP servers from `vscode-copilot-bridge/.vscode/mcp.json`**
3. The FastAPI service connects to this WebSocket server
4. When a prompt is received:
   - **The extension queries relevant MCP servers for context**
   - **MCP tools are called based on prompt analysis (e.g., weather queries)**
   - The extension uses VS Code's Language Model API
   - **Sends the enhanced prompt (with MCP context) to GitHub Copilot**
   - Waits for the response
   - Sends the response back via WebSocket

### MCP Integration Flow

```
User Prompt → FastAPI → WebSocket → Bridge Extension
                                          ↓
                                    MCP Servers
                                    (weather, db, etc.)
                                          ↓
                                    Gather Context
                                          ↓
                            Enhanced Prompt + MCP Data
                                          ↓
                                    GitHub Copilot
                                          ↓
                                    AI Response
                                          ↓
                              WebSocket → FastAPI → User
```

## Requirements

- VS Code Insiders (version 1.85.0 or higher)
- GitHub Copilot extension installed and activated
- Active GitHub Copilot subscription

## Troubleshooting

### Extension Not Starting

1. Check the Output panel: View → Output → Select "Copilot Bridge"
2. Ensure VS Code Insiders is used (not regular VS Code)
3. Verify GitHub Copilot extension is installed

### Port Already in Use

If port 8765 is already in use, change it in settings:
1. Open Settings (`Ctrl+,`)
2. Search for "copilot bridge"
3. Change the port number

### Copilot Not Responding

1. Ensure GitHub Copilot is enabled: Check status bar
2. Verify your Copilot subscription is active
3. Try signing out and back into GitHub in VS Code

## Development

### Project Structure

```
vscode-copilot-bridge/
├── src/
│   └── extension.ts       # Main extension code
├── out/                   # Compiled JavaScript output
├── package.json           # Extension manifest
├── tsconfig.json          # TypeScript configuration
└── README.md
```

### Building

```powershell
# Compile TypeScript
npm run compile

# Watch mode (auto-compile on changes)
npm run watch
```

### Debugging

1. Open the extension folder in VS Code
2. Press `F5` to start debugging
3. A new Extension Development Host window will open
4. Set breakpoints in `src/extension.ts`
5. Check Debug Console for logs

## License

MIT
