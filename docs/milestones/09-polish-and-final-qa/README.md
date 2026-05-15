# Milestone 9 - Polish And Final QA

Purpose: track final acceptance checks, manual QA, and demo readiness work.

## Goal

Verify the MVP against acceptance criteria and avoid last-minute demo failures.

## Required Commands

```bash
make qa
make run
```

Use the direct commands only when debugging the Makefile itself:

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
- Demo repo after clicking Generate Onboarding Quest twice.
- ZIP upload after previously analyzing the demo repo.
- Documentation generation before and after export.
- Tests tab with a repo that has tests.
- Tests tab with a repo that has no tests.
- Documentation preview with README/docs present.
- Documentation preview with no README/docs present.

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
- Tests tab appears and keeps test files out of the default dependency graph.
- Quiz appears.
- Documentation tab previews generated guide/report content.
- Generate documentation button works from the current analysis result.
- Markdown guide downloads.
- Built with IBM Bob section appears.
- README and infra docs are complete.
- No external runtime AI/API/agent dependency exists.

## Demo Polish Checklist

- First click shows a strong "React/Vite + FastAPI full-stack app" story for the bundled demo.
- Overview gives framework evidence without forcing the judge to inspect raw file tables.
- Architecture tab opens on the human-friendly graph, not the technical graph.
- Dependency graph excludes test files by default.
- Tests tab makes `backend/tests/test_trips.py` useful by showing likely coverage and suggested next tests.
- Component cards include short code examples or evidence snippets.
- Documentation tab shows a generated guide preview and a clear "Generate documentation" action.
- Export tab downloads the same Markdown shown in preview.
- Empty states are friendly and do not show tracebacks.
- Cloud mode hides raw error details.

## Regression Risks To Watch

- Pandas/Streamlit pins must remain compatible with the Python version used locally and on Streamlit Cloud.
- Test discovery should not accidentally run the bundled demo repo's own FastAPI tests unless those dependencies are intentionally installed.
- ZIP handling must remain scan-only. Do not extract blindly, install dependencies, or import uploaded code.
- Adding previews should not display huge files or binary contents.
- Adding documentation generation should not introduce runtime AI calls.

## Exit Criteria

- RepoQuest is ready for a short hackathon demo and Streamlit Community Cloud deployment.
