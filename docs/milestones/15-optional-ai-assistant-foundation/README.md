# Milestone 15 - Testable AI Assistant Foundation

Purpose: add an optional, testable AI layer for code assistance without weakening deterministic RepoQuest, and integrate it into the workspace as a first-class review layer.

MVP 2 phase: Optional AI Code Assistant. In progress.

## Goal

Introduce assistant mode as a disabled-by-default capability that can generate summaries, docs, tasks, workflows, and code recommendations from deterministic RepoQuest context.

Milestone 15 is not complete until AI is visible as a coherent review layer in the product shell and core workflows, not only as scattered manual buttons.

## Implementation Prompt

Use [IMPLEMENTATION_PROMPT.md](IMPLEMENTATION_PROMPT.md) as the paste-ready prompt for IBM Bob or another coding agent.

## Current Status

Implemented foundation pieces:

- `.env.example` documents `REPOQUEST_AI_ENABLED`, `CLAUDE_API_KEY`, and `CLAUDE_MODEL`.
- Local `.env` and Streamlit secrets are supported.
- Assistant provider layer includes disabled, mock, and Claude providers.
- Assistant provider layer can optionally route requests through a separate async assistant service.
- Claude calls use the standard library HTTP client and a local certificate bundle when available to avoid common macOS certificate failures.
- Docker Compose can run Streamlit and the assistant service as separate containers.
- The assistant service exposes `POST /jobs`, `GET /jobs/{job_id}`, and `GET /health`.
- Context builders create bounded packs from deterministic RepoQuest data.
- Validation rejects empty responses, nonexistent citations, and unsafe execution claims.
- UI assistant actions are manual-only and appear across Overview, Architecture, Files, API Routes, Read, Components, Work Plans, Agent Workflows, Improve, and Export where relevant.
- Deterministic analysis still completes with AI disabled, missing keys, network errors, or validation failures.

Not yet included in this foundation:

- A fully integrated AI Review workspace experience.
- A compact shell-level AI state that avoids repeated disabled messages across content panels.
- Clear separation between deterministic findings and AI review overlays throughout the UI.
- Local model providers such as Ollama, llama.cpp server, LM Studio, or OpenAI-compatible local endpoints.
- Full schema-specific responses for docs pages, task plans, and code recommendations.
- Persistent assistant job storage.

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
- `AssistantServiceProvider`: optional client for the async assistant service.

Future providers belong in Milestone 16:

- `LocalModelAssistantProvider`: OpenAI-compatible HTTP provider for local model servers.
- `OllamaAssistantProvider`: optional convenience wrapper if direct Ollama support is preferred.

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

Async service mode:

```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765
REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock
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

- Assistant foundation exists and is safe to enable experimentally.
- AI is testable locally without network access.
- AI state is visible in the product shell/sidebar.
- AI review UX is integrated into Overview, Architecture/Files/API Routes, Read/Components, Work Plans/Agent Workflows/Improve, and Export.
- Disabled and missing-key states are compact, friendly, and do not repeat noisily inside every panel.
- AI actions are manual-only and never run during quest generation.
- Deterministic workbench behavior does not depend on AI.
- Certificate/network errors are shown as assistant errors and do not break the rest of the app.

## Handoff To Milestone 16

Milestone 16 should extend this foundation rather than rewrite it after the Milestone 15 shell and review UX are complete:

- Keep the existing async assistant service API.
- Add local model provider support inside the service/provider layer.
- Add schema-specific response contracts for summaries, docs, workflows, and recommendations.
- Keep mock mode as the default CI/test path.
