# RepoQuest Milestones

This directory tracks RepoQuest across two product stages.

## MVP 1 Status

Milestones 1-9 are complete. The first MVP is fulfilled:

- Bundled demo repo works.
- Safe scanning and ZIP handling exist.
- Framework detection and repo fingerprinting exist.
- Import graph, route extraction, architecture map, reading path, component cards, quiz, and Markdown export exist.
- Streamlit UI and public docs exist.
- Final QA has been completed for the first MVP.

MVP 1 remains the hackathon-safe deterministic product: no required runtime AI, no external agents, no account connections, no GitHub OAuth, no MCP, no vector database, and no uploaded-code execution.

## MVP 2 Status

Milestones 10-14 are complete. The deterministic Code Assistant Workbench is now the current baseline:

- Default application graphs exclude tests and disconnected debug-only graph noise.
- Reading Path includes capped previews and improvement-oriented guidance.
- Deterministic epics, tasks, milestones, and agent workflows exist.
- Test Impact/Quality analysis exists and feeds the workbench.
- Component-oriented documentation and work plans are part of the generated output.
- UI work has started separating source/input, analysis, generation, and app/about concerns.
- Milestone 15 is in progress: disabled/mock/Claude providers, manual assistant actions, validation, Docker, and an async assistant service exist, but the AI Review UX still needs to feel integrated and first-class.

The remaining MVP 2 work is the optional assistant layer: finish the integrated AI Review UX in Milestone 15, then add richer schema-driven AI outputs, evals, Docker/async polish, local model providers, and deployment-profile documentation.

## MVP 2 Vision

MVP 2 takes RepoQuest from "onboarding report generator" to **RepoQuest Code Assistant Workbench**.

The product should help a developer improve the application, not only understand where files live:

- The main architecture/dependency graphs show application code only. Test files must not appear in the default graph.
- Tests have their own Test Impact/Quality view.
- Reading Path shows actual snippets, README/docs excerpts, route decorators, imports, and concrete improvement ideas.
- The app generates epics, tasks, milestones, and agent-ready workflows for IBM Bob or AI coding agents.
- UI separates RepoQuest product/about information from analyzed repo/ZIP findings.
- Documentation generation is component-based, like API/reference docs for the scanned repo.
- Optional AI mode is a testable code-assistance layer with schemas, mock providers, local model support, eval fixtures, evidence citations, and fail-closed validation.
- Docker can run the deterministic app and optional async assistant service as separate processes.
- Local model mode should run through the assistant service without requiring cloud AI credentials.

The guiding rule: deterministic analysis remains the source of truth. AI, when enabled, is an optional synthesis layer that must cite deterministic evidence and pass validation before being shown as trusted guidance.

## MVP 2 Acceptance Criteria

MVP 2 is complete when:

- Main app graphs exclude `test_*.py`, `tests/`, and similar test files by default.
- Test files appear in Test Impact/Quality views and optional debug graph mode only.
- Users can select a component/file and see details, dependencies, related routes, related tests, and optional assistant actions.
- Reading Path includes inline docs/code previews and concrete "understand/improve/assistant action" guidance.
- RepoQuest can generate deterministic workflows for AI agents and IBM Bob.
- Component-based docs are generated from detected routes, models, services, frontend pages/components, tests, and workflows.
- The UI clearly separates product shell, input/source controls, analysis workspace, generation workspace, and about/meta content.
- The app exports enhanced workbench findings, docs pages, tasks, workflows, and prompts.
- Optional assistant mode is disabled by default and does not affect deterministic behavior.
- Assistant mode, if enabled, uses bounded context packs, structured outputs, mockable providers, local/remote provider profiles, validation, and clear AI labeling.
- Docker profiles support deterministic app mode and optional async assistant service mode.
- Local model profile can run assistant calls through a local OpenAI-compatible or local-model endpoint.
- Missing secrets, unavailable local models, failed AI calls, invalid AI output, nonexistent citations, or missing evidence never break deterministic analysis.

## Planned Interfaces

MVP 2 milestone docs should guide implementation toward these models:

```python
GraphViewMode = Literal["application", "tests", "all_debug"]

@dataclass
class ReadingPathDetail:
  path: str
  summary: str
  snippet: str
  what_to_understand: list[str]
  improvement_opportunities: list[str]
  related_tasks: list[str]
  assistant_action: str

@dataclass
class TaskSuggestion:
  epic: str
  priority: str
  files: list[str]
  evidence: list[str]
  why: str
  acceptance_criteria: list[str]
  suggested_workflow: str

@dataclass
class AgentWorkflow:
  title: str
  goal: str
  ordered_steps: list[str]
  files_to_read: list[str]
  files_to_change: list[str]
  validation_steps: list[str]
  expected_output: str
  prompt: str

@dataclass
class TestInsight:
  test_file: str
  framework: str
  imports: list[str]
  likely_targets: list[str]
  covered_routes: list[str]
  missing_cases: list[str]
  suggested_tests: list[str]

@dataclass
class GeneratedDocPage:
  title: str
  category: str
  source_files: list[str]
  content: str
  evidence: list[str]
  related_components: list[str]
```

Additional assistant-provider interfaces for the remaining milestones:

```python
AssistantProviderName = Literal["disabled", "mock", "claude", "assistant-service", "local"]

@dataclass
class LocalModelConfig:
  base_url: str
  model: str
  provider_style: Literal["openai-compatible", "ollama", "lmstudio", "llama-cpp"]
```

## MVP 2 Build Order

Phase 1 is the deterministic code assistant workbench. Complete:

1. Milestone 10 - Lock MVP 2 direction and product line.
2. Milestone 11 - Add application-only graph explorer and debug graph modes.
3. Milestone 12 - Replace path-only reading with evidence-backed reading/workbench previews.
4. Milestone 13 - Add deterministic epics, tasks, milestones, and agent workflows.
5. Milestone 14 - Add useful test intelligence and impact/quality views.

Phase 2 is optional testable AI. In progress:

1. Milestone 15 - Assistant foundation, Docker, validation, manual AI actions, async service baseline, and integrated AI Review UX. In progress.
2. Milestone 16 - Add local model providers plus richer schema-driven AI summaries/docs/workflows after the AI Review UX is complete.
3. Milestone 17 - Add AI epic/task/code recommendations across Claude, local, and service providers.
4. Milestone 18 - Add evals, validation, provider-specific failure tests, and trust gates.
5. Milestone 19 - Polish persistent workspace state, sharing/export state, and assistant state export.
6. Milestone 20 - Finalize Docker, local model, hosted assistant, and deterministic deployment profiles.

Phase 1 can ship as "MVP 2 deterministic code assistant." Phase 2 can ship as "MVP 2 optional AI assistant with local model support."

## Directory Index

### MVP 1 - Complete

- `01-scaffold-and-local-shell/` - required scaffold, local runner, infra config, and local command shell.
- `02-bundled-demo-repo/` - React/Vite + FastAPI demo repo used for the live walkthrough.
- `03-scanner-and-zip-safety/` - safe directory and ZIP scanning.
- `04-framework-detection-and-repo-fingerprint/` - deterministic framework detection and project fingerprinting.
- `05-imports-routes-and-architecture/` - import graph, route extraction, and architecture maps.
- `06-reading-path-component-cards-and-quiz/` - guided onboarding path, cards, and quiz.
- `07-streamlit-demo-ui/` - full Streamlit demo flow.
- `08-markdown-export-and-documentation/` - Markdown export and public project docs.
- `09-polish-and-final-qa/` - final acceptance checks and demo readiness.

### MVP 2 - RepoQuest Code Assistant Workbench

- `10-assistant-research-and-product-direction/` - complete MVP 2 scope and code assistant product line.
- `11-interactive-graph-explorer/` - complete application graph explorer with tests excluded by default.
- `12-evidence-preview-workbench/` - complete reading path with capped code/doc previews, fullscreen reader, and improvement guidance.
- `13-deterministic-epic-task-finder/` - complete epics, tasks, milestones, and agent workflow generation.
- `14-test-intelligence-and-impact-map/` - complete useful test impact, quality, and missing-case analysis.
- `15-optional-ai-assistant-foundation/` - in progress disabled-by-default assistant adapter, secrets, validation, Claude/mock providers, Docker, optional async assistant service, and integrated AI Review UX.
- `16-ai-repo-summary-and-context-packs/` - planned local model provider support plus bounded context packs and AI summaries/docs/workflows.
- `17-ai-epic-task-and-code-recommendations/` - planned AI-assisted recommendations grounded in evidence.
- `18-assistant-evals-and-trust-gates/` - planned validation and evals for assistant outputs across mock, cloud, async service, and local providers.
- `19-shareable-workspaces-and-session-state/` - planned persistent workspace state, assistant state, session state, and exportable workspace state.
- `20-assistant-mode-deployment-profiles/` - planned deterministic, Docker, local model, local assistant, and hosted assistant profiles.

## Product Guardrails

- Do not weaken ZIP safety.
- Do not execute uploaded code.
- Do not install uploaded dependencies.
- Do not send raw full repositories to an AI provider or local model.
- Do not show test files in the default application graph.
- Do not hide deterministic findings behind assistant output.
- Do not make secrets or local models required for the default demo.
- Do not let assistant failures block the core app.
- Do not overclaim that RepoQuest fully understands arbitrary codebases.
- Do not add demo-specific file-name logic to production analyzers.
- Do not show disconnected graph nodes in the primary graph.

## Test And Acceptance Plan

MVP 2 docs should require tests for:

- Main graph excludes `test_*.py`, `tests/`, and similar test files.
- Test Impact view includes those same test files.
- Reading Path renders snippets/previews for README, backend route, frontend page, API client, and test file.
- Agent workflow generator produces deterministic workflows for the demo repo.
- Generated component docs include API route pages and component pages.
- UI state keeps RepoQuest app/about information separate from uploaded ZIP analysis.
- Mock and local-model providers return schema-valid outputs in tests/fixtures.
- Invalid AI outputs are rejected or clearly marked unusable.
- AI recommendations without evidence are not shown as trusted suggestions.
- Assistant service timeout, local model unavailable, and cloud API failure paths do not break deterministic analysis.
