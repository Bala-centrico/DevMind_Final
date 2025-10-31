# MCP Integration Guide

## Overview

The VS Code Copilot Bridge Extension now integrates with Model Context Protocol (MCP) servers to provide enhanced context to AI agents. This allows the Copilot agent to access external tools, databases, APIs, and other resources through standardized MCP servers.

## What is MCP?

Model Context Protocol (MCP) is a standardized protocol for connecting AI models to external context sources. MCP servers expose:

- **Tools**: Functions the AI can call (e.g., get_weather, query_database)
- **Resources**: Data sources the AI can read (e.g., files, API endpoints)
- **Prompts**: Pre-defined prompt templates

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Service                          │
│                        (DevMindAPI)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              VS Code Copilot Bridge Extension                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  WebSocket       │  │  MCP Server      │                    │
│  │  Server          │  │  Manager         │                    │
│  │  (Port 8765)     │  │                  │                    │
│  └──────────────────┘  └────────┬─────────┘                    │
│                                 │                                │
│                    ┌────────────┴─────────────┐                │
│                    ▼                           ▼                 │
│         ┌──────────────────┐      ┌──────────────────┐         │
│         │  MCP Server 1    │      │  MCP Server 2    │         │
│         │  (Weather)       │      │  (Database)      │         │
│         └──────────────────┘      └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VS Code Language Model API                    │
│                    (GitHub Copilot / Claude)                     │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. MCP Server Discovery

On activation, the extension:
1. Scans all workspace folders for `.vscode/mcp.json`
2. Reads MCP server configurations
3. Starts each configured MCP server as a child process

### 2. Prompt Enhancement

When a prompt is received:
1. The extension analyzes the prompt for relevant topics
2. Queries appropriate MCP servers for context
3. Combines MCP responses with the original prompt
4. Sends the enhanced prompt to the AI agent

### 3. MCP Communication

The extension uses JSON-RPC 2.0 to communicate with MCP servers:

```typescript
// Initialize MCP server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "0.1.0",
    "clientInfo": {
      "name": "vscode-copilot-bridge",
      "version": "1.0.0"
    }
  }
}

// Call a tool
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "San Francisco"
    }
  }
}
```

## Configuration

### Basic MCP Configuration

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "weather": {
      "command": "python",
      "args": ["weather.py"],
      "cwd": "C:\\Thiru\\MCP_Workplace"
    }
  }
}
```

### Multiple MCP Servers

```json
{
  "servers": {
    "weather": {
      "command": "python",
      "args": ["weather.py"],
      "cwd": "./mcp-servers"
    },
    "database": {
      "command": "node",
      "args": ["db-server.js"],
      "cwd": "./mcp-servers"
    },
    "filesystem": {
      "command": "python",
      "args": ["-m", "mcp.servers.filesystem"],
      "cwd": "."
    }
  }
}
```

## Creating MCP Servers

### Example: Weather MCP Server (Python)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
def get_weather(location: str) -> str:
    """
    Gets the weather given a location
    Args:
        location: location, can be city, country, state, etc.
    """
    # In real implementation, call weather API
    return f"The weather in {location} is sunny and 72°F"

@mcp.tool()
def get_forecast(location: str, days: int = 3) -> str:
    """
    Gets weather forecast for multiple days
    Args:
        location: location to get forecast for
        days: number of days (default: 3)
    """
    return f"{days}-day forecast for {location}: Mostly sunny"

if __name__ == "__main__":
    mcp.run()
```

### Example: Database MCP Server (Node.js)

```javascript
const { Server } = require('@modelcontextprotocol/sdk/server');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio');

const server = new Server(
  {
    name: 'database-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register query_database tool
server.setRequestHandler('tools/list', async () => ({
  tools: [
    {
      name: 'query_database',
      description: 'Query the database with SQL',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'SQL query to execute',
          },
        },
        required: ['query'],
      },
    },
  ],
}));

server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'query_database') {
    const { query } = request.params.arguments;
    // Execute database query
    const results = await db.query(query);
    return {
      content: JSON.stringify(results),
    };
  }
});

const transport = new StdioServerTransport();
server.connect(transport);
```

## Prompt Analysis and MCP Tool Selection

The extension automatically detects which MCP tools to use based on prompt content:

| Prompt Keywords | MCP Server | Tool Called |
|----------------|------------|-------------|
| weather, temperature, forecast | Weather | get_weather |
| query, database, sql | Database | query_database |
| file, read, write | Filesystem | read_file, write_file |

### Example Flow

**User Prompt**: "What's the weather in San Francisco?"

1. Extension detects "weather" keyword
2. Calls `weather` MCP server's `get_weather` tool with location="San Francisco"
3. MCP server returns: "The weather in San Francisco is sunny and 72°F"
4. Enhanced prompt sent to AI:
   ```
   What's the weather in San Francisco?
   
   [MCP Context]
   Weather Information (San Francisco): The weather is sunny and 72°F
   ```
5. AI agent receives full context and provides informed response

## API Changes

### Request Format (from FastAPI)

```json
{
  "type": "copilot_request",
  "requestId": "req-123",
  "prompt": "What's the weather in London?",
  "useMCP": true
}
```

### Response Format (to FastAPI)

```json
{
  "type": "copilot_response",
  "requestId": "req-123",
  "response": "The weather in London is currently cloudy with...",
  "mcpUsed": true,
  "mcpServers": ["weather"],
  "timestamp": "2025-10-21T10:30:00Z"
}
```

## Settings

Configure MCP behavior in VS Code settings:

```json
{
  "copilotBridge.enableMCP": true,
  "copilotBridge.mcpTimeout": 5000
}
```

## Debugging

### View MCP Server Logs

1. Open Output panel: `View → Output`
2. Select "Copilot Bridge" from dropdown
3. Look for MCP server messages:
   ```
   [weather] Received request: get_weather
   [weather] Response: The weather is sunny
   ✓ Got weather data: The weather is sunny
   ```

### Check MCP Status

Run command: `Copilot Bridge - MCP Server Status`

This shows:
- Number of configured MCP servers
- Number of active servers
- Available tools per server

### Common Issues

**MCP Server Not Starting**
- Check command path in `mcp.json`
- Verify working directory (`cwd`) exists
- Check Output panel for error messages

**No MCP Context in Response**
- Ensure `copilotBridge.enableMCP` is `true`
- Check if prompt keywords match MCP tools
- Verify MCP server is running (check status)

**Timeout Errors**
- Increase `copilotBridge.mcpTimeout` setting
- Check if MCP server is responding slowly
- Simplify MCP tool logic

## Advanced Usage

### Custom MCP Tool Detection

Extend `queryMCPServers()` in `extension.ts`:

```typescript
// Add custom detection logic
if (name === 'git' && /commit|branch|diff|log/i.test(prompt)) {
    // Call git MCP tools
}

if (name === 'jira' && /ticket|issue|story|bug/i.test(prompt)) {
    // Call JIRA MCP tools
}
```

### Parallel MCP Queries

Query multiple MCP servers simultaneously:

```typescript
const mcpPromises = Array.from(mcpServers.entries()).map(
    ([name, server]) => queryMCPServer(name, server, prompt)
);

const results = await Promise.all(mcpPromises);
```

### MCP Response Caching

Cache frequent MCP queries to improve performance:

```typescript
const cache = new Map<string, { data: string, timestamp: number }>();

function getCachedMCPResult(key: string, ttl: number = 300000) {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < ttl) {
        return cached.data;
    }
    return null;
}
```

## Best Practices

1. **Start Simple**: Begin with one MCP server and expand
2. **Error Handling**: MCP queries should fail gracefully
3. **Timeouts**: Set appropriate timeouts for MCP tools
4. **Logging**: Log all MCP interactions for debugging
5. **Security**: Validate MCP server paths and commands
6. **Performance**: Cache frequent MCP queries
7. **Context Size**: Limit MCP context to avoid token limits

## Resources

- [MCP Specification](https://modelcontextprotocol.io)
- [FastMCP Python Library](https://github.com/jlowin/fastmcp)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Example MCP Servers](https://github.com/modelcontextprotocol/servers)

## Examples

See the `/examples` directory for:
- Weather MCP server
- Database MCP server
- Filesystem MCP server
- Custom tool integration

## Support

For issues or questions:
1. Check the Output panel logs
2. Run MCP Status command
3. Review this documentation
4. Check GitHub issues
