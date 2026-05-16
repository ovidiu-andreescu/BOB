# Milestone 15 - Testable AI Assistant Foundation

Purpose: add an optional, testable AI layer for code assistance without weakening deterministic RepoQuest.

MVP 2 phase: Optional AI Code Assistant.

## Goal

Introduce assistant mode as a disabled-by-default capability that can generate summaries, docs, tasks, workflows, and code recommendations from deterministic RepoQuest context.

## Current Status

Implemented foundation:

- `.env.example` documents `REPOQUEST_AI_ENABLED`, `CLAUDE_API_KEY`, and `CLAUDE_MODEL`.
- Local `.env` and Streamlit secrets are supported.
- Assistant provider layer includes disabled, mock, and Claude providers.
- Claude calls use the standard library HTTP client and a local certificate bundle when available to avoid common macOS certificate failures.
- Context builders create bounded packs from deterministic RepoQuest data.
- Validation rejects empty responses, nonexistent citations, and unsafe execution claims.
- UI assistant actions are manual-only and appear across Overview, Architecture, Reading Path, Components, Tests, Work Plans, Documentation, and Export where relevant.
- Deterministic analysis still completes with AI disabled, missing keys, network errors, or validation failures.

## Guardrails

- Assistant mode is off by default.
- The default app must work without secrets.
- No uploaded code is executed.
- No uploaded dependencies are installed.
- Only bounded context packs and capped snippets are sent to a provider.
- AI responses are labeled AI-assisted.
- Deterministic findings remain visible and usable without AI.
- Invalid AI output fails closed and is not shown as trusted guidance.

## Provider Strategy

Define an adapter interface and require a mock provider for tests:

```python
class AssistantProvider(Protocol):
  def generate(self, request: AssistantRequest) -> AssistantResponse:
   ...
```

Required providers:

- `DisabledAssistantProvider`: always available and returns a friendly disabled state.
- `MockAssistantProvider`: deterministic fixture responses for tests.
- `ClaudeAssistantProvider`: optional real provider when configured.

## Configuration

Local:

```bash
cp .env.example .env
```

Then set:

```bash
REPOQUEST_AI_ENABLED=true
CLAUDE_API_KEY=your_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
```

Streamlit Cloud:

```toml
REPOQUEST_AI_ENABLED = "true"
CLAUDE_API_KEY = "your_key_here"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
```

Do not commit `.env` or secrets.

## Schema-Driven Outputs

AI mode should use structured schemas for:

- Application summaries.
- Component docs pages.
- Architecture graph and selected-node explanations.
- Reading path file explanations.
- Epics, tasks, and milestones.
- Agent workflows.
- Test plans.
- Documentation guide notes.
- Follow-up questions.

## Validation Rules

- Output must parse against the expected schema.
- Referenced file paths must exist in the current snapshot.
- Recommendations must cite evidence paths/snippets.
- Output must not claim tests were run unless the app actually ran a verification command.
- Output must not ask RepoQuest to execute uploaded code.
- Missing evidence downgrades or hides the suggestion.

## Tests/Checks

- App runs normally with assistant mode disabled.
- Missing API key does not crash.
- Mock provider returns schema-valid outputs.
- Malformed mock output is rejected.
- Output referencing nonexistent files is rejected.
- Output without evidence is not shown as trusted.

## Exit Criteria

- Assistant mode is safe to enable experimentally.
- AI is testable locally without network access.
- AI buttons are manual-only and never run during quest generation.
- Deterministic workbench behavior does not depend on AI.
- Certificate/network errors are shown as assistant errors and do not break the rest of the app.
