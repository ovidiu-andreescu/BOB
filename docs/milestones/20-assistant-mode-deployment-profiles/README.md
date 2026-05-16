# Milestone 20 - Assistant Mode Deployment Profiles

Purpose: separate deterministic RepoQuest from optional AI-assisted RepoQuest.

MVP 2 phase: Optional AI Code Assistant release readiness.

## Goal

Avoid confusing the no-secret deterministic app with AI-assisted code assistant mode.

## Profiles

### Deterministic Code Assistant Profile

- No secrets.
- No runtime AI.
- Streamlit Community Cloud compatible.
- Bundled demo repo works.
- Application graph excludes tests by default.
- Deterministic tasks, workflows, docs, and test intelligence work.

### Local AI Assistant Profile

- Optional local secrets.
- Mock provider by default in tests.
- Real provider only when explicitly enabled.
- Useful for development and experimentation.
- Shows AI-enabled mode label.

### Hosted AI Assistant Profile

- Requires Streamlit secrets or another server-side secret mechanism.
- Must show clear AI-enabled label.
- Must include privacy, cost, and provider notes.
- Must preserve deterministic fallback.
- Must pass assistant validation/eval tests before demo.

## Documentation Tasks

- Update README with profile table.
- Add `docs/assistant_mode.md`.
- Add setup instructions for local secrets without committing secrets.
- Add limitations and privacy notes.
- Add troubleshooting for missing keys, rate limits, schema failures, invalid citations, and validation failures.
- Document how deterministic workflows differ from AI-assisted workflows.

## Tests/Checks

- Deterministic profile runs with no secrets.
- Missing assistant secrets produce a friendly disabled state.
- Mock provider works without network access.
- Hosted profile docs explain what data may be sent to the AI provider.
- Assistant profile can be disabled without code changes.

## Exit Criteria

- Public docs clearly explain which profile is being demoed.
- The default app remains safe, deterministic, and no-secret.
- AI assistant mode is optional, testable, and clearly labeled.
