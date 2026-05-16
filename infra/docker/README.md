# Docker Deployment Guide

This directory contains Docker configurations for RepoQuest deployment.

## Available Dockerfiles

- `Dockerfile.app` - Main Streamlit application
- `Dockerfile.assistant` - Optional async assistant service

## Deployment Profiles

RepoQuest supports multiple deployment profiles via Docker Compose. Each profile is designed for specific use cases.

### Profile 1: Deterministic Code Assistant (Default)

**Use case:** Production demo, Streamlit Community Cloud alternative, no AI required

**Features:**
- No secrets required
- No external API calls
- Fully deterministic analysis
- Safe for public deployment
- Works offline

**Command:**
```bash
docker compose up --build repoquest
```

**Access:**
- App: http://localhost:8501

**Environment variables:** None required

---

### Profile 2: Mock AI Assistant

**Use case:** Testing, development, CI/CD validation

**Features:**
- AI mode enabled
- No network calls
- Deterministic mock responses
- Tests assistant UI without API costs
- Validates async service integration

**Command:**
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
docker compose --profile assistant up --build
```

**Access:**
- App: http://localhost:8501
- Assistant service: http://localhost:8765
- Health check: http://localhost:8765/health

**Environment variables:**
- `REPOQUEST_AI_ENABLED=true` - Enable AI features
- `REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765` - Point to service
- `REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock` - Use mock provider

---

### Profile 3: Cloud AI Assistant (Claude)

**Use case:** Live demo with AI insights, development with real provider

**Features:**
- Real Claude API integration
- Async assistant service
- Bounded context packs
- Response validation
- Deterministic fallback preserved

**Command:**
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
CLAUDE_API_KEY=your_api_key_here \
CLAUDE_MODEL=claude-sonnet-4-20250514 \
docker compose --profile assistant up --build
```

**Access:**
- App: http://localhost:8501
- Assistant service: http://localhost:8765
- Health check: http://localhost:8765/health

**Environment variables:**
- `REPOQUEST_AI_ENABLED=true` - Enable AI features
- `REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765` - Point to service
- `CLAUDE_API_KEY=your_key` - Your Anthropic API key
- `CLAUDE_MODEL=claude-sonnet-4-20250514` - Model to use (optional)

**Requirements:**
- Valid Anthropic API key
- Network access to api.anthropic.com
- API usage costs apply

**Privacy note:** Code snippets (max 800 chars each) are sent to Claude API. See `docs/assistant_mode.md` for details.

---

### Profile 4: Local Model Assistant

**Use case:** Private/offline AI, local model experimentation, no cloud dependencies

**Features:**
- No cloud API required
- Works with local model servers
- OpenAI-compatible endpoint support
- Bounded context packs
- Response validation
- Deterministic fallback preserved

**Supported local model servers:**
- Ollama (recommended)
- LM Studio
- llama.cpp server
- Any OpenAI-compatible endpoint

**Setup Ollama example:**

1. Install and start Ollama on host:
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.1

# Verify it's running
curl http://localhost:11434/v1/models
```

2. Run RepoQuest with local model:
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
docker compose --profile assistant up --build
```

**Access:**
- App: http://localhost:8501
- Assistant service: http://localhost:8765
- Health check: http://localhost:8765/health

**Environment variables:**
- `REPOQUEST_AI_ENABLED=true` - Enable AI features
- `REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765` - Point to service
- `REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local` - Use local model provider
- `REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1` - Local server URL
- `REPOQUEST_LOCAL_MODEL_NAME=llama3.1` - Model name

**Notes:**
- `host.docker.internal` allows Docker containers to access host services
- Local model responses may be slower than cloud APIs
- Model quality varies by size and training
- No API costs, but requires local compute resources

---

## Direct Provider Mode (No Service)

You can also run the app with direct provider calls (no async service):

**Mock mode:**
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=mock \
docker compose up --build repoquest
```

**Claude mode:**
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=claude \
CLAUDE_API_KEY=your_key_here \
docker compose up --build repoquest
```

**Local model mode:**
```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
docker compose up --build repoquest
```

---

## Environment Variables Reference

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOQUEST_AI_ENABLED` | `false` | Enable AI assistant features |

### Assistant Service Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOQUEST_ASSISTANT_SERVICE_URL` | (empty) | Assistant service URL (e.g., `http://assistant:8765`) |
| `REPOQUEST_ASSISTANT_SERVICE_TIMEOUT_SECONDS` | `45` | Request timeout for service calls |
| `REPOQUEST_ASSISTANT_SERVICE_PROVIDER` | (empty) | Provider override for service: `mock`, `claude`, `local` |

### Direct Provider Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOQUEST_ASSISTANT_PROVIDER` | `claude` | Direct provider: `mock`, `claude`, `local` |

### Cloud Provider Settings (Claude)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_API_KEY` | (empty) | Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model to use |

### Local Model Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOQUEST_LOCAL_MODEL_BASE_URL` | (empty) | OpenAI-compatible endpoint URL |
| `REPOQUEST_LOCAL_MODEL_NAME` | (empty) | Model name to request |

---

## Troubleshooting

### Assistant service won't start

**Symptom:** `docker compose --profile assistant up` fails

**Solutions:**
1. Check that `REPOQUEST_AI_ENABLED=true` is set
2. Verify Docker Compose version supports profiles (v1.28+)
3. Check logs: `docker compose --profile assistant logs assistant`

### App can't reach assistant service

**Symptom:** "Assistant service network error" in UI

**Solutions:**
1. Verify service is running: `docker compose --profile assistant ps`
2. Check health endpoint: `curl http://localhost:8765/health`
3. Verify `REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765` in app container
4. Check Docker network: `docker network inspect proj_default`

### Local model connection fails

**Symptom:** "Local model server unavailable" errors

**Solutions:**
1. Verify Ollama/model server is running on host
2. Test from host: `curl http://localhost:11434/v1/models`
3. Check `host.docker.internal` resolves: `docker compose exec assistant ping host.docker.internal`
4. Try explicit host IP instead of `host.docker.internal`
5. Verify model is pulled: `ollama list`

### Claude API errors

**Symptom:** "Claude API error" or rate limit messages

**Solutions:**
1. Verify API key is valid
2. Check Anthropic API status
3. Review rate limits in Anthropic console
4. Try mock mode first to verify setup

### Slow responses

**Symptom:** AI requests take a long time

**Expected behavior:**
- Mock mode: < 1 second
- Claude API: 2-5 seconds typical
- Local models: 5-30 seconds depending on hardware and model size

**Solutions for local models:**
1. Use smaller models (e.g., `llama3.1:8b` instead of `llama3.1:70b`)
2. Ensure adequate RAM/VRAM
3. Check CPU/GPU utilization
4. Consider quantized models for faster inference

---

## Security Notes

### Secrets Management

**Never commit secrets to git:**
- Use `.env` files (gitignored)
- Use Docker secrets for production
- Use Streamlit secrets for cloud deployment

**In Docker Compose:**
```bash
# Good: Environment variable from shell
CLAUDE_API_KEY=your_key docker compose up

# Good: .env file (gitignored)
docker compose --env-file .env up

# Bad: Hardcoded in docker-compose.yml
# environment:
#   CLAUDE_API_KEY: "sk-ant-..."  # DON'T DO THIS
```

### Network Security

**Deterministic profile:**
- No external network calls
- Safe for public deployment
- No secrets required

**AI-enabled profiles:**
- Cloud mode: Sends code snippets to external API
- Local mode: Network calls stay on local network
- Service mode: Internal Docker network only

### Data Privacy

**What gets sent to AI providers:**
- Capped code snippets (max 800 chars each)
- File paths and roles
- Project metadata
- Detected routes/components

**Never sent:**
- Full file contents
- Binary files
- `.env` files
- Secrets or credentials
- User data

See `docs/assistant_mode.md` for complete privacy details.

---

## Production Deployment

### Streamlit Community Cloud

For Streamlit Cloud deployment, use the deterministic profile (no Docker required):

1. Push repo to GitHub
2. Deploy via Streamlit Cloud dashboard
3. Set main file: `app/streamlit_app.py`
4. No secrets required for deterministic mode

For AI-enabled cloud deployment:
1. Add secrets in Streamlit dashboard:
   ```toml
   REPOQUEST_AI_ENABLED = "true"
   CLAUDE_API_KEY = "your_key_here"
   ```
2. Use direct provider mode (no assistant service)

### Self-Hosted with Docker

**Deterministic only:**
```bash
docker compose up -d repoquest
```

**With AI assistant service:**
```bash
# Create .env file with secrets
docker compose --profile assistant up -d
```

**Behind reverse proxy:**
```nginx
location / {
    proxy_pass http://localhost:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

## Development

### Building Images

```bash
# Build app only
docker compose build repoquest

# Build app and assistant service
docker compose --profile assistant build
```

### Running Tests

```bash
# Run tests in container
docker compose run --rm repoquest pytest -q

# Run with coverage
docker compose run --rm repoquest pytest --cov=repoquest
```

### Debugging

```bash
# View logs
docker compose logs -f repoquest
docker compose --profile assistant logs -f assistant

# Shell into container
docker compose exec repoquest bash
docker compose exec assistant bash

# Inspect environment
docker compose exec repoquest env | grep REPOQUEST
```

---

## Support

For issues or questions:

1. Check this documentation
2. Review `docs/assistant_mode.md`
3. Check Docker Compose logs
4. Test with mock mode first
5. Open GitHub issue with details

---

**Remember:** The deterministic profile is the default and safest option. AI features are optional enhancements.