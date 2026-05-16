# Milestone 19 - Clean UI Shell And Workspace State

Purpose: separate RepoQuest product concerns from analyzed repo/ZIP findings and make exploration feel like a workspace.

MVP 2 phase: Deterministic Code Assistant complete; optional assistant workspace polish.

## Goal

Create a clean, modern UI structure where the user always knows what belongs to RepoQuest itself and what belongs to the analyzed repository.

Milestones 10-14 completed the deterministic workbench. This milestone should polish the remaining UI state and assistant-state separation.

## UI Separation

### Product Shell

Use for:

- RepoQuest name and short value proposition.
- App status and mode labels.
- About/Built with IBM Bob.
- Safety limits and no-runtime-AI/default-mode statements.

### Source/Input Panel

Use for:

- Demo repo selection.
- ZIP upload.
- Upload validation status.
- Source name, scan timestamp, and scan warnings.
- Generate/reset controls before and after analysis.
- Current source status after analysis.
- Persistent app limits and AI status.
- After analysis, keep the source panel available so users can upload a new ZIP, switch back to the demo, or reset without losing orientation.

### Analysis Workspace

Use for analyzed repo output only:

- Overview.
- Application Graph.
- Reading Workbench.
- Components.
- Test Impact.
- Tasks and Workflows.
- Generated Docs.
- Export.
- Iconized, colored section headers that replace emoji markers while keeping sections easy to scan.

### Generate Workspace

Use for generated artifacts:

- Documentation pages.
- Agent workflows.
- AI Assistant actions.
- Export bundles.
- Optional AI recommendations.

## Recommended Navigation

- Sidebar: source controls, upload/generate/reset, current source, app limits, AI Review status, and About/Built with IBM Bob.
- Overview: project fingerprint, framework evidence, entry points, next read, and architecture preview.
- Architecture: conceptual system map and technical dependency graph.
- Files: repository tree, file selector, code preview, deterministic file analysis, dependencies, routes, and AI file review.
- API Routes: endpoint selector, route metadata, linked route file analysis, and route table details.
- Read: one selected reading-path file at a time.
- Components: one selected component card at a time.
- Work Plans: epics, tasks, and milestones.
- Agent Workflows: step-by-step assistant workflows, validation steps, AI workflow review, and workflow export.
- Improve: test intelligence and onboarding quiz.
- Export: docs preview, Markdown guide, work plan export, and AI export review.

## Session State

Store:

- Current snapshot and source metadata.
- Selected graph node/component.
- Reading path completion.
- Generated tasks and workflows.
- Generated documentation pages.
- Quiz answers.
- Assistant recommendations and validation state.
- Assistant provider metadata: disabled/mock/Claude/local/service, model name, job id, status, validation status.
- Export bundle.

## Tests/Checks

- Switching from demo repo to ZIP clears stale analysis state.
- Source/Input state is visually separate from analyzed repo findings.
- Source/Input controls remain available after analysis has completed.
- The analysis workspace exposes a Refresh action, not a "Start Over" action.
- Built with IBM Bob content is not mixed into repo analysis tabs.
- Assistant status is shown as app/runtime metadata, not as analyzed repo content.
- Local model or async service errors stay in assistant result/status areas.
- Export bundle includes selected components, completed checklist items, tasks, workflows, generated docs, and assistant validation status when present.

## Exit Criteria

- The app feels like a clean code-assistant workspace.
- Product/about information no longer competes with uploaded repo findings.
