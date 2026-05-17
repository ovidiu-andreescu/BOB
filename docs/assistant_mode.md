# AI Assistant Mode

## Overview

RepoQuest includes an **optional AI-first hybrid analyzer** that can provide additional insights beyond deterministic static analysis.

When AI is configured, RepoQuest runs deterministic analysis first, then runs **AI Fusion**. AI Fusion audits the project classification, architecture interpretation, reading path notes, component notes, risks, and recommendations using bounded context from the deterministic analyzer.

**Important:** The AI assistant is:
- **Disabled by default**
- **Optional** - all core RepoQuest features work without it
- **AI-first when configured** - AI Fusion runs automatically after deterministic analysis
- **Bounded** - only receives capped context packs, not entire repos
- **Safe** - validates responses to prevent execution claims
- **Multiple providers** - supports Claude, local models, and mock mode

AI Fusion may send capped snippets and structured repository summaries to the configured provider. Deterministic mode sends no snippets and makes no AI/model calls.

## AI Fusion Trust Model

The deterministic analyzer remains the evidence source. AI Fusion can override only interpretation-level outputs:

- project type
- framework labels/confidence notes
- entry point ranking
- architecture summary
- reading path notes
- component notes
- improvement risks and recommendations

AI Fusion cannot delete or rewrite deterministic facts such as scanned files, extracted routes, import edges, ZIP safety warnings, skipped files, or upload limits.

Every override must cite existing scanned file paths. Project-type overrides require confidence of at least `0.75` and at least two evidence paths. If deterministic confidence is already high, AI confidence must exceed it by `0.10`; otherwise the AI output is shown as a disagreement rather than an override.

## Deployment Profiles

RepoQuest supports multiple deployment profiles to accommodate different use cases, from public demos to private local development.

### Profile Comparison

| Profile | AI Enabled | Secrets Required | Network Calls | Use Case |
|---------|-----------|------------------|---------------|----------|
| **Deterministic** | No | None | None | Default, public demo, Streamlit Cloud |
| **Mock Assistant** | Yes | None | None | Testing, CI/CD, development |
| **Cloud Assistant** | Yes | API key | Claude API | Live demo with AI, development |
| **Local Model** | Yes | None | Local only | Private/offline AI, experimentation |
| **Service Assistant** | Yes | Varies | Varies | Async processing, scalability |

### 1. Deterministic Code Assistant (Default)

**Status:** Production-ready, recommended for public deployment

**Features:**
- No AI, no secrets, no external calls
- Fully deterministic static analysis
- Safe for Streamlit Community Cloud
- Works offline
- Zero API costs

**Setup:**
```bash
# Local
python scripts/run_local.py

# Docker
docker compose up --build repoquest

# Streamlit Cloud
# Deploy with no secrets required
```

**Environment:**
```bash
REPOQUEST_AI_ENABLED=false  # or unset
```

### 2. Mock AI Assistant

**Status:** Development/testing only

**Features:**
- AI UI enabled with deterministic responses
- No network calls
- No API costs
- Tests assistant integration
- Validates UI flows

**Setup:**
```bash
# Local
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=mock \
python scripts/run_local.py

# Docker with service
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
docker compose --profile assistant up --build
```

**Environment:**
```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_PROVIDER=mock
```

### 3. Cloud AI Assistant (Claude)

**Status:** Production-ready with API key

**Features:**
- Real Claude API integration
- High-quality AI insights
- Bounded context packs
- Response validation
- Deterministic fallback preserved

**Setup:**
```bash
# Local
REPOQUEST_AI_ENABLED=true \
CLAUDE_API_KEY=your_key_here \
python scripts/run_local.py

# Docker with service
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
CLAUDE_API_KEY=your_key_here \
docker compose --profile assistant up --build

# Streamlit Cloud
# Add secrets in dashboard:
# REPOQUEST_AI_ENABLED = "true"
# CLAUDE_API_KEY = "your_key_here"
```

**Environment:**
```bash
REPOQUEST_AI_ENABLED=true
CLAUDE_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514  # optional
```

**Requirements:**
- Valid Anthropic API key
- Network access to api.anthropic.com
- API usage costs apply

**Privacy:** Code snippets (max 800 chars each) sent to Claude API. See Privacy & Data section.

### 4. Local Model Assistant

**Status:** Experimental, for private/offline use

**Features:**
- No cloud API required
- Works with local model servers
- OpenAI-compatible endpoint support
- Private/offline AI
- No API costs (compute costs only)

**Supported servers:**
- Ollama (recommended)
- LM Studio
- llama.cpp server
- Any OpenAI-compatible endpoint

**Setup with Ollama:**
```bash
# 1. Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1

# 2. Run RepoQuest
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
python scripts/run_local.py

# 3. Docker with service
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
docker compose --profile assistant up --build
```

**Environment:**
```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_PROVIDER=local
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1
REPOQUEST_LOCAL_MODEL_NAME=llama3.1
```

**Notes:**
- Local model quality varies by size and training
- Responses may be slower than cloud APIs
- Requires local compute resources
- No data leaves your machine

### 5. Async Assistant Service

**Status:** Production-ready for scalability

**Features:**
- Separate service container
- Async job processing
- Keeps Streamlit UI responsive
- Supports all provider types
- In-memory job queue

**Setup:**
```bash
# Mock mode
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
docker compose --profile assistant up --build

# Cloud mode
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
CLAUDE_API_KEY=your_key_here \
docker compose --profile assistant up --build

# Local model mode
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
docker compose --profile assistant up --build
```

**Environment:**
```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765
REPOQUEST_ASSISTANT_SERVICE_TIMEOUT_SECONDS=45
# Plus provider-specific variables
```

**Service endpoints:**
- `GET /health` - Health check
- `POST /jobs` - Submit assistant request
- `GET /jobs/{job_id}` - Poll job status

**Notes:**
- Jobs stored in memory only
- Restarting service clears pending jobs
- Deterministic analysis unaffected by service status

## Configuration

### Environment Variables

Create a `.env` file (not tracked in git):

```bash
cp .env.example .env

# Enable AI assistant (default: false)
REPOQUEST_AI_ENABLED=true

# Claude API key (required if enabled)
CLAUDE_API_KEY=your_api_key_here

# Claude model (optional, default: claude-sonnet-4-20250514)
CLAUDE_MODEL=claude-sonnet-4-20250514

# Optional async assistant service URL.
# Use this when Streamlit should submit assistant jobs to a separate service.
REPOQUEST_ASSISTANT_SERVICE_URL=
REPOQUEST_ASSISTANT_SERVICE_TIMEOUT_SECONDS=45
```

### Streamlit Secrets (Cloud Deployment)

For Streamlit Community Cloud, add secrets in the dashboard:

```toml
REPOQUEST_AI_ENABLED = "true"
CLAUDE_API_KEY = "your_api_key_here"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
```

If `REPOQUEST_AI_ENABLED=true` is set while no API key or assistant service is available, RepoQuest keeps deterministic analysis enabled and shows a "no API key configured" assistant status.

### Docker Compose Assistant Service

RepoQuest can also run optional AI/model work in a separate service. This keeps
the Streamlit UI process focused on deterministic analysis and makes assistant
calls asynchronous at the service boundary.

Deterministic app only:

```bash
docker compose up --build repoquest
```

App plus assistant service in mock mode:

```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
docker compose --profile assistant up --build
```

App plus assistant service using Claude:

```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
CLAUDE_API_KEY=your_api_key_here \
docker compose --profile assistant up --build
```

The assistant service exposes:

- `GET /health` for readiness checks.
- `POST /jobs` to enqueue an assistant request.
- `GET /jobs/{job_id}` to poll queued/running/completed status.

The service stores jobs in memory only. Restarting the service clears pending
assistant jobs, while deterministic RepoQuest analysis remains available.

## Features

When enabled, AI assistant buttons appear in these sections:

### 1. Overview Tab
- **Button:** "Get AI Insights on Overview"
- **Context:** Project type, frameworks, entry points, key folders
- **Output:** High-level analysis and recommendations

### 2. Architecture Map Tab
- **Button:** "Ask AI about this file" (after selecting a graph node)
- **Context:** Selected file metadata, imports, routes, tests, and snippets
- **Output:** Node-specific explanation and follow-up suggestions

### 3. Reading Path Tab
- **Button:** "Ask AI to explain..." (per reading path file)
- **Context:** File role, capped source preview, and detected routes where relevant
- **Output:** File explanation, risks, and improvement ideas

### 4. Components Tab
- **Button:** Component-specific assistant action
- **Context:** Component role, connections, detected items
- **Output:** Component-specific insights and improvement ideas

### 5. Tests Tab
- **Button:** "Get Test Recommendations"
- **Context:** Test inventory, coverage gaps, quality signals
- **Output:** Prioritized test suggestions

### 6. Work Plans Tab
- **Button:** "Refine Work Plan"
- **Context:** Generated tasks, workflows, milestones
- **Output:** Enhanced task descriptions and priorities

### 7. Documentation and Export Tabs
- **Button:** "Improve Documentation"
- **Context:** Existing docs, detected gaps
- **Output:** Documentation enhancement suggestions

## Safety Features

### Response Validation

All AI responses are validated to ensure:

1. **Non-empty responses** - Rejects blank outputs
2. **Valid file citations** - Only cites files that exist in the scanned repo
3. **No execution claims** - Rejects responses claiming tests were run
4. **No execution instructions** - Rejects responses instructing code execution

### Context Limits

AI requests are bounded:

- **Max snippet size:** 800 characters per file
- **Max files:** Limited by section (typically 5-10)
- **Safe files only:** Excludes `.env`, secrets, binaries
- **Static analysis warning:** Every request includes a disclaimer

### Example Validation

Rejected:
```
"I ran the tests and they all passed."
```

Accepted:
```
"Based on static analysis of backend/routes/trips.py,
the route handlers appear to lack input validation."
```

## Architecture

### Provider Pattern

```python
class AssistantProvider(Protocol):
  def generate(request: AssistantRequest) -> AssistantResponse:
   ...
```

**Implementations:**
- `DisabledAssistantProvider` - Returns "disabled"status
- `MockAssistantProvider` - Returns deterministic test responses
- `ClaudeAssistantProvider` - Calls Claude API via stdlib urllib
- `AssistantServiceProvider` - Submits jobs to the optional async assistant service

### Context Builders

Each section has a dedicated context builder:

- `build_overview_context()` - Project summary
- `build_file_context()` - Single file analysis
- `build_component_context()` - Component card analysis
- `build_test_context()` - Test intelligence
- `build_workflow_context()` - Work plan refinement
- `build_documentation_context()` - Doc enhancement

### Data Flow

```
User clicks AI button
 -> Context builder creates AssistantRequest
 -> Provider generates AssistantResponse directly or submits a service job
 -> Optional service queues/runs the model call asynchronously
 -> Validator checks response
 -> UI displays result or validation error
```

## Usage Guidelines

### When to Use AI Assistant

 **Good use cases:**
- Getting high-level project insights
- Understanding complex component relationships
- Prioritizing test coverage gaps
- Refining work plan descriptions
- Improving documentation clarity

 **Not suitable for:**
- Replacing deterministic analysis
- Executing code or tests
- Making production decisions
- Security audits
- Compliance validation

### Best Practices

1. **Review AI outputs** - Always validate suggestions against actual code
2. **Use deterministic first** - Generate the quest before using AI
3. **Cite evidence** - Check that AI citations reference real files
4. **Stay bounded** - AI only sees capped snippets, not full files
5. **Manual only** - AI never runs automatically during quest generation

## Cost Considerations

- **API calls:** Each AI button click = 1 Claude API call
- **Token usage:** Typically 500-1500 tokens per request
- **Pricing:** See Anthropic pricing for current rates
- **Free tier:** Deterministic RepoQuest is always free

## Troubleshooting

### AI Assistant Not Available

**Symptom:** Sidebar shows "AI Assistant is disabled"

**Solutions:**
1. Set `REPOQUEST_AI_ENABLED=true` in `.env`
2. Restart the Streamlit app
3. Check sidebar status panel

### API Key Not Configured

**Symptom:** Sidebar shows "AI Assistant enabled but no API key configured"

**Solutions:**
1. Set `CLAUDE_API_KEY` in `.env` or Streamlit secrets
2. Verify key is valid
3. Restart the app

### Assistant Service Unavailable

**Symptom:** An AI button returns "Assistant service network error"

**Solutions:**
1. Confirm the service is running: `docker compose --profile assistant ps`
2. Check that the app has `REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765`
3. Try mock mode first with `REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock`
4. Check `GET http://localhost:8765/health` from the host

### Validation Errors

**Symptom:** Warning message after AI response

**Common causes:**
- AI cited non-existent files -> Check file paths
- AI claimed test execution -> Regenerate with different phrasing
- Empty response -> Try again or check API status

## Development

### Adding New AI Features

1. Create context builder in `repoquest/assistant_context.py`
2. Add button in relevant tab in `app/streamlit_app.py`
3. Use `run_assistant()` helper function
4. Display result from `st.session_state["assistant_outputs"]`

### Testing

```bash
# Run assistant tests
pytest tests/test_assistant.py -v

# Test with mock provider
REPOQUEST_AI_ENABLED=true pytest tests/test_assistant.py
```

### Mock Provider for Testing

```python
from repoquest.assistant_provider import MockAssistantProvider

provider = MockAssistantProvider(
  mock_response="Test response",
  mock_citations=[AssistantCitation(file_path="test.py")]
)
```

## Comparison: Deterministic vs AI

| Feature | Deterministic | AI Assistant |
|---------|--------------|--------------|
| **Always available** | Yes | Requires API key |
| **Cost** | Free | API costs |
| **Speed** | Instant | Usually a few seconds |
| **Reproducible** | Yes | May vary |
| **Evidence-based** | Always | Validated citations |
| **Offline** | Yes | Requires network |
| **Privacy** | Local only | Warning: Sends snippets |

## Privacy & Data

### What Gets Sent to Claude

- Capped code snippets (max 800 chars each)
- File paths and roles
- Project type and framework names
- Detected routes and components
- **Never sent:** Full files, secrets, binaries, credentials

### Network And Certificates

The Claude provider uses the Python standard library HTTP client. When available, it uses the local `certifi` certificate bundle to avoid common macOS certificate-chain errors. Network or certificate failures are displayed as assistant errors and do not interrupt deterministic RepoQuest output.

In Docker assistant mode, the Claude call happens inside the `assistant` service. The Streamlit app receives only the assistant response/job status from the service, then still applies RepoQuest response validation before display.

### Data Retention

- RepoQuest does not store AI responses permanently
- Responses live in Streamlit session state only
- Claude API retention: See Anthropic privacy policy

## Future Enhancements

Potential future features (not yet implemented):

- Streaming responses for long outputs
- Multi-turn conversations
- Custom system prompts
- Alternative LLM providers
- Response caching
- Persistent job storage beyond the current in-memory queue

## Support

For issues or questions:

1. Check this documentation
2. Review validation messages
3. Test with mock provider
4. Check Anthropic API status
5. Open GitHub issue with details

---

**Remember:** AI assistant is optional. RepoQuest's deterministic analysis is the foundation.
