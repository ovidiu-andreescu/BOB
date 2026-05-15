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
