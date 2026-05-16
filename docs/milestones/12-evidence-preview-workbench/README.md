# Milestone 12 - Reading And Evidence Workbench

Purpose: replace path-only reading guidance with actual docs/code previews and concrete improvement guidance.

MVP 2 phase: Deterministic Code Assistant.

## Goal

Reading Path should help a developer understand and improve the repo without forcing them to open every file manually.

## Planned Interface

```python
@dataclass
class ReadingPathDetail:
    path: str
    summary: str
    snippet: str
    what_to_understand: list[str]
    improvement_opportunities: list[str]
    related_tasks: list[str]
    bob_prompt: str
```

## Required Reading Path Sections

Each reading path item should show:

- **Read:** short source or documentation preview from the file.
- **Understand:** what concepts, flows, routes, props, models, or config to look for.
- **Improve:** concrete improvement opportunities inferred from deterministic evidence.
- **Ask Bob:** a copyable Bob/AI-agent prompt for that file.

## Preview Requirements

- README and docs files show meaningful Markdown excerpts.
- Backend route files show route decorators and handler signatures.
- Frontend pages/components show imports, props, and component entry points.
- API clients show endpoint URLs and request functions.
- Models show class/schema definitions.
- Tests show imports, assertions, and likely coverage hints.
- Large files are capped and clearly labeled as partial previews.
- Binary or skipped files are never displayed.

## Improvement Guidance Examples

- Route file: add edge-case tests, document endpoint behavior, validate errors.
- API client: handle failures, timeouts, and response typing.
- Frontend component: test empty states, accessibility, and event handling.
- Model/schema: document fields and validation.
- README/docs: add missing endpoints, setup notes, or architecture summary.

## Tests/Checks

- Reading path renders snippets/previews for README, backend route, frontend page, API client, and test file in the demo repo.
- Each reading item includes Read, Understand, Improve, and Ask Bob sections.
- Snippets are deterministic and capped.
- Improvement suggestions cite file paths or detected evidence.

## Exit Criteria

- Reading Path becomes a useful workbench, not a list of file paths.
- A developer can use the reading path to understand and improve the app.
