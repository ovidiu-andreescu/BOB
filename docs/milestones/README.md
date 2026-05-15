# RepoQuest Milestones

This directory tracks the small, testable milestones for building RepoQuest as a local-demo-first Streamlit MVP.

RepoQuest should remain deterministic, static-analysis based, and demo-focused. Do not add runtime AI APIs, external agents, account connections, cloud credentials, GitHub OAuth, MCP, vector databases, or heavyweight dependencies.

## Current Snapshot

The repository currently has an early file-inventory MVP:

- Basic `repoquest/` package exists.
- Demo repo exists at `examples/demo_repos/mini_travel_planner/`.
- Streamlit entry point exists at `app/streamlit_app.py`.
- Root `requirements.txt` references `infra/streamlit/requirements.txt`.
- Root `.streamlit/config.toml` exists for Streamlit Cloud compatibility.
- `.gitignore` exists and keeps local environments/caches out of commits.

Milestone 1 has follow-up scaffold gaps, but the current plan is to continue with Milestone 2 first and return to those cleanup items later.

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

Continue with `02-bundled-demo-repo/` and return to the deferred Milestone 1 scaffold cleanup when testing, deployment, or final submission requires it.

## Tree/Graph Display Timing

- Milestone 5 creates the underlying architecture map and dependency graph data/DOT rendering helpers.
- Milestone 7 exposes those graphs in the Streamlit UI through the Architecture Map tab.
