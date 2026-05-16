# Implementation Prompt - Milestone 15 Testable AI Assistant Foundation

You are IBM Bob working in the RepoQuest repository.

Implement Milestone 15: **Testable AI Assistant Foundation**.

The current deterministic RepoQuest workbench is complete through Milestone 14. Your job is to make optional AI assistant mode feel like a coherent first-class review layer in the product shell and core workflows, while preserving deterministic behavior when AI is disabled.

## Product Goal

RepoQuest should remain usable with no secrets, no runtime AI, and no external model service. When AI is enabled, it should provide manual, evidence-grounded review actions from bounded RepoQuest context.

Milestone 15 is not complete if AI is only scattered buttons. It must feel like an integrated **AI Review layer** with compact app-level state, clear labeling, validation, and safe failure behavior.

## Current Foundation

Assume these pieces already exist or are partially implemented:

- `.env.example` documents `REPOQUEST_AI_ENABLED`, `CLAUDE_API_KEY`, and `CLAUDE_MODEL`.
- Local `.env` and Streamlit secrets are supported.
- Assistant providers include disabled, mock, and Claude providers.
- Assistant provider layer can route through an async assistant service.
- Docker Compose can run Streamlit and the assistant service separately.
- Assistant service exposes `POST /jobs`, `GET /jobs/{job_id}`, and `GET /health`.
- Context builders create bounded packs from deterministic RepoQuest data.
- Validation rejects empty responses, nonexistent citations, and unsafe execution claims.
- Deterministic analysis works when AI is disabled, missing keys, network errors, or validation failures occur.

Do not rework the deterministic analyzer. Integrate the AI layer around it.

## Required UX Changes

Add a compact shell-level AI state:

- Show AI status once in the product shell/sidebar or top workspace area.
- States: disabled, enabled with direct provider, enabled through async service, missing key, service unavailable, provider error, validation error.
- Include provider/model when known.
- Disabled and missing-key states must not repeat noisily inside every tab or content panel.
- AI status is app/runtime metadata, not analyzed repository content.

Make AI Review visible as a coherent layer:

- Overview: AI review of project fingerprint and repo risks.
- Architecture/Files/API Routes: AI review of selected file, graph node, or route group.
- Read/Components: AI explanation, improvement ideas, and questions for selected file/component.
- Work Plans/Agent Workflows/Improve: AI refinement of deterministic tasks and workflows.
- Export: include validated AI review outputs only when present and clearly labeled.

All AI actions must be manual-only. AI must never run during quest generation.

## Required Safety Behavior

- Assistant mode is off by default.
- The app works without secrets.
- No uploaded code is executed.
- No uploaded dependencies are installed.
- Only bounded context packs and capped snippets are sent to any provider.
- AI responses are labeled AI-assisted.
- Deterministic findings remain visible and usable without AI.
- Invalid AI output fails closed and is not shown as trusted guidance.
- Certificate, network, timeout, missing-key, and provider errors stay isolated to assistant UI state.

## Provider Requirements

Keep the provider interface:

```python
class AssistantProvider(Protocol):
  def generate(self, request: AssistantRequest) -> AssistantResponse:
    ...
```

Required providers:

- `DisabledAssistantProvider`
- `MockAssistantProvider`
- `ClaudeAssistantProvider`
- `AssistantServiceProvider`

Do not implement local model providers in this milestone. Local model support belongs to Milestone 16.

## Configuration

Local:

```bash
cp .env.example .env
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

Never commit `.env` or secrets.

## Validation Rules

Assistant output must be validated before being shown as trusted:

- Empty responses are invalid.
- Referenced file paths must exist in the current snapshot.
- Recommendations must cite evidence paths or snippets.
- Output must not claim tests were run unless RepoQuest actually ran a verification command.
- Output must not ask RepoQuest to execute uploaded code.
- Missing evidence downgrades or hides the suggestion.

## Implementation Guidance

- Keep deterministic analysis and all deterministic tabs usable when AI is disabled.
- Store assistant responses and validation status in session state.
- Avoid repeating disabled/missing-key callouts in every tab.
- Use compact UI affordances: status chip, provider/model label, one-line disabled state, expandable error details.
- Make AI review outputs visually distinct from deterministic findings.
- Keep assistant requests section-scoped and bounded.
- Keep mock provider as the default path for tests.

## Tests To Add Or Update

Add or update tests so these pass:

- App/provider logic works with assistant disabled.
- Missing API key does not crash.
- Mock provider returns schema-valid or validation-acceptable outputs.
- Malformed mock output is rejected.
- Output referencing nonexistent files is rejected.
- Output without evidence is not shown as trusted.
- Assistant service error/timeout returns an assistant error and does not break deterministic analysis.
- UI/state helpers can represent disabled, missing-key, enabled, service, provider error, and validation error states.

Do not require live Claude or network calls in tests.

## Acceptance Criteria

Milestone 15 is complete when:

- Assistant foundation exists and is safe to enable experimentally.
- AI is testable locally without network access.
- AI state is visible in the product shell/sidebar.
- AI Review UX is integrated into Overview, Architecture/Files/API Routes, Read/Components, Work Plans/Agent Workflows/Improve, and Export.
- Disabled and missing-key states are compact, friendly, and not repeated inside every panel.
- AI actions are manual-only and never run during quest generation.
- Deterministic workbench behavior does not depend on AI.
- Certificate/network/service errors are shown as assistant errors and do not break the rest of the app.

## Handoff To Milestone 16

Do not implement local model providers here. After Milestone 15 is complete, Milestone 16 should:

- Keep the existing async assistant service API.
- Add local model provider support inside the service/provider layer.
- Add schema-specific response contracts for summaries, docs, workflows, and recommendations.
- Keep mock mode as the default CI/test path.
