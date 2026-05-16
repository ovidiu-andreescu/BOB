# Local Model Support

RepoQuest supports running AI assistant features with local models through OpenAI-compatible endpoints.

## Overview

Local model support allows you to:

- Run RepoQuest AI features without cloud API keys
- Use private/local models for sensitive codebases
- Experiment with different open-source models
- Reduce API costs for development/testing

## Supported Providers

RepoQuest supports any OpenAI-compatible local model endpoint, including:

- **Ollama** (recommended for ease of use)
- **LM Studio**
- **llama.cpp server**
- **vLLM**
- **LocalAI**
- Any other OpenAI-compatible endpoint

## Quick Start with Ollama

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com
```

### 2. Pull a Model

```bash
# Recommended models for code analysis
ollama pull llama3.1
ollama pull codellama
ollama pull deepseek-coder
```

### 3. Start Ollama Server

```bash
# Ollama runs on http://localhost:11434 by default
ollama serve
```

### 4. Configure RepoQuest

Create or update `.env`:

```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_PROVIDER=local
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1
REPOQUEST_LOCAL_MODEL_NAME=llama3.1
```

### 5. Run RepoQuest

```bash
python scripts/run_local.py
```

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REPOQUEST_AI_ENABLED` | Enable AI assistant features | `true` |
| `REPOQUEST_ASSISTANT_PROVIDER` | Provider type: `claude`, `local`, or `service` | `local` |
| `REPOQUEST_LOCAL_MODEL_BASE_URL` | OpenAI-compatible endpoint URL | `http://localhost:11434/v1` |
| `REPOQUEST_LOCAL_MODEL_NAME` | Model name to use | `llama3.1` |

### Streamlit Secrets

For Streamlit Cloud deployment, add to `.streamlit/secrets.toml`:

```toml
REPOQUEST_AI_ENABLED = true
REPOQUEST_ASSISTANT_PROVIDER = "local"
REPOQUEST_LOCAL_MODEL_BASE_URL = "http://host.docker.internal:11434/v1"
REPOQUEST_LOCAL_MODEL_NAME = "llama3.1"
```

## Docker Deployment

### Docker Compose with Local Model

Update `docker-compose.yml`:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.app
    environment:
      - REPOQUEST_AI_ENABLED=true
      - REPOQUEST_ASSISTANT_PROVIDER=local
      - REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1
      - REPOQUEST_LOCAL_MODEL_NAME=llama3.1
    ports:
      - "8501:8501"
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### With Assistant Service

For async processing:

```yaml
services:
  app:
    environment:
      - REPOQUEST_AI_ENABLED=true
      - REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765
    depends_on:
      - assistant

  assistant:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.assistant
    environment:
      - REPOQUEST_ASSISTANT_PROVIDER=local
      - REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1
      - REPOQUEST_LOCAL_MODEL_NAME=llama3.1
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

## Model Recommendations

### For Code Analysis

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llama3.1` | 8B | Fast | Good | General code analysis |
| `codellama` | 7B | Fast | Good | Code-specific tasks |
| `deepseek-coder` | 6.7B | Fast | Excellent | Code understanding |
| `qwen2.5-coder` | 7B | Fast | Excellent | Code generation |

### For Documentation

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llama3.1` | 8B | Fast | Good | General docs |
| `mistral` | 7B | Fast | Good | Technical writing |

## Troubleshooting

### Connection Refused

**Problem:** `Network error connecting to local model`

**Solutions:**

1. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/v1/models
   ```

2. Check firewall settings

3. For Docker, use `host.docker.internal` instead of `localhost`

### Model Not Found

**Problem:** `Local model API error (404)`

**Solutions:**

1. Verify the models endpoint works:
   ```bash
   curl http://localhost:11434/v1/models
   ```

2. Verify the chat completions endpoint exists:
   ```bash
   curl http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"llama3.1","messages":[{"role":"user","content":"Say hi"}]}'
   ```

3. Verify model is pulled:
   ```bash
   ollama list
   ```

4. Pull the model:
   ```bash
   ollama pull llama3.1
   ```

5. Check model name matches configuration.

RepoQuest uses OpenAI-compatible chat completions. If `/v1/models` works but
`/v1/chat/completions` returns 404, update the local model server or switch to an
OpenAI-compatible server/profile. For Ollama, use a recent version and:

```bash
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1
REPOQUEST_LOCAL_MODEL_NAME=llama3.1
```

### Slow Responses

**Problem:** AI responses take too long

**Solutions:**

1. Use smaller models (7B instead of 13B+)
2. Enable GPU acceleration
3. Reduce `max_tokens` in requests
4. Use quantized models (Q4, Q5)

### Empty Responses

**Problem:** Model returns empty content

**Solutions:**

1. Try a different model
2. Check model is compatible with chat format
3. Verify model supports system messages
4. Increase temperature/top_p parameters

## Performance Tips

### GPU Acceleration

Ollama automatically uses GPU if available:

```bash
# Check GPU usage
nvidia-smi

# Or for AMD
rocm-smi
```

### Memory Management

For limited RAM:

```bash
# Use smaller quantized models
ollama pull llama3.1:7b-q4_0

# Or set memory limits
OLLAMA_MAX_LOADED_MODELS=1 ollama serve
```

### Concurrent Requests

For multiple users:

```bash
# Increase parallel requests
OLLAMA_NUM_PARALLEL=4 ollama serve
```

## Security Considerations

### Local-Only Deployment

Local models never send data to external services:

- All processing happens on your machine
- No API keys required
- No network calls to cloud providers
- Full control over data privacy

### Network Isolation

For sensitive codebases:

1. Run Ollama on isolated network
2. Use firewall rules to restrict access
3. Disable internet access for the model server
4. Use VPN/private network for remote access

## Advanced Configuration

### Custom Model Parameters

Create a custom Modelfile:

```dockerfile
FROM llama3.1

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096

SYSTEM """You are a code analysis assistant for RepoQuest.
Focus on static analysis and evidence-based insights."""
```

Load it:

```bash
ollama create repoquest-analyzer -f Modelfile
```

Use it:

```bash
REPOQUEST_LOCAL_MODEL_NAME=repoquest-analyzer
```

### LM Studio Configuration

1. Start LM Studio
2. Load a model
3. Enable "Local Server" in settings
4. Configure RepoQuest:

```bash
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:1234/v1
REPOQUEST_LOCAL_MODEL_NAME=<model-name>
```

### llama.cpp Server

```bash
# Start server
./server -m models/llama-3.1-8b.gguf --port 8080

# Configure RepoQuest
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:8080/v1
REPOQUEST_LOCAL_MODEL_NAME=llama-3.1-8b
```

## Comparison: Local vs Cloud

| Feature | Local Models | Claude API |
|---------|--------------|------------|
| **Cost** | Free (hardware only) | Pay per token |
| **Privacy** | Fully private | Data sent to Anthropic |
| **Speed** | Depends on hardware | Fast (cloud) |
| **Quality** | Good (varies by model) | Excellent |
| **Setup** | Requires installation | API key only |
| **Offline** | Yes | No |

## Best Practices

1. **Start with Ollama** - Easiest setup and good performance
2. **Use 7B-8B models** - Best balance of speed and quality
3. **Test locally first** - Verify setup before Docker deployment
4. **Monitor resources** - Watch CPU/GPU/RAM usage
5. **Keep models updated** - Pull latest versions regularly
6. **Use quantized models** - Q4/Q5 for better performance
7. **Set reasonable timeouts** - Local models can be slower
8. **Fallback to deterministic** - Always works without AI

## Migration from Cloud to Local

### Step 1: Test Locally

```bash
# Keep Claude config as backup
CLAUDE_API_KEY=sk-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# Add local config
REPOQUEST_ASSISTANT_PROVIDER=local
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1
REPOQUEST_LOCAL_MODEL_NAME=llama3.1
```

### Step 2: Compare Results

Run the same analysis with both providers and compare quality.

### Step 3: Switch Provider

Update `.env`:

```bash
REPOQUEST_ASSISTANT_PROVIDER=local
```

### Step 4: Remove Cloud Config (Optional)

```bash
# Remove or comment out
# CLAUDE_API_KEY=...
```

## Support

For issues with:

- **Ollama**: https://github.com/ollama/ollama/issues
- **LM Studio**: https://lmstudio.ai/docs
- **RepoQuest**: See main README.md

## Related Documentation

- [AI Assistant Overview](assistant_mode.md)
- [Docker Deployment](../infra/docker/README.md)
- [Configuration Guide](../README.md#configuration)

# Made with Bob
