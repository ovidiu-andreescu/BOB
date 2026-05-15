# Milestone 9 - Polish And Final QA

Purpose: track final acceptance checks, manual QA, and demo readiness work.

## Goal

Verify the MVP against acceptance criteria and avoid last-minute demo failures.

## Required Commands

```bash
pytest -q
ruff check .
python scripts/run_local.py
```

## Manual QA Cases

- Bundled demo repo.
- Small valid ZIP.
- Invalid ZIP.
- Oversized ZIP.
- Empty repo.
- Unknown/mixed repo.

## Acceptance Checks

- Local app starts.
- Demo repo analyzes successfully.
- ZIP upload is safe.
- React/Vite and FastAPI are detected.
- Frontend and backend entry points are detected.
- FastAPI routes are extracted.
- Architecture graph renders.
- Dependency graph or summary renders.
- Reading path appears.
- Component cards appear.
- Quiz appears.
- Markdown guide downloads.
- Built with IBM Bob section appears.
- README and infra docs are complete.
- No external runtime AI/API/agent dependency exists.

## Exit Criteria

- RepoQuest is ready for a short hackathon demo and Streamlit Community Cloud deployment.
