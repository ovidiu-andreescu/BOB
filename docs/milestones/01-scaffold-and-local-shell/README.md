# Milestone 1 - Scaffold And Local Shell

Purpose: track scaffold and local launch work for RepoQuest.

Status: implemented enough for local development and later milestones. Remaining public-facing documentation and final submission polish are tracked in Milestones 8 and 9.

## Goal

Create the required repository shape and make the local app launchable.

## Required Files

- `repoquest/__init__.py`
- `repoquest/config.py`
- `repoquest/models.py`
- `app/streamlit_app.py`
- `infra/local/README.md`
- `infra/local/requirements-dev.txt`
- `infra/local/streamlit_config.toml`
- `infra/local/run_local.sh`
- `infra/local/run_local.ps1`
- `infra/streamlit/README.md`
- `infra/streamlit/requirements.txt`
- `infra/streamlit/streamlit_config.toml`
- `.streamlit/config.toml`
- `requirements.txt`
- `scripts/run_local.py`
- `scripts/sync_streamlit_cloud_config.py`
- `README.md`
- `pyproject.toml`

## Carry Forward

- Keep `.streamlit/config.toml` mirrored from `infra/streamlit/streamlit_config.toml`.
- Keep root `requirements.txt` as `-r infra/streamlit/requirements.txt`.
- Keep runtime dependencies limited to `streamlit`, `pandas`, and `pyyaml` unless a later milestone proves another lightweight dependency is necessary.
- Prefer `make run`, `make test`, `make lint`, and `make qa` once the Makefile exists.
- Finish public-facing docs such as `docs/bob_usage.md`, `docs/demo_script.md`, and `docs/architecture.md` in Milestone 8.

## Checks

- `make run` starts the app.
- `make check-cloud-config` validates config sync.
- `make qa` runs config validation, lint, and tests.

## Exit Criteria

- App starts locally.
- Required scaffold exists.
- No local environment/cache files appear in `git status`.
