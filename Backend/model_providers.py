"""
AI Model Providers for DevMindAPI
Supports multiple AI models: OpenAI, Claude, Gemini, and VS Code Bridge
"""
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseModelProvider(ABC):
    """Base class for AI model providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model_name = "base"
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from the model"""
        pass
    
    def is_available(self) -> bool:
        """Check if the provider is properly configured"""
        return bool(self.api_key)


class OpenAIProvider(BaseModelProvider):
    """OpenAI GPT models"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.model_name = "OpenAI GPT"
        
    async def generate(self, prompt: str, model: str = "gpt-4", **kwargs) -> str:
        """Generate response using OpenAI API"""
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.api_key)
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 2000)
            
            logger.info(f"Calling OpenAI API with model: {model}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude models"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model_name = "Anthropic Claude"
    
    async def generate(self, prompt: str, model: str = "claude-3-opus-20240229", **kwargs) -> str:
        """Generate response using Claude API"""
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 2000)
            
            logger.info(f"Calling Claude API with model: {model}")
            
            message = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


class GeminiProvider(BaseModelProvider):
    """Google Gemini models"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY"))
        self.model_name = "Google Gemini"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(self, prompt: str, model: str = "gemini-pro", **kwargs) -> str:
        """Generate response using Gemini API"""
        if not self.is_available():
            raise ValueError("Google API key not configured")
        
        try:
            import aiohttp
            
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
            
            logger.info(f"Calling Gemini API with model: {model}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    params={"key": self.api_key},
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gemini API error: {error_text}")
                    
                    data = await response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                    
        except ImportError:
            raise ImportError("aiohttp package not installed. Run: pip install aiohttp")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class OllamaProvider(BaseModelProvider):
    """Ollama local models"""
    
    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = "Ollama Local"
    
    def is_available(self) -> bool:
        """Ollama doesn't need API key, just check if URL is set"""
        return bool(self.base_url)
    
    async def generate(self, prompt: str, model: str = "llama2", **kwargs) -> str:
        """Generate response using Ollama"""
        try:
            import aiohttp
            
            temperature = kwargs.get("temperature", 0.7)
            
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            logger.info(f"Calling Ollama API with model: {model}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {error_text}")
                    
                    data = await response.json()
                    return data["response"]
                    
        except ImportError:
            raise ImportError("aiohttp package not installed. Run: pip install aiohttp")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise


class ModelFactory:
    """Factory to create and manage model providers"""
    
    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
    }
    
    _instances = {}  # Cache provider instances
    
    @classmethod
    def create_provider(cls, provider_name: str) -> BaseModelProvider:
        """Create or get cached provider instance"""
        provider_name = provider_name.lower()
        
        # Return cached instance if available
        if provider_name in cls._instances:
            return cls._instances[provider_name]
        
        # Create new instance
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available: {', '.join(cls._providers.keys())}"
            )
        
        instance = provider_class()
        cls._instances[provider_name] = instance
        return instance
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """Get list of providers and their availability status"""
        status = {}
        for name in cls._providers.keys():
            try:
                provider = cls.create_provider(name)
                status[name] = provider.is_available()
            except Exception as e:
                logger.warning(f"Error checking {name}: {e}")
                status[name] = False
        return status
    
    @classmethod
    def clear_cache(cls):
        """Clear cached provider instances"""
        cls._instances.clear()


# Model routing configuration
MODEL_ROUTING = {
    # OpenAI models
    "openai-gpt4": ("openai", "gpt-4"),
    "openai-gpt4-turbo": ("openai", "gpt-4-turbo-preview"),
    "openai-gpt3.5": ("openai", "gpt-3.5-turbo"),
    
    # Claude models
    "claude-opus": ("claude", "claude-3-opus-20240229"),
    "claude-sonnet": ("claude", "claude-3-sonnet-20240229"),
    "claude-haiku": ("claude", "claude-3-haiku-20240307"),
    
    # Gemini models
    "gemini-pro": ("gemini", "gemini-pro"),
    "gemini-pro-vision": ("gemini", "gemini-pro-vision"),
    
    # Ollama local models
    "ollama-llama2": ("ollama", "llama2"),
    "ollama-mistral": ("ollama", "mistral"),
    "ollama-codellama": ("ollama", "codellama"),
}


async def test_provider(provider_name: str, model_key: str = None):
    """Test a specific provider"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name.upper()}")
    print(f"{'='*60}")
    
    try:
        if model_key:
            provider_name, model_name = MODEL_ROUTING[model_key]
        else:
            model_name = None
        
        provider = ModelFactory.create_provider(provider_name)
        
        if not provider.is_available():
            print(f"❌ {provider_name} is not available (missing API key or configuration)")
            return False
        
        print(f"✓ {provider_name} is configured")
        
        # Test with a simple prompt
        prompt = "Say 'Hello from AI' in one sentence."
        print(f"Sending test prompt: {prompt}")
        
        response = await provider.generate(prompt, model=model_name) if model_name else await provider.generate(prompt)
        print(f"✓ Response received: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_all_providers():
    """Test all available providers"""
    print("\n" + "="*60)
    print("TESTING ALL MODEL PROVIDERS")
    print("="*60)
    
    status = ModelFactory.get_available_providers()
    
    for provider, is_available in status.items():
        status_icon = "✓" if is_available else "❌"
        print(f"{status_icon} {provider.upper()}: {'Available' if is_available else 'Not configured'}")
    
    print("\n" + "="*60)
    print("DETAILED TESTS")
    print("="*60)
    
    # Test each available provider
    for provider_name, is_available in status.items():
        if is_available:
            await test_provider(provider_name)


if __name__ == "__main__":
    # Test script
    asyncio.run(test_all_providers())
