# RepoQuest

**Turn unfamiliar repos into guided onboarding journeys**

RepoQuest helps developers onboard to small codebases faster by converting repository structure into a guided quest: project fingerprint, architecture map, reading path, component cards, quiz, and Bob-ready follow-up prompts.

## What is RepoQuest?

RepoQuest is a deterministic repository onboarding mapper for small prototype-sized codebases. It analyzes repository structure and generates:

- 🔍 **Project Fingerprint** - Detects project type, frameworks, and entry points
- 🏗️ **Architecture Map** - Visualizes component relationships and dependencies
- 📖 **Reading Path** - Suggests a 30-minute guided tour through key files
- 🎯 **Component Cards** - Detailed information about important files with test ideas
- 🧪 **Test Analysis** - Identifies test files and suggests additional test coverage
- 🎮 **Onboarding Quiz** - Verifies understanding with interactive questions
- 📝 **Markdown Export** - Generates comprehensive onboarding documentation

## Why RepoQuest?

Developers waste time figuring out where to start in unfamiliar codebases. RepoQuest solves this by:

- **Fast Analysis** - Scans and analyzes repositories in seconds
- **Deterministic** - Uses static analysis and heuristics, no AI runtime required
- **Safe** - Validates ZIP uploads, never executes uploaded code
- **Actionable** - Provides specific next steps and IBM Bob prompts
- **Exportable** - Generates standalone Markdown guides for team onboarding

## Features

### Core Analysis
- ✅ Framework detection (React, FastAPI, Flask, Express, Next.js, Django, Streamlit)
- ✅ Project type classification (full-stack, frontend, backend, CLI, library)
- ✅ Entry point identification
- ✅ API route extraction (FastAPI, Flask, Express)
- ✅ Import/dependency graph generation
- ✅ Test file detection and analysis

### Onboarding Tools
- ✅ Prioritized reading path with time estimates
- ✅ Component cards with connections and test ideas
- ✅ Interactive quiz for knowledge verification
- ✅ Documentation and config file previews
- ✅ IBM Bob prompt suggestions for deeper exploration

### Security
- ✅ ZIP slip protection
- ✅ Path traversal prevention
- ✅ File size limits (25 MB max)
- ✅ Binary file detection
- ✅ No code execution
- ✅ No dependency installation

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

## How to Use

### 1. Select Input Source

Choose between:
- **Demo Repo** - Bundled Mini Travel Planner (React + FastAPI)
- **Upload ZIP** - Your own repository (max 25 MB)

### 2. Generate Quest

Click "Generate Onboarding Quest" to analyze the repository.

### 3. Explore Results

Navigate through tabs:
- **Overview** - Project type, frameworks, entry points
- **Architecture Map** - Visual component relationships
- **Reading Path** - Guided 30-minute tour
- **Components** - Detailed file cards with test ideas
- **Tests** - Test file analysis and suggestions
- **Quest & Quiz** - Interactive onboarding verification
- **Documentation** - Preview and generate reports
- **Export** - Download Markdown onboarding guide

### 4. Export Guide

Generate and download a comprehensive Markdown onboarding document for your team.

## Project Structure

```
repoquest/
├── repoquest/          # Core analysis modules
│   ├── scanner.py      # File scanning and ZIP handling
│   ├── zip_safety.py   # ZIP security validation
│   ├── detectors.py    # Framework and project detection
│   ├── import_graph.py # Dependency graph generation
│   ├── route_extractors.py # API route detection
│   ├── architecture.py # Architecture map generation
│   ├── reading_path.py # Reading path generation
│   ├── quest.py        # Component cards and quiz
│   ├── report.py       # Markdown report generation
│   └── models.py       # Data models
├── app/
│   └── streamlit_app.py # Streamlit UI
├── tests/              # Unit tests
├── examples/
│   └── demo_repos/     # Bundled demo repositories
├── infra/
│   ├── local/          # Local development config
│   └── streamlit/      # Streamlit Cloud config
├── docs/               # Documentation
└── scripts/            # Utility scripts
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

**No Runtime Dependencies:**
- ❌ No LLMs or AI APIs
- ❌ No vector databases
- ❌ No embeddings
- ❌ No external credentials
- ❌ No code execution

## Limitations

RepoQuest is designed for small to medium-sized repositories and uses deterministic analysis:

**What it does:**
- ✅ Scans file structure and content
- ✅ Detects common frameworks and patterns
- ✅ Extracts imports and routes
- ✅ Generates reading paths and component cards

**What it doesn't do:**
- ❌ Execute code or install dependencies
- ❌ Use runtime AI/LLMs
- ❌ Understand complex custom patterns
- ❌ Analyze monorepos or very large codebases (>600 files)
- ❌ Provide semantic code search

**Best practices:**
- Use with repositories under 600 files
- Verify findings by reading actual code
- Use IBM Bob for deeper analysis
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

**Important:** RepoQuest does not use IBM Bob (or any AI) at runtime. All analysis is deterministic and based on static file scanning, pattern matching, and heuristics.

See [docs/bob_usage.md](docs/bob_usage.md) for details on how Bob helped during development.

## Documentation

- [Local Development Setup](infra/local/README.md)
- [Streamlit Cloud Deployment](infra/streamlit/README.md)
- [Architecture Overview](docs/architecture.md)
- [Demo Script](docs/demo_script.md)
- [IBM Bob Usage](docs/bob_usage.md)
- [Bob Session Reports](bob_sessions/README.md)

## Contributing

This project was created for the IBM Bob Hackathon. Contributions should maintain:

- Deterministic analysis (no runtime AI)
- Security-first approach (safe file handling)
- Simple, readable code
- Comprehensive test coverage

## License

[Add your license here]

## Acknowledgments

Built with IBM Bob for the IBM Bob Hackathon.

RepoQuest demonstrates how AI can assist development while keeping the final product deterministic, fast, and auditable.

---

*Made with Bob* 🤖