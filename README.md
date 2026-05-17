# RepoQuest

**Turn unfamiliar repos into guided onboarding journeys**

RepoQuest helps developers onboard to small codebases faster by converting repository structure into a guided quest: project fingerprint, application graph, reading workbench, component cards, test intelligence, work plans, quiz, exportable docs, and optional AI-first hybrid analysis.

## What is RepoQuest?

RepoQuest is a deterministic repository onboarding mapper for small prototype-sized codebases. It analyzes repository structure and generates:

- **Project Fingerprint** - Detects project type, frameworks, and entry points
- **Architecture Map** - Visualizes component relationships and dependencies
- **Reading Workbench** - Suggests a guided tour with capped, scrollable file previews
- **Component Cards** - Detailed information about important files with test ideas
- **Test Intelligence** - Maps tests to likely targets and suggests missing coverage
- **Work Plans** - Generates deterministic epics, tasks, and milestones
- **Agent Workflows** - Generates step-by-step workflows for IBM Bob or another coding assistant
- **AI Fusion Analyzer** - When configured, audits deterministic findings and can override interpretation-level conclusions with cited evidence
- **Onboarding Quiz** - Verifies understanding with interactive questions
- **Markdown Export** - Generates comprehensive onboarding documentation

## Why RepoQuest?

Developers waste time figuring out where to start in unfamiliar codebases. RepoQuest solves this by:

- **Fast Analysis** - Scans and analyzes repositories in seconds
- **Deterministic Evidence Core** - Uses static analysis and rule evaluators; optional AI Fusion is disabled by default
- **Safe** - Validates ZIP uploads, never executes uploaded code
- **Actionable** - Provides specific next steps, AI Fusion notes when configured, and assistant-ready actions
- **Exportable** - Generates standalone Markdown guides for team onboarding

## Features

### Core Analysis
- Framework detection (React, FastAPI, Flask, Express, Next.js, Django, Streamlit)
- Project type classification (full-stack, frontend, backend, CLI, library)
- Entry point identification
- API route extraction (FastAPI supported in MVP 1)
- Import/dependency graph generation with connected-node graph views
- Test inventory, impact mapping, quality signals, and missing-coverage suggestions
- Rule-driven deterministic indicators and reusable response templates

### Onboarding Tools
- Prioritized reading path with time estimates and inline file previews
- Component cards with connections and test ideas
- Deterministic epics, tasks, milestones, and follow-up workflows
- Interactive quiz for knowledge verification
- Documentation and config file previews
- Optional AI Fusion for project interpretation, architecture notes, reading notes, and recommendations

### Security
- ZIP slip protection
- Path traversal prevention
- File size limits (25 MB max)
- Binary file detection
- No code execution
- No dependency installation

## Quick Start

### Local Development

**Prerequisites:**
- Python 3.11 or higher
- pip

**Setup:**

```bash
# Clone the repository
git clone <repository-url>
cd repoquest

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r infra/local/requirements-dev.txt

# Run the app
python scripts/run_local.py
```

The app will open at `http://localhost:8501`

**Run Tests:**

```bash
pytest -q
```

**Lint Code:**

```bash
ruff check .
```

### Streamlit Community Cloud Deployment

RepoQuest is designed to deploy easily to Streamlit Community Cloud:

1. Push this repository to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy with these settings:
  - **Repository:** Your GitHub repo
  - **Branch:** main
  - **Main file path:** `app/streamlit_app.py`
4. No secrets or environment variables required
5. The bundled demo repo works without file upload

See [infra/streamlit/README.md](infra/streamlit/README.md) for detailed deployment instructions.

### Docker Development

Run the deterministic app in Docker:

```bash
docker compose up --build repoquest
```

Run the app with the optional async assistant service in mock mode:

```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
docker compose --profile assistant up --build
```

For a real model call, provide `CLAUDE_API_KEY` instead of the mock provider.
Docker is optional and is not required for Streamlit Community Cloud.

## Deployment Profiles

RepoQuest supports multiple deployment profiles to accommodate different use cases:

| Profile | AI Enabled | Secrets Required | Network Calls | Best For |
|---------|-----------|------------------|---------------|----------|
| **Deterministic** | No | None | None | Public demo, Streamlit Cloud, default |
| **Mock Assistant** | Yes | None | None | Testing, CI/CD, development |
| **Cloud Assistant** | Yes | API key | Claude API | Live AI demo, development |
| **Local Model** | Yes | None | Local only | Private/offline AI, experimentation |
| **Service Assistant** | Yes | Varies | Varies | Async processing, scalability |

### Deterministic Code Assistant (Default)

The default profile requires no secrets and makes no external API calls. This is the recommended profile for:
- Public demos
- Streamlit Community Cloud deployment
- Offline development
- CI/CD pipelines

**Setup:**
```bash
python scripts/run_local.py
# or
docker compose up --build repoquest
```

### Mock AI Assistant

For testing AI features without network calls or API costs:

```bash
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=mock \
python scripts/run_local.py
```

### Cloud AI Assistant (Claude)

For live AI-assisted insights:

```bash
REPOQUEST_AI_ENABLED=true \
CLAUDE_API_KEY=your_key_here \
python scripts/run_local.py
```

**Streamlit Cloud:** Add secrets in dashboard:
```toml
REPOQUEST_AI_ENABLED = "true"
CLAUDE_API_KEY = "your_key_here"
```

### Local Model Assistant

For private/offline AI using local model servers (Ollama, LM Studio, etc.):

```bash
# Start Ollama
ollama pull llama3.1

# Run RepoQuest
REPOQUEST_AI_ENABLED=true \
REPOQUEST_ASSISTANT_PROVIDER=local \
REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1 \
REPOQUEST_LOCAL_MODEL_NAME=llama3.1 \
python scripts/run_local.py
```

### Async Assistant Service

For scalable async processing with Docker:

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

**See [infra/docker/README.md](infra/docker/README.md) and [docs/assistant_mode.md](docs/assistant_mode.md) for complete deployment profile documentation.**

## How to Use

### 1. Select Input Source

Choose between:
- **Demo Repo** - Bundled Mini Travel Planner (React + FastAPI)
- **Upload ZIP** - Your own repository (max 25 MB)

### 2. Generate Quest

Click "Generate Quest" to analyze the repository. After analysis, the sidebar stays available with source status, upload/generate controls, app limits, and AI Review status so you can switch sources without losing orientation.

### 3. Explore Results

Navigate through tabs:
- **Overview** - Project type, frameworks, entry points, next read, and architecture preview
- **Architecture** - Conceptual system map plus technical dependency graph
- **Files** - Repository tree and focused file/code analysis
- **API Routes** - Detected endpoints linked to their route files
- **Read** - Guided tour with one selected file preview at a time
- **Components** - Important file cards with evidence and test ideas
- **Work Plans** - Deterministic epics, tasks, and milestones
- **Agent Workflows** - Step-by-step workflows ready for IBM Bob or another coding assistant
- **Improve** - Test intelligence and onboarding quiz
- **Export** - Download Markdown onboarding guide

About/Built with IBM Bob content lives in the persistent sidebar.

### 4. Export Guide

Generate and download a comprehensive Markdown onboarding document for your team.

## Project Structure

```
repoquest/
|-- repoquest/     # Core analysis modules
|  |-- scanner.py   # File scanning and ZIP handling
|  |-- zip_safety.py  # ZIP security validation
|  |-- indicator_rules.py # Rule definitions for deterministic analysis
|  |-- detectors.py  # Framework and project detection
|  |-- import_graph.py # Dependency graph generation
|  |-- route_extractors.py # API route detection
|  |-- architecture.py # Architecture map generation
|  |-- reading_path.py # Reading path generation
|  |-- response_templates.py # Deterministic wording and guidance
|  |-- quest.py    # Component cards and quiz
|  |-- workflows.py # Work plan and workflow generation
|  |-- test_intelligence.py # Test impact and quality analysis
|  |-- assistant_*.py # Optional manual AI assistant foundation
|  |-- report.py    # Markdown report generation
|  `-- models.py    # Data models
|-- app/
|  `-- streamlit_app.py # Streamlit UI
|-- services/
|  `-- assistant_service.py # Optional async assistant/model service
|-- tests/       # Unit tests
|-- examples/
|  `-- demo_repos/   # Bundled demo repositories
|-- infra/
|  |-- local/     # Local development config
|  |-- docker/    # Optional Dockerfiles for app and assistant service
|  `-- streamlit/   # Streamlit Cloud config
|-- docs/        # Documentation
`-- scripts/      # Utility scripts
```

## Technology Stack

**Core:**
- Python 3.11+
- Streamlit (UI framework)
- AST parsing (Python imports)
- Regex patterns (JS/TS imports)

**Analysis:**
- Deterministic static analysis
- Framework heuristics
- Pattern matching
- File role classification

**Default Runtime:**
- No required LLMs or AI APIs
- No vector databases
- No embeddings
- No external credentials
- No code execution

**Optional Assistant Mode:**
- Disabled by default
- Runs AI Fusion automatically after deterministic analysis when configured, then keeps manual AI review buttons available
- Uses bounded context packs, capped snippets, citations, and validation
- Requires `REPOQUEST_AI_ENABLED=true` and a user-provided Claude API key
- Can run model work through a separate async Docker service via `REPOQUEST_ASSISTANT_SERVICE_URL`
- May send capped repository snippets to the configured provider; deterministic mode sends no snippets and makes no AI calls

## Limitations

RepoQuest is designed for small to medium-sized repositories and uses deterministic analysis:

**What it does:**
- Scans file structure and content
- Detects common frameworks and patterns
- Extracts imports and routes
- Generates reading paths and component cards

**What it doesn't do:**
- Execute code or install dependencies
- Require runtime AI/LLMs for the default workflow
- Understand complex custom patterns
- Analyze monorepos or very large codebases (>600 files)
- Provide semantic code search

**Best practices:**
- Use with repositories under 600 files
- Verify findings by reading actual code
- Use the optional AI Assistant or IBM Bob for deeper analysis
- Treat output as a starting point, not complete analysis

## IBM Bob Integration

RepoQuest was built with IBM Bob as a development partner. Bob helped with:

- Project scaffolding and structure
- Safe ZIP scanning implementation
- Framework detection rules
- Import graph and route extraction
- Streamlit UI development
- Comprehensive test generation
- Documentation and deployment setup

**Important:** RepoQuest does not use IBM Bob at runtime. Core repository evidence is deterministic and based on static file scanning, rule evaluation, pattern matching, and heuristics. When optional AI is configured, AI Fusion can reinterpret that evidence and override displayed conclusions only after citation and validation gates pass.

See [docs/bob_usage.md](docs/bob_usage.md) for details on how Bob helped during development.

## Documentation

- [Local Development Setup](infra/local/README.md)
- [Streamlit Cloud Deployment](infra/streamlit/README.md)
- [Architecture Overview](docs/architecture.md)
- [AI Assistant Mode](docs/assistant_mode.md)
- [Demo Script](docs/demo_script.md)
- [IBM Bob Usage](docs/bob_usage.md)
- [Bob Session Reports](bob_sessions/README.md)

## Contributing

This project was created for the IBM Bob Hackathon. Contributions should maintain:

- Deterministic default analysis
- Optional AI must remain disabled by default, manual-only, and evidence-cited
- Security-first approach (safe file handling)
- Simple, readable code
- Comprehensive test coverage

## License

[Add your license here]

## Acknowledgments

Built with IBM Bob for the IBM Bob Hackathon.

RepoQuest demonstrates how AI can assist development while keeping the final product deterministic, fast, and auditable.

---

*Made with Bob*
