# Milestone 7 - Streamlit Demo UI

Purpose: track the Streamlit interface and 1-2 minute demo flow work.

## Goal

Make the app demoable in 1-2 minutes.

Milestones 1-6 produced the core analysis objects. This milestone turned them into a clean product experience with a focused first screen, tabbed exploration, safe previews, and deterministic documentation generation.

## Required Files

- `app/streamlit_app.py`

## Proposed Final Tab Layout

- Overview
- Architecture Map
- Reading Path
- Components
- Tests
- Quest & Quiz
- Documentation
- Export
- Built with IBM Bob

The extra Tests and Documentation tabs are intentional:

- Tests keeps test files out of the main dependency graph while still making them useful for onboarding.
- Documentation gives a place for README/code previews and generated guide previews before export.

## Implementation Tasks

- Add input mode for demo repo and ZIP upload.
- Add a single "Generate Quest" action.
- Add tabs: Overview, Architecture Map, Reading Path, Components, Tests, Quest & Quiz, Documentation, Export, Built with IBM Bob.
- Show limits in the sidebar.
- Keep the first result screen focused on project type and framework evidence.
- Use `st.graphviz_chart` for graphs.
- Use `st.download_button` for Markdown export.
- Include a Built with IBM Bob section without implying runtime AI usage.
- Keep the demo flow clear before adding polish.
- Add a "Generate documentation" button that builds the Markdown guide/report from the current deterministic analysis result.
- Add short code examples/evidence previews in expanders. Keep previews capped and never display large full files.
- Remove test files from the default dependency graph. Surface them in the Tests tab instead.
- Add documentation previews for README, likely docs files, config files, and generated onboarding sections.
- Add route evidence previews with decorator snippets where available.
- Add a reset/new analysis control so a ZIP error or demo rerun does not leave stale state.
- Add empty states for each tab so the app remains understandable before the first analysis.

## Tab Details

### Overview

- Project type and confidence.
- Framework badges and evidence.
- Entry points with one-line reasons.
- Key folders.
- Scan warnings and limits.

### Architecture Map

- Human-friendly architecture map first.
- Technical dependency graph second.
- Dependency path summary, for example:

```text
main.tsx -> App.tsx -> TripsPage.tsx -> api.ts -> backend/routes/trips.py
```

- Legend for colors and the dashed API boundary edge.
- Feature routes grouped ahead of root/health utility routes.

### Reading Path

- Ordered 30-minute reading path.
- Estimated minutes.
- Reason and "what to look for" copy.
- Quick action to open the related component card if Streamlit state handling stays simple.

### Components

- Role grouping or filtering if useful for scanning.
- Expandable component cards.
- Connections, detected routes/items, test ideas, and optional assistant actions.
- Short code snippets for evidence where available.

Example card preview:

```text
backend/routes/trips.py
Likely role: backend route
Detected evidence: @router.get("/trips"), @router.post("/trips")
Connected to: backend/services/recommendations.py, backend/models/trip.py
```

### Tests

- Detected test files.
- Likely test framework hints, such as pytest from `test_*.py`.
- App files targeted by tests, based on imports.
- Suggested next tests from component cards.
- Keep this tab separate from the main dependency graph to avoid making the architecture map look test-first.

Example:

```text
backend/tests/test_trips.py
Imports: backend/main.py
Likely covers: FastAPI route behavior
Suggested next tests: missing destination, delete nonexistent trip, recommendation fallback
```

### Quest & Quiz

- Onboarding checklist.
- Deterministic quiz questions.
- Answer reveal and score.
- No chat box.

### Documentation

- README preview.
- Documentation/config preview table.
- Generated onboarding guide preview.
- "Generate documentation" button that refreshes the deterministic Markdown output.
- Optional "copy AI Assistant action" controls for follow-up prompts, if Streamlit supports it cleanly.

### Export

- Markdown preview.
- Download button.
- Warnings and limitations included in the exported report.

### Built With IBM Bob

- Summarize how Bob helped during development.
- Link/reference `docs/bob_usage.md` and `bob_sessions/`.
- State clearly that RepoQuest does not use Bob or external AI tools at runtime.

## Tests/Checks

- Demo repo flow produces useful output within seconds.
- Invalid ZIP produces a friendly error.
- Empty/unknown repo still produces a cautious fallback.
- No UI text mentions private development tools or hidden review process.
- The main dependency graph does not show test files by default.
- The Tests tab shows detected test files and their likely targets.
- Documentation tab previews short file/report snippets without dumping large files.
- Generate documentation button produces or refreshes the same deterministic report for the same input.
- Route and code examples are short, capped, and tied to scanned evidence.

## Exit Criteria

- Judge can understand the product in one short live demo.
- Main tabs match the required RepoQuest flow.
- Architecture and dependency graphs render in the Architecture Map tab as part of the final tabbed UI.
- Tests and documentation are visible as first-class onboarding aids without turning RepoQuest into a chatbot.
