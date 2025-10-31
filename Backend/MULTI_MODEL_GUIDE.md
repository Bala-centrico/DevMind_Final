# Multi-Model Support Guide for DevMindAPI

## Overview
This guide explains how to extend the Copilot Bridge to support multiple AI models including OpenAI, Claude, Gemini, and others.

## Architecture Options

### Option 1: Extend VS Code Language Model API (Easiest)
Use VS Code's built-in `vscode.lm` API which supports multiple model providers.

### Option 2: Direct API Integration (Most Flexible)
Integrate multiple AI provider APIs directly in the FastAPI backend.

### Option 3: Hybrid Approach (Recommended)
Combine both approaches - use VS Code LM API when available, fall back to direct APIs.

---

## Implementation: Option 1 - VS Code Language Model API

### Benefits
- ✅ No API keys needed in many cases
- ✅ Uses user's existing subscriptions (Copilot, etc.)
- ✅ Integrated with VS Code permissions
- ✅ Automatic model updates

### Step-by-Step Implementation

#### 1. Update FastAPI Request Model

```python
# main.py
from enum import Enum

class ModelProvider(str, Enum):
    COPILOT_GPT4 = "copilot-gpt4"
    COPILOT_GPT35 = "copilot-gpt3.5"
    CLAUDE = "claude"
    GEMINI = "gemini"
    AUTO = "auto"  # Let VS Code pick best available

class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    timeout: Optional[int] = Field(default=60)
    model: Optional[ModelProvider] = Field(
        default=ModelProvider.AUTO,
        description="AI model to use"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=2000,
        description="Maximum tokens in response"
    )
```

#### 2. Update WebSocket Message Format

```python
# In VSCodeBridgeManager.send_prompt()
message = {
    "type": "copilot_request",
    "requestId": request_id,
    "prompt": prompt,
    "model": model_config.get("provider", "auto"),
    "temperature": model_config.get("temperature", 0.7),
    "maxTokens": model_config.get("max_tokens", 2000),
    "timestamp": request_id
}
```

#### 3. Update VS Code Extension to Handle Model Selection

```typescript
// extension.ts

interface ModelConfig {
    provider: string;
    temperature: number;
    maxTokens: number;
}

interface CopilotRequest {
    type: string;
    requestId: string;
    prompt: string;
    model?: string;
    temperature?: number;
    maxTokens?: number;
    timestamp: string;
}

async function handleCopilotRequest(ws: WebSocket, message: CopilotRequest) {
    const prompt = message.prompt;
    const requestId = message.requestId;
    const modelConfig: ModelConfig = {
        provider: message.model || 'auto',
        temperature: message.temperature || 0.7,
        maxTokens: message.maxTokens || 2000
    };

    outputChannel.appendLine(`Processing request with model: ${modelConfig.provider}`);

    try {
        const response = await sendToCopilotChat(prompt, modelConfig);
        
        const responseMessage = {
            type: 'copilot_response',
            requestId: requestId,
            response: response,
            model: modelConfig.provider,
            timestamp: new Date().toISOString()
        };

        ws.send(JSON.stringify(responseMessage));
        outputChannel.appendLine(`✓ Response sent using ${modelConfig.provider}`);
    } catch (error: any) {
        outputChannel.appendLine(`Error: ${error.message}`);
        sendError(ws, error.message);
    }
}

async function sendToCopilotChat(prompt: string, config: ModelConfig): Promise<string> {
    outputChannel.appendLine(`Selecting model: ${config.provider}`);

    try {
        let models: vscode.LanguageModelChat[];

        // Select model based on provider
        switch (config.provider) {
            case 'copilot-gpt4':
                models = await vscode.lm.selectChatModels({
                    vendor: 'copilot',
                    family: 'gpt-4'
                });
                break;

            case 'copilot-gpt3.5':
                models = await vscode.lm.selectChatModels({
                    vendor: 'copilot',
                    family: 'gpt-3.5-turbo'
                });
                break;

            case 'claude':
                // Claude via Copilot or direct extension
                models = await vscode.lm.selectChatModels({
                    vendor: 'anthropic'
                });
                if (models.length === 0) {
                    models = await vscode.lm.selectChatModels({
                        family: 'claude'
                    });
                }
                break;

            case 'gemini':
                models = await vscode.lm.selectChatModels({
                    vendor: 'google',
                    family: 'gemini'
                });
                break;

            case 'auto':
            default:
                // Get all available models and use the best one
                models = await vscode.lm.selectChatModels();
                outputChannel.appendLine(`Found ${models.length} available models`);
                break;
        }

        if (models.length === 0) {
            throw new Error(`No models available for provider: ${config.provider}`);
        }

        const selectedModel = models[0];
        outputChannel.appendLine(`Using model: ${selectedModel.name} (${selectedModel.vendor}/${selectedModel.family})`);
        
        return await getChatResponse(selectedModel, prompt, config);

    } catch (error: any) {
        outputChannel.appendLine(`Error selecting model: ${error.message}`);
        throw error;
    }
}

async function getChatResponse(
    model: vscode.LanguageModelChat, 
    prompt: string,
    config: ModelConfig
): Promise<string> {
    const messages = [
        vscode.LanguageModelChatMessage.User(prompt)
    ];

    // Configure request options
    const options: vscode.LanguageModelChatRequestOptions = {
        justification: 'DevMindAPI Bridge Request'
    };

    const chatRequest = await model.sendRequest(
        messages, 
        options,
        new vscode.CancellationTokenSource().token
    );
    
    let response = '';
    for await (const fragment of chatRequest.text) {
        response += fragment;
    }

    outputChannel.appendLine(`Received response (${response.length} chars) from ${model.name}`);
    return response;
}
```

---

## Implementation: Option 2 - Direct API Integration

### Benefits
- ✅ Full control over API parameters
- ✅ No VS Code dependency for API calls
- ✅ Support for any AI provider
- ✅ Can use different API keys per model

### Step-by-Step Implementation

#### 1. Create Model Providers Module

```python
# model_providers.py
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import aiohttp
from openai import AsyncOpenAI
import anthropic

class BaseModelProvider(ABC):
    """Base class for AI model providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from the model"""
        pass

class OpenAIProvider(BaseModelProvider):
    """OpenAI GPT models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate(self, prompt: str, model: str = "gpt-4", **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content

class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    async def generate(self, prompt: str, model: str = "claude-3-opus-20240229", **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        message = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text

class GeminiProvider(BaseModelProvider):
    """Google Gemini models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(self, prompt: str, model: str = "gemini-pro", **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params={"key": self.api_key},
                json=payload
            ) as response:
                data = await response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

class ModelFactory:
    """Factory to create model providers"""
    
    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str) -> BaseModelProvider:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class()
    
    @classmethod
    def get_available_providers(cls) -> list:
        return list(cls._providers.keys())
```

#### 2. Update Main API

```python
# main.py (additions)
from model_providers import ModelFactory

class ModelProvider(str, Enum):
    VSCODE_BRIDGE = "vscode-bridge"  # Use VS Code extension
    OPENAI_GPT4 = "openai-gpt4"
    OPENAI_GPT35 = "openai-gpt3.5"
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_SONNET = "claude-sonnet"
    GEMINI_PRO = "gemini-pro"

# Model routing
MODEL_ROUTING = {
    ModelProvider.OPENAI_GPT4: ("openai", "gpt-4"),
    ModelProvider.OPENAI_GPT35: ("openai", "gpt-3.5-turbo"),
    ModelProvider.CLAUDE_OPUS: ("claude", "claude-3-opus-20240229"),
    ModelProvider.CLAUDE_SONNET: ("claude", "claude-3-sonnet-20240229"),
    ModelProvider.GEMINI_PRO: ("gemini", "gemini-pro"),
}

@app.post("/api/v1/copilot/chat", response_model=CopilotResponse)
async def getCopilotResponseWithVSCodeBridge(request: PromptRequest):
    """Send prompt to selected AI model"""
    
    try:
        logger.info(f"Request: model={request.model}, prompt={request.prompt[:50]}...")
        
        # Route to appropriate provider
        if request.model == ModelProvider.VSCODE_BRIDGE:
            # Use VS Code extension bridge
            response = await bridge_manager.send_prompt(
                prompt=request.prompt,
                timeout=request.timeout
            )
            response_text = response.get("response", "")
        
        else:
            # Use direct API integration
            provider_name, model_name = MODEL_ROUTING.get(request.model)
            provider = ModelFactory.create_provider(provider_name)
            
            response_text = await provider.generate(
                prompt=request.prompt,
                model=model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        return CopilotResponse(
            success=True,
            response=response_text,
            prompt=request.prompt,
            timestamp=datetime.now().isoformat(),
            model=request.model,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return CopilotResponse(
            success=False,
            response="",
            prompt=request.prompt,
            timestamp=datetime.now().isoformat(),
            model=request.model,
            error=str(e)
        )
```

#### 3. Environment Configuration

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-claude-key
GOOGLE_API_KEY=your-google-api-key
```

#### 4. Update Requirements

```txt
# requirements.txt additions
openai>=1.0.0
anthropic>=0.18.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

---

## Implementation: Option 3 - Hybrid Approach (Recommended)

### Configuration File

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # VS Code Bridge
    vscode_bridge_enabled: bool = True
    vscode_bridge_host: str = "localhost"
    vscode_bridge_port: int = 8765
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    
    # Model preferences
    default_model: str = "vscode-bridge"
    fallback_model: str = "openai-gpt4"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Testing Different Models

### Example API Calls

```bash
# Test with VS Code Copilot
curl -X POST "http://localhost:8000/api/v1/copilot/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain async/await in Python",
    "model": "vscode-bridge"
  }'

# Test with OpenAI GPT-4
curl -X POST "http://localhost:8000/api/v1/copilot/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain async/await in Python",
    "model": "openai-gpt4",
    "temperature": 0.7,
    "max_tokens": 1000
  }'

# Test with Claude
curl -X POST "http://localhost:8000/api/v1/copilot/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain async/await in Python",
    "model": "claude-opus"
  }'
```

### Python Test Script

```python
# test_models.py
import asyncio
import aiohttp

async def test_model(model: str, prompt: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/copilot/chat",
            json={"prompt": prompt, "model": model}
        ) as response:
            data = await response.json()
            print(f"\n{'='*60}")
            print(f"Model: {model}")
            print(f"Success: {data['success']}")
            print(f"Response: {data['response'][:200]}...")
            print(f"{'='*60}\n")

async def main():
    prompt = "Write a Python function to calculate fibonacci numbers"
    
    models = [
        "vscode-bridge",
        "openai-gpt4",
        "claude-opus",
        "gemini-pro"
    ]
    
    for model in models:
        try:
            await test_model(model, prompt)
        except Exception as e:
            print(f"Error testing {model}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Model Comparison Dashboard

### Add Dashboard Endpoint

```python
# main.py addition
@app.get("/api/v1/models", tags=["Models"])
async def list_available_models():
    """List all available AI models and their status"""
    
    models_status = []
    
    # Check VS Code bridge
    models_status.append({
        "name": "VS Code Copilot",
        "provider": "vscode-bridge",
        "available": bridge_manager.is_connected,
        "cost": "subscription",
        "latency": "low"
    })
    
    # Check API-based models
    for model_key, (provider, model_name) in MODEL_ROUTING.items():
        api_key_available = False
        if provider == "openai":
            api_key_available = bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "claude":
            api_key_available = bool(os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "gemini":
            api_key_available = bool(os.getenv("GOOGLE_API_KEY"))
        
        models_status.append({
            "name": model_name,
            "provider": provider,
            "available": api_key_available,
            "cost": "pay-per-use",
            "latency": "medium"
        })
    
    return {
        "total_models": len(models_status),
        "available_models": sum(1 for m in models_status if m["available"]),
        "models": models_status
    }
```

---

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install openai anthropic aiohttp python-dotenv
```

### 2. Configure API Keys
Create `.env` file:
```env
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

### 3. Start API
```bash
python main.py
```

### 4. Test Models
```bash
# Test available models
curl http://localhost:8000/api/v1/models

# Use specific model
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "model": "openai-gpt4"}'
```

---

## Troubleshooting

### Model Not Available
- Check API keys in `.env`
- Verify VS Code extension is running for bridge models
- Check `/api/v1/models` endpoint for status

### Performance Issues
- Use streaming responses for large outputs
- Implement caching for common queries
- Add rate limiting per model

### Cost Management
- Set default limits on `max_tokens`
- Implement usage tracking per model
- Add cost estimation before requests

---

## Next Steps

1. **Add Streaming Support**: Implement Server-Sent Events for real-time responses
2. **Model Comparison**: Add A/B testing between models
3. **Context Management**: Add conversation history support
4. **Fine-tuning**: Support custom fine-tuned models
5. **Monitoring**: Add Prometheus metrics for model performance

---

## Summary

The hybrid approach gives you the best of both worlds:
- Use VS Code's integrated models when available (free with Copilot subscription)
- Fall back to direct API integration for specific needs
- Easy to add new model providers
- Flexible configuration per request

Choose based on your needs:
- **Option 1**: Simplest, uses VS Code extensions
- **Option 2**: Most flexible, requires API keys
- **Option 3**: Best balance, combines both approaches
