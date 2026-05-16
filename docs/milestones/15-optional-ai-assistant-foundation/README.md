# Milestone 15 - Testable AI Assistant Foundation

Purpose: add an optional, testable AI layer for code assistance without weakening deterministic RepoQuest.

MVP 2 phase: Optional AI Code Assistant.

## Goal

Introduce assistant mode as a disabled-by-default capability that can generate summaries, docs, tasks, workflows, and code recommendations from deterministic RepoQuest context.

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
- `OpenAIAssistantProvider`: optional real provider when configured.

## Schema-Driven Outputs

AI mode should use structured schemas for:

- Application summaries.
- Component docs pages.
- Epics, tasks, and milestones.
- Agent workflows.
- Test plans.
- Code recommendations.
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
- Deterministic workbench behavior does not depend on AI.
