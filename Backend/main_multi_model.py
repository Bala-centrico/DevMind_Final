"""
DevMindAPI - Enhanced version with multiple AI model support
Supports: VS Code Copilot, OpenAI, Claude, Gemini, Ollama
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import os

# Import model providers
from model_providers import ModelFactory, MODEL_ROUTING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevMindAPI - Multi-Model",
    description="API to interact with multiple AI models (Copilot, OpenAI, Claude, Gemini, Ollama)",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket configuration for VS Code extension bridge
WS_HOST = "localhost"
WS_PORT = 8765
REQUEST_TIMEOUT = 60  # seconds


class ModelProvider(str, Enum):
    """Available AI model providers"""
    VSCODE_BRIDGE = "vscode-bridge"  # Use VS Code Copilot via extension
    OPENAI_GPT4 = "openai-gpt4"
    OPENAI_GPT4_TURBO = "openai-gpt4-turbo"
    OPENAI_GPT35 = "openai-gpt3.5"
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    GEMINI_PRO = "gemini-pro"
    OLLAMA_LLAMA2 = "ollama-llama2"
    OLLAMA_MISTRAL = "ollama-mistral"
    OLLAMA_CODELLAMA = "ollama-codellama"


class PromptRequest(BaseModel):
    """Request model for AI chat prompt"""
    prompt: str = Field(..., min_length=1, description="The prompt to send to the AI model")
    model: ModelProvider = Field(
        default=ModelProvider.VSCODE_BRIDGE,
        description="AI model to use"
    )
    timeout: Optional[int] = Field(default=60, description="Timeout in seconds")
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)"
    )
    max_tokens: Optional[int] = Field(
        default=2000,
        ge=1,
        le=4000,
        description="Maximum tokens in response"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty or whitespace only')
        return v.strip()


class AIResponse(BaseModel):
    """Response model from AI"""
    success: bool
    response: str
    prompt: str
    model: str
    provider: str
    timestamp: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    bridge_connected: bool
    available_models: Dict[str, bool]
    timestamp: str


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    provider: str
    available: bool
    cost_type: str
    description: str


# Global WebSocket connection manager for VS Code bridge
class VSCodeBridgeManager:
    def __init__(self):
        self.ws_client = None
        self.is_connected = False
        
    async def connect(self):
        """Connect to VS Code extension WebSocket server"""
        try:
            self.ws_client = await websockets.connect(f"ws://{WS_HOST}:{WS_PORT}")
            self.is_connected = True
            logger.info(f"Connected to VS Code bridge at ws://{WS_HOST}:{WS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to VS Code bridge: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from VS Code extension"""
        if self.ws_client:
            await self.ws_client.close()
            self.is_connected = False
            logger.info("Disconnected from VS Code bridge")
    
    async def send_prompt(self, prompt: str, timeout: int = 60, **kwargs) -> dict:
        """Send prompt to Copilot via VS Code extension"""
        if not self.is_connected:
            connected = await self.connect()
            if not connected:
                raise HTTPException(
                    status_code=503,
                    detail="VS Code Copilot bridge is not available. Please ensure the VS Code extension is running."
                )
        
        try:
            request_id = datetime.now().isoformat()
            message = {
                "type": "copilot_request",
                "requestId": request_id,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "maxTokens": kwargs.get("max_tokens", 2000),
                "timestamp": request_id
            }
            
            await self.ws_client.send(json.dumps(message))
            logger.info(f"Sent prompt to VS Code bridge")
            
            try:
                response_raw = await asyncio.wait_for(
                    self.ws_client.recv(),
                    timeout=timeout
                )
                response = json.loads(response_raw)
                return response
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail=f"Timeout waiting for response after {timeout} seconds"
                )
                
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
            raise HTTPException(
                status_code=503,
                detail="Connection to VS Code bridge was closed"
            )
        except Exception as e:
            logger.error(f"Error communicating with VS Code bridge: {e}")
            raise


# Initialize managers
bridge_manager = VSCodeBridgeManager()


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("DevMindAPI Multi-Model starting up...")
    
    # Try to connect to VS Code bridge (non-blocking)
    try:
        await bridge_manager.connect()
    except Exception as e:
        logger.warning(f"Could not connect to VS Code bridge on startup: {e}")
    
    # Check available model providers
    available = ModelFactory.get_available_providers()
    logger.info(f"Available providers: {available}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("DevMindAPI shutting down...")
    await bridge_manager.disconnect()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "DevMindAPI - Multi-Model AI Bridge",
        "version": "2.0.0",
        "supported_models": [model.value for model in ModelProvider],
        "endpoints": {
            "chat": "/api/v1/ai/chat",
            "models": "/api/v1/models",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    available_models = ModelFactory.get_available_providers()
    
    return HealthResponse(
        status="healthy",
        bridge_connected=bridge_manager.is_connected,
        available_models=available_models,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/models", tags=["Models"])
async def list_models():
    """List all available AI models and their status"""
    
    available_providers = ModelFactory.get_available_providers()
    
    models_info = []
    
    # VS Code Bridge
    models_info.append({
        "name": "VS Code Copilot",
        "key": "vscode-bridge",
        "provider": "GitHub Copilot",
        "available": bridge_manager.is_connected,
        "cost_type": "subscription",
        "description": "GitHub Copilot via VS Code extension"
    })
    
    # API-based models
    model_descriptions = {
        "openai-gpt4": "Most capable OpenAI model, best for complex tasks",
        "openai-gpt4-turbo": "Faster GPT-4 variant with better performance",
        "openai-gpt3.5": "Fast and cost-effective OpenAI model",
        "claude-opus": "Most capable Claude model, excellent for analysis",
        "claude-sonnet": "Balanced Claude model, good for most tasks",
        "claude-haiku": "Fastest Claude model, good for simple tasks",
        "gemini-pro": "Google's multimodal model",
        "ollama-llama2": "Local Llama 2 model via Ollama",
        "ollama-mistral": "Local Mistral model via Ollama",
        "ollama-codellama": "Local Code Llama model via Ollama"
    }
    
    for model_key, (provider, model_name) in MODEL_ROUTING.items():
        is_available = available_providers.get(provider, False)
        
        models_info.append({
            "name": model_name,
            "key": model_key,
            "provider": provider.upper(),
            "available": is_available,
            "cost_type": "pay-per-use" if provider != "ollama" else "local-free",
            "description": model_descriptions.get(model_key, f"{provider.upper()} model")
        })
    
    return {
        "total_models": len(models_info),
        "available_count": sum(1 for m in models_info if m["available"]),
        "models": models_info
    }


@app.post("/api/v1/ai/chat", response_model=AIResponse, tags=["AI Chat"])
async def chat_with_ai(request: PromptRequest):
    """
    Send a prompt to selected AI model and get the response
    
    - **prompt**: The prompt/question to send (required, non-empty)
    - **model**: AI model to use (default: vscode-bridge)
    - **timeout**: Maximum time to wait for response in seconds (default: 60)
    - **temperature**: Sampling temperature 0.0-2.0 (default: 0.7)
    - **max_tokens**: Maximum tokens in response (default: 2000)
    """
    try:
        logger.info(f"Request: model={request.model}, prompt={request.prompt[:50]}...")
        
        response_text = ""
        provider_name = ""
        
        # Route to appropriate provider
        if request.model == ModelProvider.VSCODE_BRIDGE:
            # Use VS Code extension bridge
            logger.info("Using VS Code Copilot bridge")
            response = await bridge_manager.send_prompt(
                prompt=request.prompt,
                timeout=request.timeout,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if response.get("type") == "copilot_response":
                response_text = response.get("response", "")
                provider_name = "VS Code Copilot"
            elif response.get("type") == "error":
                raise HTTPException(
                    status_code=500,
                    detail=response.get("error", "Unknown error from VS Code bridge")
                )
        
        else:
            # Use direct API integration
            if request.model.value not in MODEL_ROUTING:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown model: {request.model}"
                )
            
            provider_key, model_name = MODEL_ROUTING[request.model.value]
            logger.info(f"Using {provider_key} with model {model_name}")
            
            provider = ModelFactory.create_provider(provider_key)
            
            if not provider.is_available():
                raise HTTPException(
                    status_code=503,
                    detail=f"{provider_key.upper()} is not configured. Please set up API key."
                )
            
            response_text = await provider.generate(
                prompt=request.prompt,
                model=model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            provider_name = f"{provider_key.upper()} - {model_name}"
        
        return AIResponse(
            success=True,
            response=response_text,
            prompt=request.prompt,
            model=request.model.value,
            provider=provider_name,
            timestamp=datetime.now().isoformat(),
            error=None,
            metadata={
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return AIResponse(
            success=False,
            response="",
            prompt=request.prompt,
            model=request.model.value,
            provider="error",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    uvicorn.run(
        "main_multi_model:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
