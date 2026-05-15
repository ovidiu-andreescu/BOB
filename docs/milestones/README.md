# RepoQuest Milestones

This directory tracks the small, testable milestones for building RepoQuest as a local-demo-first Streamlit MVP.

RepoQuest should remain deterministic, static-analysis based, and demo-focused. Do not add runtime AI APIs, external agents, account connections, cloud credentials, GitHub OAuth, MCP, vector databases, or heavyweight dependencies.

## Current Snapshot

Milestones 1-6 are implemented enough to move the product work forward:

- The required package, demo repo, local runner, dependency files, tests, and Streamlit entry point exist.
- The bundled `mini_travel_planner` repo supports the React/Vite + FastAPI demo story.
- Safe directory and ZIP scanning are implemented and covered by tests.
- Framework detection and repo fingerprinting are implemented.
- Import graph parsing, route extraction, and graph rendering are implemented.
- Reading path, component cards, and quiz generation are implemented.
- `make qa` is the preferred local verification command.

The remaining milestone work is productization: reorganize the Streamlit UI, add richer previews and export flows, finish public docs, and complete final QA.

## Directory Index

- `01-scaffold-and-local-shell/` - required scaffold, local runner, infra config, and local command shell.
- `02-bundled-demo-repo/` - React/Vite + FastAPI demo repo used for the live walkthrough.
- `03-scanner-and-zip-safety/` - safe directory and ZIP scanning.
- `04-framework-detection-and-repo-fingerprint/` - deterministic framework detection and project fingerprinting.
- `05-imports-routes-and-architecture/` - import graph, route extraction, and architecture maps.
- `06-reading-path-component-cards-and-quiz/` - guided onboarding path, cards, and quiz.
- `07-streamlit-demo-ui/` - full Streamlit demo flow.
- `08-markdown-export-and-documentation/` - Markdown export and public project docs.
- `09-polish-and-final-qa/` - final acceptance checks and demo readiness.

## Recommended Next Step

Continue with Milestone 7. The app should move from "analysis output exists" to a polished demo workflow with clear tabs, better evidence previews, and explicit test/documentation surfaces.

## Tree/Graph Display Timing

- Milestone 5 includes the local-demo graph rendering slice.
- Milestone 7 should reorganize the existing outputs into the final tabbed Streamlit demo UI.
- Test files should not clutter the main dependency graph. Keep the primary dependency graph focused on application files and move test-specific relationships into a dedicated Tests tab or test section.

## Carry-Forward Product Notes

- Add a dedicated Tests tab that summarizes detected test files, likely test targets, test framework hints, and suggested next tests.
- Add documentation/code preview surfaces so judges can see short, safe snippets and generated onboarding text without leaving the app.
- Add a deterministic "Generate documentation" action for producing the Markdown guide/report from the current analysis result.
- Include short code examples as evidence, but keep previews capped and avoid showing entire large files.
- Keep every generated artifact deterministic. No runtime LLMs, agents, credentials, or hidden network calls.
