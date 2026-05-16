# Milestone 16 - Local Models, Context Packs, And AI Docs

Purpose: extend the assistant foundation with local model support, richer bounded context packs, and schema-driven AI documentation after Milestone 15's integrated AI Review UX is complete.

MVP 2 phase: Optional AI Code Assistant.

## Required Baseline From Milestones 10-15

Required before starting this milestone:

- Deterministic Code Assistant Workbench through Milestone 14.
- Disabled, mock, and Claude assistant providers.
- Manual-only assistant actions in the UI.
- Persistent shell/sidebar AI status.
- AI Review areas integrated into the core workspace groups.
- Compact disabled/missing-key states that do not clutter deterministic content.
- Optional async assistant service with `POST /jobs`, `GET /jobs/{job_id}`, and `GET /health`.
- Docker Compose profile for running Streamlit and the assistant service separately.
- Bounded assistant context builders.
- Citation validation and failure handling.

Milestone 16 should focus on local models and richer schema-driven outputs, not on re-creating the provider foundation or repairing the UI shell.

## Goal

Let RepoQuest run optional assistant mode through local models as well as cloud providers, while generating useful AI-assisted summaries and component documentation from bounded deterministic context.

## Local Model Provider Support

Add a local model provider path that can run through the same provider interface:

```python
class LocalModelAssistantProvider:
  provider: Literal["local-openai-compatible", "ollama", "lmstudio"]
  base_url: str
  model: str
```

Recommended default implementation:

- Support an OpenAI-compatible local HTTP endpoint first.
- Configure with `REPOQUEST_LOCAL_MODEL_BASE_URL` and `REPOQUEST_LOCAL_MODEL_NAME`.
- Route local model calls through the async assistant service when Docker is used.
- Keep mock provider as the CI default.

Optional later convenience adapters:

- Ollama native API.
- LM Studio OpenAI-compatible API.
- llama.cpp server OpenAI-compatible API.

## Configuration

Add documented environment variables:

```bash
REPOQUEST_AI_ENABLED=true
REPOQUEST_ASSISTANT_PROVIDER=local
REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1
REPOQUEST_LOCAL_MODEL_NAME=llama3.1
REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765
```

Docker notes:

- The Streamlit container should call the assistant service.
- The assistant service should call the local model endpoint.
- Local model containers or host services should be optional.
- Deterministic app mode must still run without any model service.

## Planned Interface

```python
@dataclass
class GeneratedDocPage:
  title: str
  category: str
  source_files: list[str]
  content: str
  evidence: list[str]
  related_components: list[str]
```

## Context Pack Contents

- Project fingerprint.
- Framework evidence.
- Entry points.
- Application graph summary without test files.
- Test impact summary.
- Routes.
- Component cards.
- Reading path details and snippets.
- Deterministic epics/tasks/workflows.
- Warnings and skipped files.
- Short evidence snippets.

## Schema-Driven AI Outputs

Add structured response contracts for:

- Application summary.
- Component documentation pages.
- API route reference pages.
- Test plan summary.
- Workflow refinement.
- Code recommendation summary.

## Component Documentation Pages

Generate reference-style docs:

- API Routes reference.
- Models/Schemas reference.
- Services/business logic notes.
- Frontend pages/components reference.
- API client reference.
- Test reference.
- Agent workflows.
- Known gaps and improvement opportunities.

Each generated page should include purpose, source files, evidence snippets, dependencies, related tests, improvement ideas, and assistant prompts.

## Tests/Checks

- Local provider config can be parsed without requiring a model to be running.
- Mock local-model responses validate against schemas.
- Local provider network failures return assistant errors without breaking deterministic analysis.
- Context pack excludes skipped files and full large files.
- Context pack includes route evidence, component evidence, test insights, and workflows for the demo repo.
- Generated docs include API route pages and frontend component pages.
- AI-enhanced docs cite existing file paths.
- Mock AI docs with invalid citations are rejected.

## Exit Criteria

- RepoQuest can be configured for local model execution through the assistant provider/service layer.
- RepoQuest can generate reference-style documentation from discovered components.
- Optional AI can enhance docs without becoming the source of truth.
