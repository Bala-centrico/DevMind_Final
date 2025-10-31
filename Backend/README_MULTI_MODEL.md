# DevMindAPI Multi-Model Support 🤖

Connect the VS Code Copilot Bridge with multiple AI models including OpenAI GPT-4, Claude, Gemini, and local Ollama models.

## 🌟 Features

- **Multiple AI Providers**: OpenAI, Anthropic Claude, Google Gemini, Ollama (local)
- **VS Code Integration**: Use GitHub Copilot via VS Code extension bridge
- **Flexible Architecture**: Easy to add new model providers
- **Unified API**: Single endpoint for all models
- **Model Discovery**: Automatic detection of available models
- **Cost Optimization**: Mix free (Copilot), paid (APIs), and local (Ollama) models

## 📋 Supported Models

### VS Code Bridge (Requires Copilot Subscription)
- ✅ **vscode-bridge** - GitHub Copilot via VS Code extension

### OpenAI Models (Requires API Key)
- ✅ **openai-gpt4** - Most capable, best for complex tasks
- ✅ **openai-gpt4-turbo** - Faster GPT-4 variant
- ✅ **openai-gpt3.5** - Fast and cost-effective

### Anthropic Claude Models (Requires API Key)
- ✅ **claude-opus** - Most capable Claude model
- ✅ **claude-sonnet** - Balanced performance/cost
- ✅ **claude-haiku** - Fastest, most affordable

### Google Gemini Models (Requires API Key)
- ✅ **gemini-pro** - Google's multimodal model

### Ollama Local Models (Free, Runs Locally)
- ✅ **ollama-llama2** - Meta's Llama 2
- ✅ **ollama-mistral** - Mistral AI model
- ✅ **ollama-codellama** - Specialized for coding

## 🚀 Quick Start

### 1. Setup

```powershell
# Run setup script
.\setup_multi_model.ps1

# Or manually:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements_multi_model.txt
```

### 2. Configure API Keys

Edit `.env` file:

```env
# OpenAI (https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here

# Anthropic Claude (https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Google Gemini (https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your-key-here

# Ollama (local, no key needed - install from https://ollama.ai/)
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Start Server

```powershell
.\start_multi_model.ps1
```

Or:

```powershell
python main_multi_model.py
```

Server will start at: http://localhost:8000

### 4. Test

```powershell
# Quick test
python test_multi_model.py --quick

# Interactive testing
python test_multi_model.py
```

## 📖 API Usage

### Check Available Models

```bash
curl http://localhost:8000/api/v1/models
```

Response:
```json
{
  "total_models": 11,
  "available_count": 5,
  "models": [
    {
      "name": "VS Code Copilot",
      "key": "vscode-bridge",
      "available": true,
      "cost_type": "subscription"
    },
    {
      "name": "gpt-4",
      "key": "openai-gpt4",
      "available": true,
      "cost_type": "pay-per-use"
    }
  ]
}
```

### Send Chat Request

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain async/await in Python",
    "model": "openai-gpt4",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

Response:
```json
{
  "success": true,
  "response": "Async/await in Python...",
  "prompt": "Explain async/await in Python",
  "model": "openai-gpt4",
  "provider": "OPENAI - gpt-4",
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Python Example

```python
import requests

# Test with different models
models_to_test = [
    "vscode-bridge",
    "openai-gpt4",
    "claude-opus",
    "gemini-pro"
]

prompt = "Write a Python function to calculate fibonacci"

for model in models_to_test:
    response = requests.post(
        "http://localhost:8000/api/v1/ai/chat",
        json={
            "prompt": prompt,
            "model": model,
            "temperature": 0.7
        }
    )
    
    data = response.json()
    if data['success']:
        print(f"\n{model}:")
        print(data['response'][:200])
```

## 🔧 Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────────────────┐
│               DevMindAPI (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Request Router & Handler                    │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │                                                │
│  ┌──────────▼──────────┐  ┌──────────────────────────────┐ │
│  │ VS Code Bridge Mgr  │  │   Model Factory              │ │
│  └──────────┬──────────┘  └──────────┬───────────────────┘ │
└─────────────┼──────────────────────────┼───────────────────┘
              │                          │
              │ WebSocket                │ Direct API
              │                          │
┌─────────────▼──────────┐  ┌───────────▼──────────────────┐
│  VS Code Extension     │  │   AI Provider APIs           │
│  ┌──────────────────┐  │  │  ┌────────────────────────┐  │
│  │ Language Model   │  │  │  │  OpenAI API            │  │
│  │ API (vscode.lm)  │  │  │  │  Anthropic API         │  │
│  └──────────────────┘  │  │  │  Google Gemini API     │  │
└────────────────────────┘  │  │  Ollama (Local)        │  │
                            │  └────────────────────────┘  │
                            └─────────────────────────────┘
```

### File Structure

```
DevMindAPI/
├── main_multi_model.py          # Enhanced FastAPI server
├── model_providers.py            # AI provider implementations
├── .env                          # API keys (create from .env.example)
├── .env.example                  # Template for configuration
├── requirements_multi_model.txt  # Dependencies
├── setup_multi_model.ps1         # Setup script
├── start_multi_model.ps1         # Start script
├── test_multi_model.py           # Testing utilities
├── MULTI_MODEL_GUIDE.md          # Detailed guide
└── vscode-copilot-bridge/        # VS Code extension
    ├── src/extension.ts          # Extension code
    └── package.json              # Extension config
```

## 🎯 Use Cases

### 1. Cost Optimization

Use free Copilot for development, GPT-4 for production:

```python
# Development
response = chat("Debug this code", model="vscode-bridge")

# Production with fallback
try:
    response = chat("Analyze data", model="openai-gpt4")
except:
    response = chat("Analyze data", model="vscode-bridge")
```

### 2. Model Comparison

Test different models for the same task:

```python
prompt = "Explain quantum computing"
models = ["openai-gpt4", "claude-opus", "gemini-pro"]

responses = {}
for model in models:
    responses[model] = chat(prompt, model=model)

# Compare responses
```

### 3. Local Development

Use Ollama for offline/privacy-sensitive work:

```python
# No internet required, no API costs
response = chat(
    "Review this code for security issues",
    model="ollama-codellama"
)
```

### 4. Specialized Tasks

Route to best model for the task:

```python
def smart_route(task_type, prompt):
    routing = {
        "code": "ollama-codellama",
        "analysis": "claude-opus",
        "creative": "openai-gpt4",
        "quick": "openai-gpt3.5"
    }
    model = routing.get(task_type, "vscode-bridge")
    return chat(prompt, model=model)
```

## 🔐 Security Best Practices

1. **Never commit .env file**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use environment variables**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. **Rotate API keys regularly**

4. **Monitor API usage and costs**

5. **Implement rate limiting**

## 📊 Monitoring & Logging

The API logs all requests:

```python
# Check logs
tail -f logs/api.log

# Or in PowerShell
Get-Content logs/api.log -Wait
```

Log format:
```
2024-01-01 12:00:00 - INFO - Request: model=openai-gpt4, prompt=...
2024-01-01 12:00:01 - INFO - Using OPENAI with model gpt-4
2024-01-01 12:00:03 - INFO - Response received (523 chars)
```

## 🐛 Troubleshooting

### Model Not Available

**Problem**: `{"error": "Model not available"}`

**Solutions**:
1. Check API key in `.env`
2. Verify key is valid
3. Check `/api/v1/models` for status

### VS Code Bridge Not Connected

**Problem**: `{"error": "VS Code bridge not available"}`

**Solutions**:
1. Ensure VS Code extension is running
2. Check extension is installed: `F1` → "Copilot Bridge Status"
3. Restart VS Code
4. Check port 8765 is not blocked

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'openai'`

**Solution**:
```powershell
pip install -r requirements_multi_model.txt
```

### Ollama Not Working

**Problem**: Cannot connect to Ollama

**Solutions**:
1. Install Ollama: https://ollama.ai/
2. Start Ollama service
3. Pull models: `ollama pull llama2`
4. Check `OLLAMA_BASE_URL` in `.env`

## 📈 Performance Tips

1. **Cache responses** for repeated prompts
2. **Use streaming** for long responses
3. **Implement retry logic** with exponential backoff
4. **Monitor latency** per model
5. **Set appropriate timeouts**

## 🔄 Adding New Models

### Example: Adding Cohere

1. **Install SDK**:
   ```bash
   pip install cohere
   ```

2. **Create Provider**:
   ```python
   # In model_providers.py
   class CohereProvider(BaseModelProvider):
       def __init__(self, api_key=None):
           super().__init__(api_key or os.getenv("COHERE_API_KEY"))
       
       async def generate(self, prompt: str, **kwargs):
           import cohere
           co = cohere.Client(self.api_key)
           response = co.generate(prompt=prompt)
           return response.generations[0].text
   ```

3. **Register Provider**:
   ```python
   ModelFactory._providers["cohere"] = CohereProvider
   ```

4. **Add Routing**:
   ```python
   MODEL_ROUTING["cohere-command"] = ("cohere", "command")
   ```

## 📚 Resources

- **OpenAI**: https://platform.openai.com/docs
- **Claude**: https://docs.anthropic.com/
- **Gemini**: https://ai.google.dev/docs
- **Ollama**: https://ollama.ai/docs
- **VS Code LM API**: https://code.visualstudio.com/api/extension-guides/language-model

## 🤝 Contributing

Contributions welcome! To add a new model provider:

1. Implement `BaseModelProvider` interface
2. Add to `ModelFactory._providers`
3. Update `MODEL_ROUTING`
4. Add tests in `test_multi_model.py`
5. Update documentation

## 📝 License

This project is part of DevMindAPI. See main README for license information.

## ✨ Credits

Built with:
- FastAPI
- VS Code Extension API
- OpenAI API
- Anthropic API
- Google Generative AI
- Ollama

---

**Need Help?** Check the detailed guide: [MULTI_MODEL_GUIDE.md](MULTI_MODEL_GUIDE.md)
