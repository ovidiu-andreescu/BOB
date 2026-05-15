# RepoQuest

Turn an unfamiliar repository into a guided onboarding journey.

## What is RepoQuest?

RepoQuest is a deterministic Streamlit web app that analyzes small codebases and generates:

- 🔍 Repository fingerprint and project type detection
- 🏗️ Framework detection (React/Vite, FastAPI, etc.)
- 🗺️ Architecture maps and dependency graphs
- 📖 30-minute guided reading path
- 📋 Component cards with test ideas
- ✅ Onboarding quiz
- 📝 Exportable Markdown guide
- 🤖 IBM Bob-ready follow-up prompts

## Current Status: Checkpoint 1 - File Inventory

This checkpoint demonstrates:
- ✅ Loading bundled demo repository (mini_travel_planner)
- ✅ Safe file scanning with ignore rules
- ✅ Basic file role classification
- ✅ Interactive file table display
- ✅ CSV export functionality

**Coming next:** Framework detection, route extraction, and architecture mapping!

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd BOB
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Locally

Run the app with:
```bash
python scripts/run_local.py
```

Or manually:
```bash
streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Demo Repository

The bundled demo repository is `mini_travel_planner`, a small full-stack web app with:

**Frontend:**
- React 18 + Vite
- TypeScript
- Component-based architecture

**Backend:**
- FastAPI
- Python 3.11+
- RESTful API with routes, services, and models

## Project Structure

```
repoquest/          # Core analysis modules
  __init__.py
  config.py         # Configuration constants
  models.py         # Data models
  scanner.py        # Repository scanner
  sample_loader.py  # Demo repo loader

app/
  streamlit_app.py  # Main Streamlit application

examples/
  demo_repos/
    mini_travel_planner/  # Bundled demo repository

infra/
  streamlit/
    requirements.txt      # Runtime dependencies

scripts/
  run_local.py      # Local launch script

requirements.txt    # Root dependencies file
```

## Features (Roadmap)

- [x] Repository scanning
- [x] File inventory
- [ ] Framework detection (React/Vite, FastAPI)
- [ ] Route extraction
- [ ] Import graph analysis
- [ ] Architecture visualization
- [ ] Reading path generation
- [ ] Component cards
- [ ] Onboarding quiz
- [ ] Markdown export
- [ ] ZIP upload support

## Limitations

- Designed for small prototype-sized codebases (< 600 files)
- No runtime AI/LLM dependencies
- Deterministic static analysis only
- Framework detection limited to React/Vite and FastAPI in MVP

## Built for IBM Bob Hackathon

RepoQuest is built as part of the IBM Bob Hackathon to demonstrate how deterministic code analysis can create valuable onboarding experiences without requiring runtime AI dependencies.

## License

MIT
