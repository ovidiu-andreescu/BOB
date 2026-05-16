# Milestone 8 - Markdown Export And Documentation

Purpose: track Markdown export, README, docs, and submission documentation work.

## Goal

Finish the public project story and submission-ready documentation.

The app should also make documentation generation feel like part of the product, not only a hidden export implementation.

## Required Files

- `repoquest/report.py`
- `tests/test_report.py`
- `README.md`
- `docs/bob_usage.md`
- `docs/demo_script.md`
- `docs/architecture.md`
- `infra/local/README.md`
- `infra/streamlit/README.md`
- `bob_sessions/README.md`

## Implementation Tasks

- Generate an exportable Markdown onboarding guide.
- Include summary, detected project type, frameworks, entry points, architecture summary, routes, reading path, component cards, checklist, quiz, AI Assistant actions, and warnings.
- Include a Tests section in the report with detected test files, likely targets, and suggested next tests.
- Include a Documentation/Previews section in the app that previews README/docs/config snippets and the generated report before download.
- Add a visible "Generate documentation" button in the UI. The button should use the already computed deterministic analysis result and should not call any runtime AI.
- Add short code examples/evidence snippets to the report where useful, especially for routes, imports, and entry points.
- Document local development.
- Document Streamlit Cloud deployment.
- Document how IBM Bob helped during development.
- Add the authentic Bob session report placement instructions.
- Keep the public story focused on IBM Bob and deterministic static analysis.

## Suggested Report Structure

```text
# RepoQuest Onboarding Guide

## Summary
## Detected Project Type
## Frameworks and Evidence
## Key Entry Points
## Architecture Map Summary
## Routes Detected
## Dependency Summary
## Tests Detected
## 30-Minute Reading Path
## Component Cards
## Documentation and Config Previews
## Onboarding Checklist
## Quiz Questions
## Warnings and Limitations
```

## Code Example Guidelines

- Use scanned source snippets as evidence, not invented behavior.
- Keep snippets short, typically 3-8 lines.
- Include file path and, if available, line numbers.
- Prefer examples that explain why RepoQuest made a claim.
- Do not include full files or large generated code blocks.

Good examples:

```python
@router.get("/trips")
async def list_trips():
 ...
```

```tsx
import TripsPage from "./pages/TripsPage";
```

```python
from fastapi import FastAPI
```

## Documentation Preview Guidelines

- Preview README first when present.
- Preview docs files before config files.
- Preview config files such as `package.json`, `requirements.txt`, `pyproject.toml`, and `vite.config.ts` only when they support framework or setup evidence.
- Cap previews with `MAX_TEXT_PREVIEW_CHARS` or a smaller UI-specific preview limit.
- Make the preview clearly labeled as partial.

## Button Behavior

The "Generate documentation" button should:

- Require a completed analysis result.
- Build the Markdown report from in-memory deterministic data.
- Refresh the preview in the Documentation tab.
- Enable the download button in the Export tab.
- Show a friendly message if no analysis has been run yet.

## Tests/Checks

- Report includes all required sections.
- Report includes demo framework evidence and routes.
- Report includes detected tests separately from the main dependency graph.
- Report includes short code examples/evidence for at least one route and one frontend import.
- README includes local setup, Streamlit Cloud setup, limitations, and no external runtime AI statement.
- Bob session instructions say to place authentic exported reports in `bob_sessions/`.
- Documentation preview does not display full large files.

## Exit Criteria

- Project is understandable from README and demo script.
- Exported guide is useful as a standalone onboarding handoff.
- The app can generate, preview, and download documentation without any external AI/API dependency.
