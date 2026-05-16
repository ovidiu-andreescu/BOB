# RepoQuest Architecture

This document describes the architecture and design of RepoQuest.

## Overview

RepoQuest is a deterministic repository onboarding mapper built with Python and Streamlit. It analyzes small codebases using static analysis and generates guided onboarding documentation.

## Design Principles

1. **Deterministic** - All analysis is based on static file scanning, pattern matching, and heuristics. No runtime AI or LLMs.
2. **Security-First** - Safe file handling with ZIP validation, path checking, and no code execution.
3. **Simple** - Readable code, focused modules, minimal dependencies.
4. **Testable** - Comprehensive unit tests with fixtures and edge case coverage.
5. **Exportable** - Generate standalone Markdown guides that work without the app.

## Architecture Layers

### 1. Input Layer

**Purpose:** Safely acquire repository content

**Components:**
- `repoquest/zip_safety.py` - ZIP security validation
- `repoquest/scanner.py` - Directory and ZIP scanning
- `repoquest/sample_loader.py` - Demo repository loading

**Security Features:**
- ZIP slip protection (rejects `..` and absolute paths)
- File size limits (25 MB ZIP, 512 KB per file)
- Binary file detection and skipping
- Safe path resolution
- No code execution

**Output:** `RepositorySnapshot` with scanned files

### 2. Detection Layer

**Purpose:** Identify frameworks, project type, and structure

**Components:**
- `repoquest/detectors.py` - Framework and project detection
- `repoquest/framework_rules.py` - Detection rule definitions

**Detection Methods:**
- File structure patterns (e.g., `frontend/`, `backend/`)
- Config file presence (e.g., `package.json`, `pyproject.toml`)
- Import statements (e.g., `from fastapi import FastAPI`)
- File naming conventions (e.g., `main.py`, `App.tsx`)
- Decorator patterns (e.g., `@app.get`, `@router.post`)

**Output:** `ProjectFingerprint` with frameworks, entry points, and confidence scores

### 3. Analysis Layer

**Purpose:** Extract relationships and structure

**Components:**
- `repoquest/import_graph.py` - Import parsing and graph building
- `repoquest/route_extractors.py` - API route detection
- `repoquest/architecture.py` - Graph generation

**Analysis Methods:**
- **Python imports:** AST parsing for accurate import extraction
- **JS/TS imports:** Regex patterns for `import` and `require` statements
- **Route extraction:** Pattern matching for FastAPI, Flask, Express decorators
- **Graph generation:** DOT format for Streamlit visualization

**Output:** `ImportEdge` list, `RouteInfo` list, DOT graphs

### 4. Synthesis Layer

**Purpose:** Generate actionable onboarding content

**Components:**
- `repoquest/reading_path.py` - Reading path generation
- `repoquest/quest.py` - Component cards and quiz generation

**Generation Logic:**
- **Reading path:** Priority-based ordering (README → entry points → routes → services → models → frontend → tests)
- **Component cards:** Role-based card generation with connections, test ideas, and Bob prompts
- **Quiz:** Repository-specific questions based on structure and detected components

**Output:** `ReadingPathItem` list, `ComponentCard` list, `QuizQuestion` list

### 5. Report Layer

**Purpose:** Generate exportable documentation

**Components:**
- `repoquest/report.py` - Markdown report generation

**Report Sections:**
- Summary and project type
- Frameworks with evidence
- Entry points with code previews
- Architecture map summary
- Detected routes with examples
- Dependency summary
- Test file analysis
- Reading path with snippets
- Component cards
- Documentation previews
- Onboarding checklist
- Quiz questions
- IBM Bob prompts
- Warnings and limitations

**Output:** Markdown string

### 6. UI Layer

**Purpose:** Interactive web interface

**Components:**
- `app/streamlit_app.py` - Streamlit application

**UI Features:**
- Input selection (demo repo or ZIP upload)
- Analysis trigger and progress
- Tabbed result display
- Interactive graphs with Graphviz
- Quiz with scoring
- Documentation preview
- Markdown export with download

## Data Flow

```
User Input (Demo/ZIP)
  ↓
ZIP Safety Validation
  ↓
File Scanning
  ↓
RepositorySnapshot
  ↓
Framework Detection → ProjectFingerprint
  ↓
Import Parsing → ImportEdge list
Route Extraction → RouteInfo list
  ↓
Architecture Map Generation → DOT graphs
  ↓
Reading Path Generation → ReadingPathItem list
Component Card Generation → ComponentCard list
Quiz Generation → QuizQuestion list
  ↓
Report Generation → Markdown string
  ↓
UI Display & Export
```

## Data Models

All data models are defined in `repoquest/models.py` as dataclasses:

- `FileInfo` - Scanned file information
- `RepositorySnapshot` - Complete scan result
- `FrameworkFinding` - Detected framework with evidence
- `ProjectFingerprint` - Project classification
- `ImportEdge` - Import relationship
- `RouteInfo` - API route information
- `ReadingPathItem` - Reading path entry
- `ComponentCard` - Component information card
- `QuizQuestion` - Quiz question with answer

## Configuration

Configuration constants are defined in `repoquest/config.py`:

- `MAX_ZIP_SIZE_MB = 25` - Maximum ZIP upload size
- `MAX_FILES_SCANNED = 600` - Maximum files to scan
- `MAX_FILE_SIZE_BYTES = 512_000` - Maximum individual file size
- `MAX_TEXT_PREVIEW_CHARS = 20_000` - Maximum text preview length
- `MAX_GRAPH_NODES = 80` - Maximum graph nodes
- `MAX_READING_PATH_ITEMS = 9` - Maximum reading path items
- `MAX_COMPONENT_CARDS = 30` - Maximum component cards
- `MAX_QUIZ_QUESTIONS = 8` - Maximum quiz questions

## Deployment Profiles

### Local Development (`infra/local/`)

- Full development dependencies (pytest, ruff)
- Local Streamlit config with hot reload
- Detailed error messages
- Port 8501

### Streamlit Cloud (`infra/streamlit/`)

- Minimal runtime dependencies
- Production Streamlit config
- Limited error details
- Automatic port assignment

## Security Considerations

### ZIP Upload Safety

1. **Path Validation:**
   - Reject absolute paths
   - Reject paths containing `..`
   - Verify resolved paths stay within target directory

2. **Size Limits:**
   - 25 MB maximum ZIP size
   - 512 KB maximum per file
   - 600 file scan limit

3. **Content Safety:**
   - Skip binary files
   - Skip unsupported extensions
   - Safe UTF-8 decoding with fallback

4. **Execution Prevention:**
   - Never execute uploaded code
   - Never install dependencies
   - Never import uploaded modules

### No Runtime AI

RepoQuest does not:
- Call external AI APIs
- Use LLMs or embeddings
- Require credentials or secrets
- Make hidden network requests
- Store or transmit user data

All analysis is local, deterministic, and auditable.

## Testing Strategy

### Unit Tests

Each module has corresponding tests in `tests/`:
- `test_zip_safety.py` - ZIP validation and security
- `test_scanner.py` - File scanning
- `test_detectors.py` - Framework detection
- `test_import_graph.py` - Import parsing
- `test_route_extractors.py` - Route extraction
- `test_architecture.py` - Graph generation
- `test_reading_path.py` - Reading path generation
- `test_quest.py` - Component cards and quiz
- `test_report.py` - Report generation

### Test Coverage

- Normal operation paths
- Edge cases (empty repos, large files, etc.)
- Security scenarios (ZIP slip, path traversal)
- Error handling
- Data model validation

### Fixtures

Common test data is defined in `tests/fixtures/`:
- Sample files for scanning
- Test repositories
- Mock data for analysis

## Performance Considerations

### Scanning

- Ignore common large directories (node_modules, .git, etc.)
- Skip binary files early
- Limit file preview size
- Stop at file count limit

### Graph Generation

- Limit graph nodes to prevent rendering issues
- Filter test files from main dependency graph
- Summarize large graphs
- Use simple DOT format

### UI Responsiveness

- Show progress spinners during analysis
- Use Streamlit caching where appropriate
- Lazy load tab content
- Limit preview sizes

## Limitations

### By Design

- Small to medium repositories only (< 600 files)
- Common frameworks only (no custom pattern detection)
- Heuristic-based (not semantic understanding)
- English-language documentation focus

### Technical

- No monorepo support
- No multi-language project analysis
- No runtime code analysis
- No dependency resolution
- No semantic code search

## Future Considerations

Potential improvements (not in current scope):

- Additional framework support
- Custom detection rule configuration
- Larger repository support with sampling
- Multi-language documentation
- Export to other formats (PDF, HTML)
- Integration with development tools

## Conclusion

RepoQuest demonstrates that useful repository analysis can be achieved with deterministic static analysis, without requiring runtime AI or complex infrastructure.

The architecture prioritizes:
- Security and safety
- Simplicity and maintainability
- Deterministic and auditable results
- Actionable onboarding guidance

---

*This architecture document was created with IBM Bob's assistance.*
