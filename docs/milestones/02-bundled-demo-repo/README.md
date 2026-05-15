# Milestone 2 - Bundled Demo Repo

Purpose: track the bundled React/Vite + FastAPI demo repo work.

## Goal

Provide a small, deterministic React/Vite + FastAPI repo that makes the demo story obvious.

## Required Files

- `examples/demo_repos/mini_travel_planner/README.md`
- `examples/demo_repos/mini_travel_planner/frontend/package.json`
- `examples/demo_repos/mini_travel_planner/frontend/vite.config.ts`
- `examples/demo_repos/mini_travel_planner/frontend/src/App.tsx`
- `examples/demo_repos/mini_travel_planner/frontend/src/pages/TripsPage.tsx`
- `examples/demo_repos/mini_travel_planner/frontend/src/components/TripCard.tsx`
- `examples/demo_repos/mini_travel_planner/frontend/src/components/SearchForm.tsx`
- `examples/demo_repos/mini_travel_planner/frontend/src/services/api.ts`
- `examples/demo_repos/mini_travel_planner/backend/requirements.txt`
- `examples/demo_repos/mini_travel_planner/backend/main.py`
- `examples/demo_repos/mini_travel_planner/backend/routes/trips.py`
- `examples/demo_repos/mini_travel_planner/backend/services/recommendations.py`
- `examples/demo_repos/mini_travel_planner/backend/models/trip.py`
- `examples/demo_repos/mini_travel_planner/backend/tests/test_trips.py`

## Implementation Tasks

- Keep the demo repo small and readable.
- Include React imports that produce useful component connections.
- Include FastAPI decorators for route extraction.
- Include backend route, service, model, and test examples.
- Make the frontend/backend story easy to explain in a 1-2 minute demo.
- Do not require the demo repo to be installed or executed by RepoQuest.

## Confirmed Milestone 2 Status

- Required demo repo files exist, including `backend/tests/test_trips.py`.
- The demo repo contains React/Vite evidence through `package.json`, `vite.config.ts`, `src/main.tsx`, and `src/App.tsx`.
- The demo repo contains FastAPI evidence through `backend/main.py`, `backend/routes/trips.py`, and route decorators.
- Frontend and backend imports are present and are now used by Milestone 5 graph work.

## Tests/Checks

- Demo repo scan sees expected files.
- Demo repo contains both frontend and backend entry points.
- Demo repo contains at least one FastAPI route decorator.
- Existing scanner classifies demo files into useful roles.

## Exit Criteria

- The bundled demo supports a 1-2 minute live walkthrough.
- The demo gives later milestones enough evidence for React/Vite detection, FastAPI detection, entry points, route extraction, component cards, reading path, and quiz questions.

## Post-Milestone 2 Follow-Up Fixes

These are small consistency fixes to make before or during the next Bob pass. They are not blockers for moving into Milestone 3, but they should be resolved before final demo polish.

- Update `examples/demo_repos/mini_travel_planner/README.md` so documented API endpoints match the FastAPI router prefix. Use `/api/trips`, `/api/trips/{trip_id}`, and `/api/recommendations`.
- Make the frontend recommendation-search story truthful and analyzable. Either add a simple `getRecommendations(destination?: string)` function in `frontend/src/services/api.ts` and wire `SearchForm`/`TripsPage` so the destination value reaches that API call, or simplify the demo README so it does not imply working recommendation search.
- Keep the demo repo deterministic and self-contained. Do not add real external APIs, account integrations, credentials, or heavyweight dependencies.
- Keep the demo repo as analysis input only. RepoQuest should not install or execute this demo repo during analysis.

## Carry Forward To UI And Docs

- Use the demo repo as the default live-demo path in Milestone 7.
- Keep the demo repo small enough that code/documentation previews are readable.
- Use demo files as evidence examples in the Documentation tab and exported report.
- Keep the demo repo as analysis input only. RepoQuest should not install or execute it.
