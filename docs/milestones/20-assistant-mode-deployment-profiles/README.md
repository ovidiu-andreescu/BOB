# Milestone 20 - Assistant Mode Deployment Profiles

Purpose: separate deterministic RepoQuest from optional AI-assisted RepoQuest.

MVP 2 phase: Optional AI Code Assistant release readiness.

## Goal

Avoid confusing the no-secret deterministic app with AI-assisted code assistant mode.

This milestone should document the now-real Docker/async service setup and the planned local model profile.

## Profiles

### Deterministic Code Assistant Profile

- No secrets.
- No required runtime AI.
- Optional AI disabled.
- Streamlit Community Cloud compatible.
- Bundled demo repo works.
- Application graph excludes tests by default.
- Deterministic tasks, workflows, docs, and test intelligence work.

### Local AI Assistant Profile

- Optional local secrets.
- Mock provider by default in tests.
- Real provider only when explicitly enabled.
- Optional Docker Compose profile runs Streamlit and assistant/model calls as separate services.
- The app talks to the assistant service through `REPOQUEST_ASSISTANT_SERVICE_URL`.
- Can target a cloud provider or a local model provider.
- Useful for development and experimentation.
- Shows AI-enabled mode label.

### Local Model Profile

- No cloud AI key required.
- Runs a local model server on the host or in another container.
- Assistant service calls the local model endpoint.
- Recommended configuration uses OpenAI-compatible local endpoints first.
- Example providers: Ollama with OpenAI-compatible endpoint, LM Studio, llama.cpp server.
- Must still use bounded context packs and validation.
- Must have mock-mode tests; live local model calls are manual/dev-only.

### Hosted AI Assistant Profile

- Requires Streamlit secrets or another server-side secret mechanism.
- May use a separately hosted assistant service, but deterministic Streamlit deployment must still work without it.
- Must show clear AI-enabled label.
- Must include privacy, cost, and provider notes.
- Must preserve deterministic fallback.
- Must pass assistant validation/eval tests before demo.

## Documentation Tasks

- Update README with profile table.
- Add `docs/assistant_mode.md`.
- Add setup instructions for local secrets without committing secrets.
- Add local model setup instructions.
- Add Docker Compose examples for deterministic app, mock assistant service, Claude assistant service, and local model assistant service.
- Add limitations and privacy notes.
- Add troubleshooting for missing keys, rate limits, schema failures, invalid citations, and validation failures.
- Add troubleshooting for local model connection failures and slow model responses.
- Document how deterministic workflows differ from AI-assisted workflows.

## Tests/Checks

- Deterministic profile runs with no secrets.
- Missing assistant secrets produce a friendly disabled state.
- Mock provider works without network access.
- Hosted profile docs explain what data may be sent to the AI provider.
- Assistant profile can be disabled without code changes.
- Docker assistant service can run in mock mode without network access.
- Local model profile can be configured without a cloud key.
- Local model unavailable errors are displayed as assistant errors and do not break deterministic analysis.

## Exit Criteria

- Public docs clearly explain which profile is being demoed.
- The default app remains safe, deterministic, and no-secret.
- AI assistant mode is optional, testable, and clearly labeled.
