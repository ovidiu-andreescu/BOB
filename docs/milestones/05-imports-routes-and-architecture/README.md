# Milestone 5 - Imports, Routes, And Architecture

Purpose: track the local-demo graph slice: import graph parsing, route extraction, architecture DOT generation, and Streamlit graph rendering.

## Goal

Show how important files connect and where requests enter the app.

This milestone was originally started early for demo value, then completed after scanner and detector work landed.

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
- Resolves local `../` JS/TS imports.
- Resolves alias-aware Python `ImportFrom` cases such as `from routes import trips`.
- Excludes external packages from the main dependency graph.
- Extracts FastAPI route decorators.
- Applies the demo `/api` router prefix to feature routes.
- Generates DOT strings for an architecture map and dependency graph.
- Uses `MAX_GRAPH_NODES` from `repoquest/config.py`.
- Renders graphs with `st.graphviz_chart`.
- Uses explicit light node colors to avoid blacked-out Graphviz nodes.
- Filters `__init__.py` files out of displayed architecture/dependency graph nodes.

## Current Local QC

Direct analyzer smoke checks should confirm:

- Detected routes:
  - `GET /api/recommendations`
  - `GET /api/trips`
  - `POST /api/trips`
  - `DELETE /api/trips/{trip_id}`
  - `GET /`
  - `GET /health`
- Import graph includes the expected application edges:
  - `frontend/src/main.tsx -> frontend/src/App.tsx`
  - `frontend/src/App.tsx -> frontend/src/pages/TripsPage.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/TripCard.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/components/SearchForm.tsx`
  - `frontend/src/pages/TripsPage.tsx -> frontend/src/services/api.ts`
  - `backend/main.py -> backend/routes/trips.py`
  - `backend/routes/trips.py -> backend/models/trip.py`
  - `backend/routes/trips.py -> backend/services/recommendations.py`
  - `backend/tests/test_trips.py -> backend/main.py`
- Architecture and dependency DOT generation compile successfully.
- Displayed graph DOT should not include `__init__.py` nodes as primary graph nodes.

## Carry Forward To Milestone 7

Milestone 5 is feature-complete for the MVP, but the UI should present its data more carefully:

- Exclude test files from the primary dependency graph by default. They are useful, but they make the main architecture story noisier.
- Add a separate Tests tab or test section that shows test files and their detected app-file targets.
- Add a compact dependency path summary below the graph.
- Add code/evidence previews for selected edges and routes.
- Keep root/health routes visible, but group them separately from feature routes.

## Code Evidence Examples

Use short snippets as deterministic evidence in the UI or exported report. Examples:

```python
from routes import trips

app.include_router(trips.router, prefix="/api", tags=["trips"])
```

```python
@router.get("/trips")
async def list_trips():
    ...
```

```tsx
import TripCard from "../components/TripCard";
import { getTrips, deleteTrip } from "../services/api";
```

Do not display full files. Cap previews and show the file path plus line context when available.

## Additional Suggestions

- Add a small graph summary below the visual graph, for example:
  `main.tsx -> App.tsx -> TripsPage.tsx -> api.ts -> backend/routes/trips.py`.
- Add a legend explaining colors and the dashed API boundary edge.
- Add route evidence text, such as `@router.get("/trips")`, in the route table or a route-detail expander.
- Keep root/health routes in the route table, but visually group or sort them after feature routes.
- Add a "Show tests separately" treatment so `backend/tests/test_trips.py -> backend/main.py` appears in Tests, not as a distracting main dependency edge.
- Keep the graph demo-specific and deterministic. Do not add layout libraries, external APIs, Graphviz system dependencies, or runtime AI.

## Acceptance Criteria

- Clicking "Generate Onboarding Quest" locally shows file inventory, architecture map, dependency graph, detected routes, and import statistics.
- Graph nodes render with readable labels and no blacked-out blocks.
- `__init__.py` files do not appear as primary graph nodes.
- Import statistics show nonzero Python and JS/TS local imports.
- Dependency graph includes the full frontend and backend edge set listed above.
- Route table shows `/api` feature routes plus root/health utility routes.
- Test edges are available somewhere in the UI, but not mixed into the first architecture story by default.
