# Local Development Setup

This guide explains how to set up and run RepoQuest locally for development.

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Latest version
- **Git:** For cloning the repository

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd repoquest
```

### 2. Create Virtual Environment

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install -r infra/local/requirements-dev.txt
```

This installs:
- Runtime dependencies (Streamlit, pandas, PyYAML)
- Development dependencies (pytest, ruff)

### 4. Run the Application

**Using the helper script:**
```bash
python scripts/run_local.py
```

**Manual command:**
```bash
streamlit run app/streamlit_app.py --server.maxUploadSize=25 --server.runOnSave=true
```

The app will open at `http://localhost:8501`

## Development Commands

### Run Tests

```bash
# Run all tests
pytest

# Run with minimal output
pytest -q

# Run specific test file
pytest tests/test_scanner.py

# Run with coverage
pytest --cov=repoquest
```

### Lint Code

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

### Type Checking

```bash
# Run mypy (if installed)
mypy repoquest/
```

## Configuration

Local development uses `infra/local/streamlit_config.toml`:

```toml
[server]
port = 8501
maxUploadSize = 25
runOnSave = true
headless = true

[client]
showErrorDetails = true

[theme]
base = "light"
```

Key settings:
- **runOnSave:** Auto-reload on file changes
- **showErrorDetails:** Show full error tracebacks
- **maxUploadSize:** 25 MB ZIP limit

## Project Structure

```
repoquest/
├── repoquest/          # Core modules
│   ├── scanner.py      # File scanning
│   ├── detectors.py    # Framework detection
│   ├── import_graph.py # Import parsing
│   ├── route_extractors.py # Route detection
│   ├── architecture.py # Graph generation
│   ├── reading_path.py # Reading path
│   ├── quest.py        # Component cards & quiz
│   ├── report.py       # Markdown generation
│   └── models.py       # Data models
├── app/
│   └── streamlit_app.py # UI
├── tests/              # Unit tests
├── examples/
│   └── demo_repos/     # Demo repositories
└── infra/
    └── local/          # Local config
```

## Development Workflow

### 1. Make Changes

Edit files in `repoquest/` or `app/`

### 2. Test Changes

```bash
# Run relevant tests
pytest tests/test_scanner.py

# Run all tests
pytest -q
```

### 3. Lint Code

```bash
ruff check .
```

### 4. Test in UI

The app auto-reloads when files change (if `runOnSave=true`)

### 5. Commit Changes

```bash
git add .
git commit -m "Description of changes"
```

## Common Tasks

### Add a New Framework Detector

1. Edit `repoquest/framework_rules.py`
2. Add detection logic to `repoquest/detectors.py`
3. Add tests to `tests/test_detectors.py`
4. Run tests: `pytest tests/test_detectors.py`

### Add a New Route Extractor

1. Edit `repoquest/route_extractors.py`
2. Add extraction logic for the framework
3. Add tests to `tests/test_route_extractors.py`
4. Run tests: `pytest tests/test_route_extractors.py`

### Modify the UI

1. Edit `app/streamlit_app.py`
2. Save and check auto-reload
3. Test all tabs and interactions

### Update Documentation

1. Edit relevant `.md` files in `docs/`
2. Update `README.md` if needed
3. Commit documentation changes

## Troubleshooting

### Port Already in Use

If port 8501 is busy:

```bash
# Find process using port
lsof -i :8501  # Mac/Linux
netstat -ano | findstr :8501  # Windows

# Kill process or use different port
streamlit run app/streamlit_app.py --server.port=8502
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r infra/local/requirements-dev.txt --force-reinstall

# Verify installation
pip list | grep streamlit
```

### Test Failures

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_scanner.py::test_scan_directory -v

# Show print statements
pytest -s
```

### Streamlit Cache Issues

```bash
# Clear Streamlit cache
streamlit cache clear
```

## Known Limitations

### Local Development

- File upload limited to 25 MB
- Maximum 600 files scanned per repository
- Binary files are skipped
- Large files (>512 KB) are truncated

### Performance

- Large repositories may take longer to scan
- Graph rendering limited to 80 nodes
- Text previews limited to 20,000 characters

## Next Steps

After local setup:
- Explore the demo repository analysis
- Try uploading your own small repository
- Run the test suite
- Read the architecture documentation

## Additional Resources

- [Main README](../../README.md)
- [Architecture Documentation](../../docs/architecture.md)
- [Streamlit Cloud Deployment](../streamlit/README.md)
- [Demo Script](../../docs/demo_script.md)

---

*This guide was created with IBM Bob's assistance.*