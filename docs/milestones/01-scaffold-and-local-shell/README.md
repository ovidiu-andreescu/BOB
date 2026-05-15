# Milestone 1 - Scaffold And Local Shell

Purpose: track scaffold and local launch work for RepoQuest.

Status: partially complete. The current plan is to move on to Milestone 2 first, then return to these scaffold cleanup items when they become necessary for testing, deployment, or final submission.

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

## Additional Fixes Missed In The Initial Checkpoint

- `infra/local/` was not created.
- `infra/streamlit/streamlit_config.toml` was not created.
- `infra/streamlit/README.md` was not created.
- `scripts/sync_streamlit_cloud_config.py` was not created.
- `tests/` and `tests/fixtures/` were not created.
- `docs/bob_usage.md`, `docs/demo_script.md`, and `docs/architecture.md` were not created.
- `bob_sessions/README.md` was not created.
- `pyproject.toml` was not created.
- `scripts/run_local.py` did not include `--server.runOnSave=true`.
- Streamlit configs did not explicitly disable usage statistics.
- The root cloud config was not backed by a canonical `infra/streamlit/streamlit_config.toml`.
- The demo backend test file was not included.

## Existing File Corrections

- Update `scripts/run_local.py` to pass `--server.runOnSave=true`.
- Add `[browser] gatherUsageStats = false` to local and cloud Streamlit configs.
- Make `.streamlit/config.toml` mirror `infra/streamlit/streamlit_config.toml`.
- Keep root `requirements.txt` as `-r infra/streamlit/requirements.txt`.
- Keep runtime dependencies limited to `streamlit`, `pandas`, and `pyyaml` unless a later milestone proves another lightweight dependency is necessary.

## Checks

- `python scripts/run_local.py` starts the app.
- `python scripts/sync_streamlit_cloud_config.py --check` or equivalent validates config sync.
- `ruff check .` can run once dev dependencies exist.

## Exit Criteria

- App starts locally.
- Required scaffold exists.
- No local environment/cache files appear in `git status`.
