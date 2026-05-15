# Milestone 5 - Imports, Routes, And Architecture

Purpose: track the local-demo graph slice: import graph parsing, FastAPI route extraction, architecture DOT generation, and Streamlit graph rendering.

## Goal

Show how important files connect and where requests enter the app.

This milestone intentionally jumped ahead of Milestones 3 and 4 for local demo value. ZIP upload remains disabled, and full framework detection remains deferred.

## Implemented Files

- `repoquest/import_graph.py`
- `repoquest/route_extractors.py`
- `repoquest/architecture.py`
- `tests/test_import_graph.py`
- `tests/test_route_extractors.py`
- `tests/test_architecture.py`

## Implemented Behavior

- Parses Python imports with `ast`.
- Parses basic JS/TS imports with regex.
- Excludes external packages from the main dependency graph.
- Extracts FastAPI route decorators.
- Applies the demo `/api` router prefix to feature routes.
- Generates DOT strings for an architecture map and dependency graph.
- Uses `MAX_GRAPH_NODES` from `repoquest/config.py`.
- Renders graphs in the current local Streamlit page with `st.graphviz_chart`.
- Uses explicit light node colors to avoid blacked-out Graphviz nodes.
- Filters `__init__.py` files out of displayed architecture/dependency graph nodes.

## Current Local QC

Direct analyzer smoke check from the current files:

- Detected routes:
  - `GET /api/recommendations`
  - `GET /api/trips`
  - `POST /api/trips`
  - `DELETE /api/trips/{trip_id}`
  - `GET /`
  - `GET /health`
- Import graph currently returns 6 local edges:
  - `frontend/src/main.tsx -> frontend/src/App.tsx`
  - `frontend/src/App.tsx -> frontend/src/pages/TripsPage.tsx`
  - `backend/main.py -> backend/routes/__init__.py`
  - `backend/tests/test_trips.py -> backend/main.py`
  - `backend/routes/trips.py -> backend/models/trip.py`
  - `backend/routes/trips.py -> backend/services/recommendations.py`
- Architecture and dependency DOT generation compile successfully.
- Displayed graph DOT no longer includes `__init__.py` nodes, but one underlying edge still resolves through `backend/routes/__init__.py`.

## Remaining Milestone 5 Fixes

These should be fixed before calling Milestone 5 fully done.

- JS/TS path normalization still misses imports containing `..`, such as:
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/TripCard.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/SearchForm.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/services/api.ts`
- Python package import resolution still needs alias-aware `ImportFrom` handling:
  - `from routes import trips` should resolve to `backend/routes/trips.py`, not `backend/routes/__init__.py`.
- Dependency graph should include the complete expected demo relationship set:
  - `frontend/src/main.tsx -> frontend/src/App.tsx`
  - `frontend/src/App.tsx -> frontend/src/pages/TripsPage.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/TripCard.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/SearchForm.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/services/api.ts`
  - `backend/main.py -> backend/routes/trips.py`
  - `backend/routes/trips.py -> backend/services/recommendations.py`
  - `backend/routes/trips.py -> backend/models/trip.py`
  - `backend/tests/test_trips.py -> backend/main.py`
- The architecture map should be generated from resolved import edges plus one intentional dashed API edge, instead of hard-coded file-name relationships wherever possible.
- The visible Streamlit server should be restarted after graph-code changes until local `runOnSave` is fixed in Milestone 1 cleanup.

## Additional Suggestions

- Add a small graph summary below the visual graph, for example:
  `main.tsx -> App.tsx -> TripsPage.tsx -> api.ts -> backend/routes/trips.py`.
- Add a legend explaining colors and the dashed API boundary edge.
- Add route evidence text, such as `@router.get("/trips")`, in the route table or a route-detail expander.
- Keep root/health routes in the route table, but visually group or sort them after feature routes.
- Keep the graph demo-specific and deterministic. Do not add layout libraries, external APIs, Graphviz system dependencies, or runtime AI.

## Acceptance Criteria

- Clicking "Generate Onboarding Quest" locally shows file inventory, architecture map, dependency graph, detected routes, and import statistics.
- Graph nodes render with readable labels and no blacked-out blocks.
- `__init__.py` files do not appear as primary graph nodes.
- Import statistics show nonzero Python and JS/TS local imports.
- Dependency graph includes the full frontend and backend edge set listed above.
- Route table shows `/api` feature routes plus root/health utility routes.
- ZIP upload remains disabled.
