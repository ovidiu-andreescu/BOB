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
  assistant_action: str
```

## Required Reading Path Sections

Each reading path item should show:

- **Read:** short source or documentation preview from the file.
- **Understand:** what concepts, flows, routes, props, models, or config to look for.
- **Improve:** concrete improvement opportunities inferred from deterministic evidence.
- **AI Assistant Action:** an optional manual assistant action for that file when AI mode is configured.

## Preview Requirements

- README and docs files show meaningful Markdown excerpts.
- Backend route files show route decorators and handler signatures.
- Frontend pages/components show imports, props, and component entry points.
- API clients show endpoint URLs and request functions.
- Models show class/schema definitions.
- Tests show imports, assertions, and likely coverage hints.
- Large files are capped and clearly labeled as partial previews.
- Binary or skipped files are never displayed.

## UI Requirements for File Previews

The Reading Path tab should provide a real reader surface rather than path-only guidance:

- **Syntax-highlighted code previews** using lightweight deterministic highlighting where needed
- **Light/dark preview mode toggle** placed inside the code block toolbar
- **Fullscreen popup viewer** opened by an expansion icon, not a radio/toggle
- **Scrollable preview area** with a fixed max height so files do not consume the full page
- **Buffered preview loading**: compact preview by default, larger capped buffer in fullscreen
- **Respect existing scan limits** - cap file previews using `MAX_TEXT_PREVIEW_CHARS` and `MAX_FILE_SIZE_BYTES`
- **Never execute uploaded files** - all previews are read-only text display
- **Keep preview controls visually attached to the code block** rather than in a separate metadata container
- **Link to AI Assistant actions** for deeper analysis of each file when optional AI is enabled

The goal is to make Reading Path a real workbench where developers can read, understand, and get actionable improvement suggestions without leaving the app.

## Improvement Guidance Examples

- Route file: add edge-case tests, document endpoint behavior, validate errors.
- API client: handle failures, timeouts, and response typing.
- Frontend component: test empty states, accessibility, and event handling.
- Model/schema: document fields and validation.
- README/docs: add missing endpoints, setup notes, or architecture summary.

## Tests/Checks

- Reading path renders snippets/previews for README, backend route, frontend page, API client, and test file in the demo repo.
- Each reading item includes Read, Understand, Improve, and AI Assistant Action sections.
- Snippets are deterministic and capped.
- Improvement suggestions cite file paths or detected evidence.
- Plain text previews are read-only.
- Fullscreen code viewer opens as a popup and uses a larger capped buffer.
- Theme switching works inside the code viewer.

## Exit Criteria

- Reading Path becomes a useful workbench, not a list of file paths.
- A developer can use the reading path to understand and improve the app.
