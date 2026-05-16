# Milestone 19 - Clean UI Shell And Workspace State

Purpose: separate RepoQuest product concerns from analyzed repo/ZIP findings and make exploration feel like a workspace.

MVP 2 phase: Deterministic Code Assistant, then Optional AI Code Assistant.

## Goal

Create a clean, modern UI structure where the user always knows what belongs to RepoQuest itself and what belongs to the analyzed repository.

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
- Reset/new analysis.

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

### Generate Workspace

Use for generated artifacts:

- Documentation pages.
- Agent workflows.
- Bob prompts.
- Export bundles.
- Optional AI recommendations.

## Recommended Navigation Groups

- Analyze: Overview, Source, Fingerprint.
- Explore: Application Graph, Reading Workbench, Components.
- Improve: Test Impact, Tasks, Workflows.
- Generate: Docs, Prompts, Export.
- About: Built with IBM Bob, App Limits, Safety.

## Session State

Store:

- Current snapshot and source metadata.
- Selected graph node/component.
- Reading path completion.
- Generated tasks and workflows.
- Generated documentation pages.
- Quiz answers.
- Assistant recommendations and validation state.
- Export bundle.

## Tests/Checks

- Switching from demo repo to ZIP clears stale analysis state.
- Source/Input state is visually separate from analyzed repo findings.
- Built with IBM Bob content is not mixed into repo analysis tabs.
- Export bundle includes selected components, completed checklist items, tasks, workflows, generated docs, and assistant validation status when present.

## Exit Criteria

- The app feels like a clean code-assistant workspace.
- Product/about information no longer competes with uploaded repo findings.
