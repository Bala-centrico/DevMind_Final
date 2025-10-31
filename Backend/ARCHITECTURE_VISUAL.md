# DevMindAPI Multi-Model Architecture - Visual Guide

## 🎯 Overview Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                              │
│  (Web App, CLI Tool, IDE Extension, Automation Script, etc.)        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ HTTP REST API
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                  DevMindAPI Multi-Model Server                       │
│                      (FastAPI Application)                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Unified Chat Endpoint                          │    │
│  │         POST /api/v1/ai/chat                                │    │
│  │         { "prompt": "...", "model": "..." }                 │    │
│  └────────────────┬───────────────────────────────────────────┘    │
│                   │                                                 │
│  ┌────────────────▼───────────────────────────────────────────┐    │
│  │                  Request Router                             │    │
│  │   (Determines which provider to use based on model)         │    │
│  └────┬──────────────────────────────────────┬─────────────────┘   │
│       │                                      │                      │
│  ┌────▼──────────────────┐    ┌─────────────▼──────────────────┐  │
│  │  VS Code Bridge Mgr   │    │     Model Factory              │  │
│  │  (WebSocket Client)   │    │  (Creates AI Providers)        │  │
│  └────┬──────────────────┘    └─────────────┬──────────────────┘  │
└───────┼───────────────────────────────────────┼─────────────────────┘
        │                                      │
        │ WebSocket                            │ Direct HTTP/API
        │ (Port 8765)                          │
        │                                      │
┌───────▼──────────────────┐    ┌──────────────▼──────────────────────┐
│  VS Code Extension       │    │      AI Provider APIs                │
│  (Copilot Bridge)        │    │                                      │
│                          │    │  ┌────────────────────────────────┐ │
│  ┌────────────────────┐  │    │  │   OpenAI API                   │ │
│  │  WebSocket Server  │  │    │  │   api.openai.com               │ │
│  │  (Port 8765)       │  │    │  │   Models: GPT-4, GPT-3.5       │ │
│  └────────┬───────────┘  │    │  └────────────────────────────────┘ │
│           │              │    │                                      │
│  ┌────────▼───────────┐  │    │  ┌────────────────────────────────┐ │
│  │  VS Code LM API    │  │    │  │   Anthropic API                │ │
│  │  (vscode.lm)       │  │    │  │   api.anthropic.com            │ │
│  │                    │  │    │  │   Models: Claude Opus/Sonnet   │ │
│  └────────┬───────────┘  │    │  └────────────────────────────────┘ │
│           │              │    │                                      │
│  ┌────────▼───────────┐  │    │  ┌────────────────────────────────┐ │
│  │  GitHub Copilot    │  │    │  │   Google Gemini API            │ │
│  │  (Subscription)    │  │    │  │   generativelanguage.google... │ │
│  └────────────────────┘  │    │  │   Models: Gemini Pro           │ │
└──────────────────────────┘    │  └────────────────────────────────┘ │
                                │                                      │
                                │  ┌────────────────────────────────┐ │
                                │  │   Ollama (Local)               │ │
                                │  │   localhost:11434              │ │
                                │  │   Models: Llama2, Mistral, etc │ │
                                │  └────────────────────────────────┘ │
                                └──────────────────────────────────────┘
```

## 🔄 Request Flow

### Scenario 1: Using VS Code Copilot Bridge

```
┌──────────┐      ┌────────────┐      ┌──────────────┐      ┌──────────┐
│  Client  │─────▶│ DevMindAPI │─────▶│  VS Code     │─────▶│ Copilot  │
│          │      │  (FastAPI) │      │  Extension   │      │  Cloud   │
└──────────┘      └────────────┘      └──────────────┘      └──────────┘
     │                   │                    │                    │
     │  POST /chat       │                    │                    │
     │  model=vscode     │                    │                    │
     │──────────────────▶│                    │                    │
     │                   │ WebSocket: prompt  │                    │
     │                   │───────────────────▶│                    │
     │                   │                    │  vscode.lm API     │
     │                   │                    │───────────────────▶│
     │                   │                    │                    │
     │                   │                    │◀───────────────────│
     │                   │                    │   AI Response      │
     │                   │◀───────────────────│                    │
     │                   │  WebSocket: resp   │                    │
     │◀──────────────────│                    │                    │
     │  JSON Response    │                    │                    │
```

### Scenario 2: Using Direct API (OpenAI Example)

```
┌──────────┐      ┌────────────┐      ┌──────────────┐
│  Client  │─────▶│ DevMindAPI │─────▶│  OpenAI API  │
│          │      │  (FastAPI) │      │              │
└──────────┘      └────────────┘      └──────────────┘
     │                   │                    │
     │  POST /chat       │                    │
     │  model=openai     │                    │
     │──────────────────▶│                    │
     │                   │                    │
     │                   │  HTTPS POST        │
     │                   │  /chat/completions │
     │                   │───────────────────▶│
     │                   │                    │
     │                   │◀───────────────────│
     │                   │   AI Response      │
     │◀──────────────────│                    │
     │  JSON Response    │                    │
```

## 🏗️ Component Details

### 1. Model Factory Pattern

```python
┌─────────────────────────────────────────┐
│         ModelFactory                     │
├─────────────────────────────────────────┤
│  _providers = {                         │
│    "openai": OpenAIProvider,            │
│    "claude": ClaudeProvider,            │
│    "gemini": GeminiProvider,            │
│    "ollama": OllamaProvider             │
│  }                                      │
├─────────────────────────────────────────┤
│  create_provider(name) → Provider       │
│  get_available_providers() → Dict       │
└─────────────────────────────────────────┘
              │
              │ creates
              ▼
┌─────────────────────────────────────────┐
│      BaseModelProvider                   │
├─────────────────────────────────────────┤
│  + generate(prompt, **kwargs) → str     │
│  + is_available() → bool                │
└─────────────────────────────────────────┘
              △
              │ inherits
    ┌─────────┴─────────┬─────────┬──────────┐
    │                   │         │          │
┌───▼──────┐  ┌────────▼───┐  ┌──▼──────┐  ┌▼────────┐
│ OpenAI   │  │  Claude    │  │ Gemini  │  │ Ollama  │
│ Provider │  │  Provider  │  │Provider │  │Provider │
└──────────┘  └────────────┘  └─────────┘  └─────────┘
```

### 2. Configuration Flow

```
.env file
   │
   │ loads on startup
   ▼
┌─────────────────────┐
│  Environment Vars   │
│  - OPENAI_API_KEY   │
│  - ANTHROPIC_KEY    │
│  - GOOGLE_KEY       │
└──────────┬──────────┘
           │
           │ accessed by
           ▼
┌─────────────────────┐
│  Model Providers    │
│  - OpenAIProvider   │
│  - ClaudeProvider   │
│  - GeminiProvider   │
└──────────┬──────────┘
           │
           │ registered in
           ▼
┌─────────────────────┐
│  MODEL_ROUTING      │
│  {                  │
│   "openai-gpt4":    │
│     ("openai",      │
│      "gpt-4")       │
│  }                  │
└─────────────────────┘
```

## 📊 Model Selection Decision Tree

```
                    ┌──────────────┐
                    │ API Request  │
                    │ with "model" │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │ Is model ==   │
                    │"vscode-bridge"│
                    └───┬─────┬─────┘
                        │     │
                   YES  │     │ NO
                        │     │
              ┌─────────▼     ▼──────────┐
              │                           │
        ┌─────▼──────┐           ┌───────▼────────┐
        │ Use VS Code│           │ Lookup model in│
        │  WebSocket │           │  MODEL_ROUTING │
        │   Bridge   │           └───────┬────────┘
        └─────┬──────┘                   │
              │                          │
              │                  ┌───────▼────────┐
              │                  │ Get provider & │
              │                  │  model name    │
              │                  └───────┬────────┘
              │                          │
              │                  ┌───────▼────────┐
              │                  │ Create/Get     │
              │                  │  Provider      │
              │                  └───────┬────────┘
              │                          │
              │                  ┌───────▼────────┐
              │                  │ Check if       │
              │                  │  available     │
              │                  └───┬───────┬────┘
              │                      │       │
              │                  YES │       │ NO
              │                      │       │
              │           ┌──────────▼       ▼────────────┐
              │           │                               │
              │    ┌──────▼──────┐              ┌────────▼────┐
              │    │Call provider│              │ Return 503  │
              │    │  .generate()│              │   Error     │
              │    └──────┬──────┘              └─────────────┘
              │           │
              └───────────┴────────────┐
                                       │
                              ┌────────▼─────────┐
                              │ Return Response  │
                              │  to Client       │
                              └──────────────────┘
```

## 🔐 Security Layers

```
┌────────────────────────────────────────────────┐
│              Public Internet                    │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│         1. CORS Middleware                      │
│   (Controls which origins can access API)       │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│         2. Request Validation                   │
│   (Pydantic models validate input)              │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│         3. API Key Management                   │
│   (Keys stored in .env, never in code)          │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│         4. Rate Limiting (Optional)             │
│   (Prevent abuse and control costs)             │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│         5. Logging & Monitoring                 │
│   (Track all requests for audit)                │
└─────────────────────────────────────────────────┘
```

## 💰 Cost Optimization Strategy

```
                    ┌──────────────┐
                    │   Request    │
                    │   Arrives    │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │  Check task   │
                    │  complexity   │
                    └───┬───────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼───┐    ┌────▼────┐    ┌───▼────┐
    │ Simple │    │ Medium  │    │Complex │
    │  Task  │    │  Task   │    │  Task  │
    └────┬───┘    └────┬────┘    └───┬────┘
         │             │              │
    ┌────▼─────┐  ┌───▼──────┐  ┌────▼─────┐
    │ Use Free │  │Use Cheap │  │Use Best  │
    │ Copilot  │  │ GPT-3.5  │  │ GPT-4    │
    │   OR     │  │   OR     │  │   OR     │
    │  Ollama  │  │  Haiku   │  │  Opus    │
    └──────────┘  └──────────┘  └──────────┘
         │             │              │
         └─────────────┴──────────────┘
                       │
                ┌──────▼───────┐
                │   Return     │
                │   Response   │
                └──────────────┘

Cost Ranking:
1. Ollama (Local) - FREE
2. VS Code Copilot - SUBSCRIPTION (~$10/month)
3. GPT-3.5 / Haiku - LOW (~$0.50 per 1M tokens)
4. Sonnet / Gemini - MEDIUM (~$3 per 1M tokens)
5. GPT-4 / Opus - HIGH (~$15-30 per 1M tokens)
```

## 🚀 Deployment Options

### Option 1: Local Development
```
┌─────────────┐
│   Laptop    │
│             │
│  ┌───────┐  │
│  │DevMind│  │
│  │  API  │  │
│  └───────┘  │
│      +      │
│  ┌───────┐  │
│  │VS Code│  │
│  └───────┘  │
└─────────────┘
```

### Option 2: Docker Container
```
┌────────────────────┐
│  Docker Container  │
│                    │
│  ┌──────────────┐  │
│  │  DevMindAPI  │  │
│  │    +         │  │
│  │  VS Code Ext │  │
│  └──────────────┘  │
│                    │
│  Port: 8000        │
└────────────────────┘
```

### Option 3: Cloud Deployment
```
┌─────────────────────────────┐
│      Cloud Provider         │
│   (AWS/Azure/GCP)           │
│                             │
│  ┌───────────────────────┐  │
│  │   DevMindAPI          │  │
│  │   (Container/VM)      │  │
│  └───────────────────────┘  │
│           │                 │
│  ┌────────▼──────────┐      │
│  │   Load Balancer   │      │
│  └───────────────────┘      │
└─────────────────────────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│   Your Clients  │
└─────────────────┘
```

## 📈 Scaling Considerations

### Vertical Scaling
```
┌──────────────────┐
│  Single Server   │
│                  │
│  More CPU        │
│  More RAM        │
│  More Threads    │
└──────────────────┘
```

### Horizontal Scaling
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Server 1 │  │ Server 2 │  │ Server 3 │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┴─────────────┘
                   │
          ┌────────▼─────────┐
          │  Load Balancer   │
          └──────────────────┘
```

## 🔍 Monitoring Dashboard (Conceptual)

```
┌─────────────────────────────────────────────────────────┐
│                  DevMindAPI Dashboard                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Total Requests: 1,234   │  Active: 5   │  Errors: 3   │
│                                                          │
├──────────────────┬──────────────────────────────────────┤
│                  │                                       │
│  Model Usage     │   Response Times                      │
│  ────────────    │   ──────────────                      │
│  ▓▓▓ GPT-4  45%  │   GPT-4:    2.3s                     │
│  ▓▓  Claude 30%  │   Claude:   1.8s                     │
│  ▓   Copilot 15% │   Copilot:  1.2s                     │
│  ▓   Other  10%  │   Ollama:   0.5s                     │
│                  │                                       │
├──────────────────┴──────────────────────────────────────┤
│                                                          │
│  API Costs (24h)             │  Error Rate              │
│  ───────────────             │  ──────────              │
│  OpenAI:    $12.50           │  503 errors:  2          │
│  Claude:    $8.30            │  500 errors:  1          │
│  Gemini:    $3.20            │  Timeouts:    0          │
│  Total:     $24.00           │  Success: 99.7%          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

This visual guide helps you understand how all the components work together!

For implementation details, see: [MULTI_MODEL_GUIDE.md](MULTI_MODEL_GUIDE.md)
