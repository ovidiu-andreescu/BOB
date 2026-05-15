# RepoQuest Milestones

This directory tracks the small, testable milestones for building RepoQuest as a local-demo-first Streamlit MVP.

RepoQuest should remain deterministic, static-analysis based, and demo-focused. Do not add runtime AI APIs, external agents, account connections, cloud credentials, GitHub OAuth, MCP, vector databases, or heavyweight dependencies.

## Current Snapshot

The repository currently has a local-demo graph slice:

- Basic `repoquest/` package exists.
- Demo repo exists at `examples/demo_repos/mini_travel_planner/`.
- Streamlit entry point exists at `app/streamlit_app.py`.
- Root `requirements.txt` references `infra/streamlit/requirements.txt`.
- Root `.streamlit/config.toml` exists for Streamlit Cloud compatibility.
- `.gitignore` exists and keeps local environments/caches out of commits.
- The local Streamlit flow scans the bundled demo repo and shows file inventory, routes, architecture map, dependency graph, and import statistics.

Milestone 1 still has follow-up scaffold gaps. Milestone 5 is partially implemented for the local demo and needs one more graph-resolution pass before moving on.

## Directory Index

- `01-scaffold-and-local-shell/` - required scaffold, local runner, infra config, and deferred cleanup.
- `02-bundled-demo-repo/` - React/Vite + FastAPI demo repo used for the live walkthrough.
- `03-scanner-and-zip-safety/` - safe directory and ZIP scanning.
- `04-framework-detection-and-repo-fingerprint/` - deterministic framework detection and project fingerprinting.
- `05-imports-routes-and-architecture/` - import graph, route extraction, and architecture maps.
- `06-reading-path-component-cards-and-quiz/` - guided onboarding path, cards, and quiz.
- `07-streamlit-demo-ui/` - full Streamlit demo flow.
- `08-markdown-export-and-documentation/` - Markdown export and public project docs.
- `09-polish-and-final-qa/` - final acceptance checks and demo readiness.

## Recommended Next Step

Finish the remaining graph-resolution fixes in `05-imports-routes-and-architecture/`, then continue toward `06-reading-path-component-cards-and-quiz/`.

## Tree/Graph Display Timing

- Milestone 5 now includes the local-demo graph rendering slice.
- Milestone 7 should later reorganize this into the final tabbed Streamlit demo UI.
