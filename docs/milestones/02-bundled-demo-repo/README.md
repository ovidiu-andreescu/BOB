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

## Current Gaps To Check

- Confirm `backend/tests/test_trips.py` exists.
- Confirm the demo README explains the app story in a few lines.
- Confirm frontend files import each other enough to support a useful dependency graph.
- Confirm backend route files import service/model files enough to support a useful dependency graph.
- Confirm the route file contains clear FastAPI decorators such as `@router.get`, `@router.post`, and `@router.delete`.

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

## Carry Forward To Later Milestones

- Milestone 3 should confirm the scanner safely handles the expanded demo repo file set.
- Milestone 4 should ensure file roles include `frontend/src/main.tsx` as an entry point, `frontend/tsconfig.json` as config, and `frontend/src/App.css` as style.
- Milestone 5 should use the demo imports and FastAPI decorators as fixtures for import graph and route extraction.
