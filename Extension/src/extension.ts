import * as vscode from 'vscode';
import { WebSocketServer, WebSocket } from 'ws';
import { spawn, ChildProcess } from 'child_process';

let outputChannel: vscode.OutputChannel;
let wsServer: WebSocketServer | null = null;
let isServerRunning = false;

// MCP Server Management
interface MCPServer {
    name: string;
    process: ChildProcess | null;
    available: boolean;
    tools: MCPTool[];
    resources: MCPResource[];
}

interface MCPTool {
    name: string;
    description: string;
    inputSchema: any;
}

interface MCPResource {
    uri: string;
    name: string;
    description?: string;
}

interface MCPRequest {
    jsonrpc: string;
    id: number;
    method: string;
    params?: any;
}

interface MCPResponse {
    jsonrpc: string;
    id: number;
    result?: any;
    error?: any;
}

let mcpServers: Map<string, MCPServer> = new Map();
let mcpRequestId = 1;
let extensionContext: vscode.ExtensionContext;

// Progress tracking
interface ProgressUpdate {
    jiraNumber: string;
    stage: string;
    status: 'pending' | 'in-progress' | 'completed' | 'error';
    message: string;
    progress: number;
    timestamp: string;
}

async function sendProgressUpdate(update: ProgressUpdate) {
    try {
        const response = await fetch('http://localhost:5002/api/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(update)
        });
        outputChannel.appendLine(`[Progress] ${update.jiraNumber}: ${update.progress}% - ${update.message}`);
    } catch (error: any) {
        // Monitoring service not running - not critical, just log
        outputChannel.appendLine(`[Progress] Failed to send update: ${error.message}`);
    }
}

export function activate(context: vscode.ExtensionContext) {
    extensionContext = context;
    outputChannel = vscode.window.createOutputChannel('Copilot Bridge');
    outputChannel.appendLine('VS Code Copilot Bridge extension activated');

    // Initialize MCP servers and register their tools
    initializeMCPServers();

    // Register commands
    const startCommand = vscode.commands.registerCommand('copilot-bridge.start', () => {
        startBridgeServer();
    });

    const stopCommand = vscode.commands.registerCommand('copilot-bridge.stop', () => {
        stopBridgeServer();
    });

    const statusCommand = vscode.commands.registerCommand('copilot-bridge.status', () => {
        showStatus();
    });

    const mcpStatusCommand = vscode.commands.registerCommand('copilot-bridge.mcpStatus', () => {
        showMCPStatus();
    });

    context.subscriptions.push(startCommand, stopCommand, statusCommand, mcpStatusCommand, outputChannel);

    // Auto-start if configured
    const config = vscode.workspace.getConfiguration('copilotBridge');
    const autoStart = config.get<boolean>('autoStart', true);
    
    if (autoStart) {
        outputChannel.appendLine('Auto-starting bridge server...');
        startBridgeServer();
    }
}

export function deactivate() {
    outputChannel.appendLine('Deactivating extension...');
    stopBridgeServer();
    shutdownMCPServers();
}

// MCP Server Initialization
async function initializeMCPServers() {
    outputChannel.appendLine('Initializing MCP servers...');
    
    try {
        // Try to find MCP configuration in workspace folders
        let mcpConfigPath: vscode.Uri | null = null;
        
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            // Check each workspace folder for .vscode/mcp.json
            for (const folder of vscode.workspace.workspaceFolders) {
                const configUri = vscode.Uri.joinPath(folder.uri, '.vscode', 'mcp.json');
                try {
                    await vscode.workspace.fs.stat(configUri);
                    mcpConfigPath = configUri;
                    outputChannel.appendLine(`Found MCP config at: ${configUri.fsPath}`);
                    break;
                } catch {
                    // File doesn't exist, continue searching
                }
            }
        }
        
        if (!mcpConfigPath) {
            outputChannel.appendLine('No MCP configuration file found in workspace folders');
            outputChannel.appendLine('Create .vscode/mcp.json in your workspace to configure MCP servers');
            return;
        }
        
        try {
            const configData = await vscode.workspace.fs.readFile(mcpConfigPath);
            const configText = Buffer.from(configData).toString('utf8');
            const config = JSON.parse(configText.replace(/\/\/.*/g, '')); // Remove comments
            
            if (config.servers) {
                for (const [serverName, serverConfig] of Object.entries(config.servers)) {
                    await startMCPServer(serverName, serverConfig as any);
                }
            }
        } catch (err: any) {
            outputChannel.appendLine(`MCP config file not found or invalid: ${err.message}`);
        }
        
        outputChannel.appendLine(`✓ Initialized ${mcpServers.size} MCP server(s)`);
        
        // Register all MCP tools as VS Code Language Model tools
        registerMCPToolsAsLanguageModelTools();
    } catch (error: any) {
        outputChannel.appendLine(`Error initializing MCP servers: ${error.message}`);
    }
}

// Register tools for a specific MCP server
function registerMCPToolsForServer(serverName: string, server: MCPServer) {
    if (!server.tools || server.tools.length === 0) {
        return;
    }

    outputChannel.appendLine(`✓ Server ${serverName} ready with ${server.tools.length} tools`);
    // Don't register with VS Code - we'll handle tool calls directly
}

// Register MCP tools as VS Code Language Model tools
function registerMCPToolsAsLanguageModelTools() {
    for (const [serverName, server] of mcpServers.entries()) {
        if (server.available && server.tools && server.tools.length > 0) {
            registerMCPToolsForServer(serverName, server);
        }
    }
    
    if (mcpServers.size === 0) {
        outputChannel.appendLine('No MCP servers with tools available yet');
    }
}

async function startMCPServer(name: string, config: any) {
    outputChannel.appendLine(`Starting MCP server: ${name}`);
    
    try {
        const mcpServer: MCPServer = {
            name,
            process: null,
            available: false,
            tools: [],
            resources: []
        };

        // Start the MCP server process
        const serverProcess = spawn(config.command, config.args || [], {
            cwd: config.cwd || process.cwd(),
            stdio: ['pipe', 'pipe', 'pipe']
        });

        mcpServer.process = serverProcess;

        // Handle server output
        let initResponse = '';
        serverProcess.stdout?.on('data', (data) => {
            const output = data.toString();
            initResponse += output;
            outputChannel.appendLine(`[${name}] ${output}`);
        });

        serverProcess.stderr?.on('data', (data) => {
            outputChannel.appendLine(`[${name}] Error: ${data.toString()}`);
        });

        serverProcess.on('error', (error) => {
            outputChannel.appendLine(`[${name}] Process error: ${error.message}`);
            mcpServer.available = false;
        });

        // Initialize the MCP server with JSON-RPC
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Wait for server to start

        // Send initialize request with proper capabilities
        const initRequest: MCPRequest = {
            jsonrpc: '2.0',
            id: mcpRequestId++,
            method: 'initialize',
            params: {
                protocolVersion: '2024-11-05',
                capabilities: {
                    roots: {
                        listChanged: true
                    },
                    sampling: {}
                },
                clientInfo: {
                    name: 'vscode-copilot-bridge',
                    version: '1.0.0'
                }
            }
        };

        serverProcess.stdin?.write(JSON.stringify(initRequest) + '\n');

        // Wait for initialization response
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Send initialized notification
        const initializedNotification = {
            jsonrpc: '2.0',
            method: 'notifications/initialized'
        };

        serverProcess.stdin?.write(JSON.stringify(initializedNotification) + '\n');

        // Wait a bit before querying tools
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Query available tools
        const toolsRequest: MCPRequest = {
            jsonrpc: '2.0',
            id: mcpRequestId++,
            method: 'tools/list',
            params: {}
        };

        // Set up continuous listener for tools list (MCP server may take 2-3 minutes to start)
        let buffer = '';
        const toolsDataHandler = (data: Buffer) => {
            const output = data.toString();
            buffer += output;
            
            // Try to parse complete JSON objects from buffer
            let startIdx = 0;
            while (true) {
                const jsonStart = buffer.indexOf('{', startIdx);
                if (jsonStart === -1) break;
                
                let braceCount = 0;
                let jsonEnd = -1;
                
                for (let i = jsonStart; i < buffer.length; i++) {
                    if (buffer[i] === '{') braceCount++;
                    if (buffer[i] === '}') braceCount--;
                    if (braceCount === 0) {
                        jsonEnd = i + 1;
                        break;
                    }
                }
                
                if (jsonEnd === -1) break; // Incomplete JSON
                
                const jsonStr = buffer.substring(jsonStart, jsonEnd);
                try {
                    const response: MCPResponse = JSON.parse(jsonStr);
                    if (response.id === toolsRequest.id && response.result?.tools) {
                        outputChannel.appendLine(`[${name}] ✓ Received ${response.result.tools.length} tools`);
                        mcpServer.tools = response.result.tools;
                        
                        // Register the tools immediately when they arrive
                        registerMCPToolsForServer(name, mcpServer);
                        return;
                    }
                } catch (e) {
                    // Ignore parse errors
                }
                
                startIdx = jsonEnd;
            }
            
            // Keep only unparsed data in buffer
            buffer = buffer.substring(startIdx);
        };
        
        serverProcess.stdout?.on('data', toolsDataHandler);
        serverProcess.stdin?.write(JSON.stringify(toolsRequest) + '\n');
        
        // Don't wait - let tools load asynchronously
        mcpServer.tools = [];
        mcpServer.available = true;
        mcpServers.set(name, mcpServer);
        
        outputChannel.appendLine(`✓ MCP server '${name}' started (waiting for tools list...)`);
    } catch (error: any) {
        outputChannel.appendLine(`Failed to start MCP server '${name}': ${error.message}`);
    }
}

function shutdownMCPServers() {
    outputChannel.appendLine('Shutting down MCP servers...');
    
    for (const [name, server] of mcpServers.entries()) {
        if (server.process) {
            server.process.kill();
            outputChannel.appendLine(`✓ Stopped MCP server: ${name}`);
        }
    }
    
    mcpServers.clear();
}

function showMCPStatus() {
    const activeServers = Array.from(mcpServers.values()).filter(s => s.available);
    const message = `MCP Servers: ${activeServers.length} active\n` +
                   activeServers.map(s => `  - ${s.name} (${s.tools.length} tools)`).join('\n');
    
    vscode.window.showInformationMessage(
        `${mcpServers.size} MCP server(s) configured, ${activeServers.length} active`
    );
    outputChannel.appendLine(message);
}

function startBridgeServer() {
    if (isServerRunning) {
        vscode.window.showInformationMessage('Copilot Bridge server is already running');
        return;
    }

    const config = vscode.workspace.getConfiguration('copilotBridge');
    const port = config.get<number>('port', 8765);

    try {
        wsServer = new WebSocketServer({ 
            port: port,
            host: '127.0.0.1'  // Explicitly bind to IPv4 localhost
        });

        wsServer.on('listening', () => {
            isServerRunning = true;
            outputChannel.appendLine(`✓ WebSocket server started on port ${port}`);
            vscode.window.showInformationMessage(`Copilot Bridge started on port ${port}`);
        });

        wsServer.on('connection', (ws: WebSocket) => {
            outputChannel.appendLine('✓ Client connected to bridge');

            ws.on('message', async (data: Buffer) => {
                try {
                    const message = JSON.parse(data.toString());
                    outputChannel.appendLine(`Received message: ${JSON.stringify(message)}`);

                    if (message.type === 'copilot_request') {
                        await handleCopilotRequest(ws, message);
                    }
                } catch (error) {
                    outputChannel.appendLine(`Error processing message: ${error}`);
                    sendError(ws, 'Invalid message format');
                }
            });

            ws.on('close', () => {
                outputChannel.appendLine('Client disconnected from bridge');
            });

            ws.on('error', (error) => {
                outputChannel.appendLine(`WebSocket error: ${error.message}`);
            });
        });

        wsServer.on('error', (error) => {
            outputChannel.appendLine(`Server error: ${error.message}`);
            vscode.window.showErrorMessage(`Copilot Bridge error: ${error.message}`);
            isServerRunning = false;
        });

    } catch (error: any) {
        outputChannel.appendLine(`Failed to start server: ${error.message}`);
        vscode.window.showErrorMessage(`Failed to start Copilot Bridge: ${error.message}`);
    }
}

function stopBridgeServer() {
    if (!isServerRunning || !wsServer) {
        vscode.window.showInformationMessage('Copilot Bridge server is not running');
        return;
    }

    wsServer.close(() => {
        outputChannel.appendLine('✓ WebSocket server stopped');
        isServerRunning = false;
        wsServer = null;
        vscode.window.showInformationMessage('Copilot Bridge stopped');
    });
}

function showStatus() {
    const status = isServerRunning ? 'Running' : 'Stopped';
    const config = vscode.workspace.getConfiguration('copilotBridge');
    const port = config.get<number>('port', 8765);
    
    vscode.window.showInformationMessage(
        `Copilot Bridge Status: ${status}${isServerRunning ? ` on port ${port}` : ''}`
    );
}

async function handleCopilotRequest(ws: WebSocket, message: any) {
    const prompt = message.prompt;
    const requestId = message.requestId;

    outputChannel.appendLine(`Processing Copilot request: "${prompt}"`);

    try {
        // Send the prompt directly to Copilot Chat
        // Copilot Chat already has access to MCP tools configured in VS Code
        const response = await sendToCopilotChat(prompt);
        
        // Send response back to client
        const responseMessage = {
            type: 'copilot_response',
            requestId: requestId,
            response: response,
            timestamp: new Date().toISOString()
        };

        ws.send(JSON.stringify(responseMessage));
        outputChannel.appendLine(`✓ Sent response back to client`);

    } catch (error: any) {
        outputChannel.appendLine(`Error getting Copilot response: ${error.message}`);
        sendError(ws, error.message);
    }
}

// Helper function to call MCP tools
async function callMCPTool(server: MCPServer, toolRequest: MCPRequest): Promise<string> {
    return new Promise<string>((resolve) => {
        const timeout = setTimeout(() => resolve(''), 5000);
        
        const dataHandler = (data: Buffer) => {
            const output = data.toString();
            try {
                const mcpResponse: MCPResponse = JSON.parse(output);
                if (mcpResponse.id === toolRequest.id && mcpResponse.result) {
                    clearTimeout(timeout);
                    server.process?.stdout?.off('data', dataHandler);
                    
                    // Handle different MCP response formats
                    let resultText = '';
                    const result = mcpResponse.result;
                    
                    if (typeof result === 'string') {
                        resultText = result;
                    } else if (result.content) {
                        // Handle content array (standard MCP format)
                        if (Array.isArray(result.content)) {
                            resultText = result.content
                                .map((item: any) => {
                                    if (typeof item === 'string') return item;
                                    if (item.text) return item.text;
                                    if (item.type === 'text' && item.text) return item.text;
                                    return JSON.stringify(item, null, 2);
                                })
                                .join('\n');
                        } else if (typeof result.content === 'string') {
                            resultText = result.content;
                        } else if (result.content.text) {
                            resultText = result.content.text;
                        } else {
                            resultText = JSON.stringify(result.content, null, 2);
                        }
                    } else if (result.text) {
                        resultText = result.text;
                    } else if (result.result) {
                        resultText = typeof result.result === 'string' 
                            ? result.result 
                            : JSON.stringify(result.result, null, 2);
                    } else {
                        // Fallback: pretty-print the entire result
                        resultText = JSON.stringify(result, null, 2);
                    }
                    
                    resolve(resultText);
                }
            } catch (e) {
                // Ignore parse errors
            }
        };

        server.process?.stdout?.on('data', dataHandler);
        server.process?.stdin?.write(JSON.stringify(toolRequest) + '\n');
    });
}

async function queryMCPServers(prompt: string): Promise<string> {
    const mcpResults: string[] = [];
    const allTools: string[] = [];

    // Collect all available tools from MCP servers
    for (const [name, server] of mcpServers.entries()) {
        if (!server.available || !server.process) {
            continue;
        }

        try {
            outputChannel.appendLine(`Querying MCP server: ${name}`);
            
            // Add tool information to context
            if (server.tools && server.tools.length > 0) {
                allTools.push(`\n[MCP Server: ${name}]`);
                allTools.push(`Available tools (${server.tools.length}):`);
                server.tools.forEach(tool => {
                    allTools.push(`- ${tool.name}: ${tool.description}`);
                });
            }

            // Check if prompt might need Jira information
            if (/jira|issue|ticket|CMU-|bug|story|task|status/i.test(prompt)) {
                // Extract Jira issue key from prompt
                const issueMatch = prompt.match(/\b([A-Z]+-\d+)\b/i);
                
                if (issueMatch) {
                    const issueKey = issueMatch[1].toUpperCase();
                    outputChannel.appendLine(`Found Jira issue key: ${issueKey}`);
                    
                    // Call the get_jira_issue tool
                    const toolRequest: MCPRequest = {
                        jsonrpc: '2.0',
                        id: mcpRequestId++,
                        method: 'tools/call',
                        params: {
                            name: 'get_jira_issue',
                            arguments: {
                                issue_key: issueKey
                            }
                        }
                    };
                    
                    const response = await callMCPTool(server, toolRequest);
                    if (response) {
                        mcpResults.push(`[Jira Issue ${issueKey}]\n${response}`);
                        outputChannel.appendLine(`✓ Got Jira data for ${issueKey}`);
                    }
                }
            }

            // Check if prompt might need weather information
            if (name === 'weather' && /weather|temperature|forecast|climate/i.test(prompt)) {
                // Extract location from prompt (simple heuristic)
                const locationMatch = prompt.match(/(?:in|at|for)\s+([A-Za-z\s]+)/i);
                const location = locationMatch ? locationMatch[1].trim() : 'unknown';

                // Call the weather tool
                const toolRequest: MCPRequest = {
                    jsonrpc: '2.0',
                    id: mcpRequestId++,
                    method: 'tools/call',
                    params: {
                        name: 'get_weather',
                        arguments: {
                            location: location
                        }
                    }
                };

                // Send request to MCP server
                let response = '';
                const responsePromise = new Promise<string>((resolve) => {
                    const timeout = setTimeout(() => resolve(''), 2000);
                    
                    const dataHandler = (data: Buffer) => {
                        const output = data.toString();
                        try {
                            const mcpResponse: MCPResponse = JSON.parse(output);
                            if (mcpResponse.id === toolRequest.id && mcpResponse.result) {
                                clearTimeout(timeout);
                                server.process?.stdout?.off('data', dataHandler);
                                
                                // Handle different MCP response formats
                                let resultText = '';
                                const result = mcpResponse.result;
                                
                                if (typeof result === 'string') {
                                    resultText = result;
                                } else if (result.content) {
                                    // Handle content array (standard MCP format)
                                    if (Array.isArray(result.content)) {
                                        resultText = result.content
                                            .map((item: any) => {
                                                if (typeof item === 'string') return item;
                                                if (item.text) return item.text;
                                                if (item.type === 'text' && item.text) return item.text;
                                                return JSON.stringify(item, null, 2);
                                            })
                                            .join('\n');
                                    } else if (typeof result.content === 'string') {
                                        resultText = result.content;
                                    } else if (result.content.text) {
                                        resultText = result.content.text;
                                    } else {
                                        resultText = JSON.stringify(result.content, null, 2);
                                    }
                                } else if (result.text) {
                                    resultText = result.text;
                                } else if (result.result) {
                                    resultText = typeof result.result === 'string' 
                                        ? result.result 
                                        : JSON.stringify(result.result, null, 2);
                                } else {
                                    // Fallback: pretty-print the entire result
                                    resultText = JSON.stringify(result, null, 2);
                                }
                                
                                resolve(resultText);
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    };

                    server.process?.stdout?.on('data', dataHandler);
                });

                server.process.stdin?.write(JSON.stringify(toolRequest) + '\n');
                response = await responsePromise;

                if (response) {
                    mcpResults.push(`Weather Information (${location}): ${response}`);
                    outputChannel.appendLine(`✓ Got weather data: ${response}`);
                }
            }

            // Add more MCP tool queries based on prompt analysis here

        } catch (error: any) {
            outputChannel.appendLine(`Error querying MCP server '${name}': ${error.message}`);
        }
    }

    // Combine tool information and results
    let finalContext = '';
    if (allTools.length > 0) {
        finalContext += allTools.join('\n') + '\n\n';
    }
    if (mcpResults.length > 0) {
        finalContext += mcpResults.join('\n\n');
    }

    return finalContext;
}

async function sendToCopilotChat(prompt: string): Promise<string> {
    outputChannel.appendLine('Sending request to GitHub Copilot Chat with MCP tools...');

    // Extract Jira number from prompt for progress tracking
    const jiraMatch = prompt.match(/\b([A-Z]+-\d+)\b/);
    const jiraNumber = jiraMatch ? jiraMatch[1] : 'UNKNOWN';
    
    // Send initial progress update
    await sendProgressUpdate({
        jiraNumber,
        stage: 'prompt_injected',
        status: 'in-progress',
        message: 'Prompt injected to Copilot Chat',
        progress: 10,
        timestamp: new Date().toISOString()
    });

    try {
        // Get available language models
        const allModels = await vscode.lm.selectChatModels();
        if (allModels.length === 0) {
            throw new Error('No language models available. Please ensure GitHub Copilot is properly configured.');
        }

        // Prefer Claude Sonnet or Copilot models
        let selectedModel = allModels.find(m => 
            m.name.toLowerCase().includes('claude') || 
            m.name.toLowerCase().includes('copilot')
        ) || allModels[0];

        outputChannel.appendLine(`Using model: ${selectedModel.name} (family: ${selectedModel.family})`);

        // Filter tools based on prompt content to avoid overwhelming the model
        const availableTools: vscode.LanguageModelChatTool[] = [];
        
        // Analyze prompt to determine relevant tool categories
        const promptLower = prompt.toLowerCase();
        const relevantToolCategories: string[] = [];
        
        // Jira-related tools
        if (/jira|issue|ticket|bug|story|task|status|CMU-|\b[A-Z]+-\d+\b/i.test(promptLower)) {
            relevantToolCategories.push('jira');
        }
        
        // SVN-related tools
        if (/svn|commit|revision|version|checkout|repository|file|code/i.test(promptLower)) {
            relevantToolCategories.push('svn');
        }
        
        // Oracle/SQL tools
        if (/oracle|sql|database|table|query|procedure|function|standard/i.test(promptLower)) {
            relevantToolCategories.push('oracle', 'sql');
        }
        
        // Weather tools (if available)
        if (/weather|temperature|forecast|climate/i.test(promptLower)) {
            relevantToolCategories.push('weather');
        }
        
        // If no specific categories detected, include a few general tools
        if (relevantToolCategories.length === 0) {
            relevantToolCategories.push('jira', 'oracle'); // Default useful tools
        }
        
        // Filter tools based on detected categories
        for (const [serverName, server] of mcpServers.entries()) {
            if (server.available && server.tools) {
                for (const tool of server.tools) {
                    const toolNameLower = tool.name.toLowerCase();
                    const toolDescLower = tool.description.toLowerCase();
                    
                    // Check if tool matches any relevant category
                    const isRelevant = relevantToolCategories.some(category => 
                        toolNameLower.includes(category) || 
                        toolDescLower.includes(category) ||
                        serverName.toLowerCase().includes(category)
                    );
                    
                    if (isRelevant) {
                        availableTools.push({
                            name: `${serverName}__${tool.name}`,
                            description: tool.description,
                            inputSchema: tool.inputSchema
                        });
                    }
                }
            }
        }

        outputChannel.appendLine(`✓ Detected categories: ${relevantToolCategories.join(', ')}`);
        outputChannel.appendLine(`✓ Passing ${availableTools.length} relevant MCP tools to language model`);

        // Create messages for the chat request
        let messages: vscode.LanguageModelChatMessage[] = [
            vscode.LanguageModelChatMessage.User(prompt)
        ];

        let finalResponse = '';
        let maxIterations = 15; // Allow more iterations for complex multi-step tasks (was 5)
        let iteration = 0;
        let currentProgress = 10; // Start at 10% (prompt injected)

        while (iteration < maxIterations) {
            iteration++;
            outputChannel.appendLine(`Iteration ${iteration}/${maxIterations}: Sending request...`);

            // Send request with MCP tools available
            const chatRequest = await selectedModel.sendRequest(
                messages,
                {
                    justification: 'Processing user request via REST API bridge',
                    tools: availableTools
                },
                new vscode.CancellationTokenSource().token
            );
            
            let response = '';
            const toolCalls: vscode.LanguageModelToolCallPart[] = [];

            // Process the response stream
            let fragmentCount = 0;
            for await (const fragment of chatRequest.stream) {
                fragmentCount++;
                if (fragment instanceof vscode.LanguageModelTextPart) {
                    response += fragment.value;
                    outputChannel.appendLine(`[Fragment ${fragmentCount}] TEXT: "${fragment.value.substring(0, 50)}${fragment.value.length > 50 ? '...' : ''}"`);
                } else if (fragment instanceof vscode.LanguageModelToolCallPart) {
                    toolCalls.push(fragment);
                    outputChannel.appendLine(`[Fragment ${fragmentCount}] TOOL CALL: ${fragment.name} with callId=${fragment.callId}`);
                } else {
                    outputChannel.appendLine(`[Fragment ${fragmentCount}] UNKNOWN TYPE: ${(fragment as any).constructor?.name || 'unknown'}`);
                }
            }
            outputChannel.appendLine(`Stream complete: ${fragmentCount} fragments total`);
            

            // Log the response details
            outputChannel.appendLine(`Response text: ${response.substring(0, 100)}${response.length > 100 ? '...' : ''}`);
            outputChannel.appendLine(`Tool calls detected: ${toolCalls.length}`);

            // If no tool calls, we're done - this is the final response
            if (toolCalls.length === 0) {
                finalResponse = response;
                outputChannel.appendLine(`✓ Final response received (no more tool calls) - ${finalResponse.length} characters`);
                break;
            }

            // Tool calls were made - this response is just intermediate text, not the final answer
            outputChannel.appendLine(`⚠️ Intermediate response detected - NOT returning this yet`);
            outputChannel.appendLine(`⚠️ Executing ${toolCalls.length} tool call(s) first...`);
            const toolResults: vscode.LanguageModelToolResultPart[] = [];

            for (const toolCall of toolCalls) {
                try {
                    // Parse the tool name to find the server and tool
                    // Format is: serverName__toolName
                    const separatorIndex = toolCall.name.indexOf('__');
                    if (separatorIndex === -1) {
                        throw new Error(`Invalid tool name format: ${toolCall.name}. Expected format: serverName__toolName`);
                    }
                    
                    const serverName = toolCall.name.substring(0, separatorIndex);
                    const toolName = toolCall.name.substring(separatorIndex + 2);
                    
                    const server = mcpServers.get(serverName);
                    if (!server) {
                        throw new Error(`Server ${serverName} not found`);
                    }
                    
                    outputChannel.appendLine(`Calling MCP tool: ${toolName} on server ${serverName}`);
                    
                    // Calculate progress linearly based on iteration (10% initial + 90% spread across iterations)
                    // Progress increases monotonically - never goes backwards
                    if (currentProgress < 90) {
                        currentProgress = Math.min(90, 10 + (iteration * 6)); // Increment by ~6% per iteration, cap at 90%
                    }
                    
                    // Determine stage and message based on tool being called
                    let stage = 'processing';
                    let message = `Processing ${toolName}...`;
                    
                    if (toolName === 'get_jira_issue') {
                        stage = 'fetching_jira';
                        message = `Fetching Jira requirement details for ${jiraNumber}`;
                    } else if (toolName === 'analyze_oracle_standards' || toolName === 'get_latest_jira_tmp_prompt') {
                        stage = 'checking_standards';
                        message = 'Analyzing Oracle development standards and templates';
                    } else if (toolName === 'search_similar_jira_requirements') {
                        stage = 'searching_kb';
                        message = 'Searching for similar past work in knowledge base';
                    } else if (toolName.includes('analyze_db_code') || toolName.includes('get_committed_file') || toolName.includes('get_latest_component_version')) {
                        stage = 'analyzing_svn';
                        message = 'Analyzing existing SVN code patterns';
                    } else if (toolName === 'insert_jira_prompt' || toolName === 'update_jira_prompt') {
                        stage = 'generating_code';
                        message = 'Generating Oracle code from requirements';
                        currentProgress = 90; // Final stage before completion
                    } else if (toolName === 'update_issue_status' || toolName === 'add_or_update_jira_dashboard') {
                        stage = 'saving_results';
                        message = 'Updating Jira status and saving results';
                        currentProgress = 95;
                    }
                    
                    // Send progress update
                    await sendProgressUpdate({
                        jiraNumber,
                        stage,
                        status: 'in-progress',
                        message,
                        progress: currentProgress,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Call the MCP server directly
                    const toolRequest: MCPRequest = {
                        jsonrpc: '2.0',
                        id: mcpRequestId++,
                        method: 'tools/call',
                        params: {
                            name: toolName,
                            arguments: toolCall.input
                        }
                    };

                    const result = await callMCPTool(server, toolRequest);
                    
                    toolResults.push(new vscode.LanguageModelToolResultPart(
                        toolCall.callId, 
                        [new vscode.LanguageModelTextPart(result)]
                    ));
                    outputChannel.appendLine(`✓ Tool ${toolCall.name} executed successfully`);
                } catch (error: any) {
                    outputChannel.appendLine(`✗ Tool ${toolCall.name} failed: ${error.message}`);
                    toolResults.push(new vscode.LanguageModelToolResultPart(
                        toolCall.callId,
                        [new vscode.LanguageModelTextPart(`Error: ${error.message}`)]
                    ));
                }
            }

            // Add assistant message with tool calls (include intermediate text if any) and user message with results
            // The intermediate response text is just the model saying "I'll do X..." - include it for context
            const assistantParts: (vscode.LanguageModelToolCallPart | vscode.LanguageModelTextPart)[] = [...toolCalls];
            if (response.trim()) {
                assistantParts.push(new vscode.LanguageModelTextPart(response));
            }
            messages.push(vscode.LanguageModelChatMessage.Assistant(assistantParts));
            messages.push(vscode.LanguageModelChatMessage.User(toolResults));
            
            outputChannel.appendLine(`✓ Tool results added to conversation. Continuing to iteration ${iteration + 1} for final response...`);
            // Continue loop to get the final response after tool execution
        }

        // If we exit the loop without getting a final response, check if we hit max iterations
        if (!finalResponse && iteration >= maxIterations) {
            outputChannel.appendLine(`⚠️ Warning: Reached max iterations (${maxIterations}) without final response`);
            outputChannel.appendLine(`⚠️ This usually means the agent is still working on multiple tasks.`);
            outputChannel.appendLine(`⚠️ Consider increasing maxIterations if tasks consistently fail to complete.`);
            
            // Send error progress - task incomplete
            await sendProgressUpdate({
                jiraNumber,
                stage: 'error',
                status: 'error',
                message: `Max iterations (${maxIterations}) reached. Task may be incomplete. Check logs for details.`,
                progress: currentProgress,
                timestamp: new Date().toISOString()
            });
            
            finalResponse = `Task incomplete: Reached maximum iterations (${maxIterations}) while processing. ` +
                          `The agent was working through multiple steps but did not finish. ` +
                          `Last progress: ${currentProgress}%. Please check VS Code Output panel for details.`;
        } else if (!finalResponse) {
            outputChannel.appendLine(`⚠️ Warning: Exited loop without final response and without hitting max iterations!`);
            finalResponse = "I apologize, but I encountered an unexpected issue. Please try again.";
        }

        outputChannel.appendLine(`✓ Returning final response (${finalResponse.length} characters)`);
        
        // Only send completion progress if task actually completed (not hit max iterations)
        if (finalResponse && iteration < maxIterations) {
            await sendProgressUpdate({
                jiraNumber,
                stage: 'saving_results',
                status: 'completed',
                message: 'Analysis complete! Code ready for review',
                progress: 100,
                timestamp: new Date().toISOString()
            });
        }
        
        return finalResponse;

    } catch (error: any) {
        outputChannel.appendLine(`Error in sendToCopilotChat: ${error.message}`);
        
        // Send error progress
        await sendProgressUpdate({
            jiraNumber,
            stage: 'error',
            status: 'error',
            message: `Error: ${error.message}`,
            progress: 0,
            timestamp: new Date().toISOString()
        });
        
        throw error;
    }
}

function sendError(ws: WebSocket, errorMessage: string) {
    const errorResponse = {
        type: 'error',
        error: errorMessage,
        timestamp: new Date().toISOString()
    };
    ws.send(JSON.stringify(errorResponse));
}
