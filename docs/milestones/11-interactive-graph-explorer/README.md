# Milestone 11 - Application Graph Explorer

Purpose: make the graph an application exploration surface while keeping tests out of the default architecture story.

MVP 2 phase: Deterministic Code Assistant.

## Goal

Users should select an application file/component and immediately see its role, evidence, docs, related tests, tasks, workflows, and assistant prompts.

## Graph Modes

Add explicit graph modes:

```python
GraphViewMode = Literal["application", "tests", "all_debug"]
```

- `application`: default mode. Excludes `test_*.py`, `*_test.*`, `tests/`, `__tests__/`, and similar test paths.
- `tests`: shows test files and the application files they likely cover.
- `all_debug`: shows every resolved edge for debugging and development only.

## Required Behavior

- Main architecture map and dependency graph use `application` mode by default.
- Test files must not appear in the default app graphs.
- Test relationships move to Milestone 14's Test Impact view.
- The graph model should be JSON-first, with DOT as a renderer/fallback.
- Each node id maps to `FileInfo.path`.
- Each edge includes source, target, kind, confidence, evidence, and `is_test_edge`.
- The UI should provide filters for frontend, backend, API, models, docs, config, and unknown files.

## Selected Node Panel

Selecting a node should show:

- File path, role, language, and size.
- Short summary of what the file does.
- Evidence snippets from imports, route decorators, config, or file content.
- Incoming and outgoing application dependencies.
- Related tests from Test Impact data.
- Generated docs page links.
- Related tasks and workflows.
- Bob-ready prompt for this component.

## Implementation Notes

- Start with Streamlit widgets around the existing graph if needed.
- Keep `st.graphviz_chart` as the safe fallback for Community Cloud.
- If a third-party or custom graph component is introduced later, keep the same graph JSON contract.

## Tests/Checks

- Demo repo `backend/tests/test_trips.py` does not appear in default graph output.
- Demo repo test edge appears in `tests` or `all_debug` mode.
- Application graph still includes frontend and backend production edges.
- Selected node detail can be built for `backend/routes/trips.py`, `frontend/src/pages/TripsPage.tsx`, and `frontend/src/services/api.ts`.

## Exit Criteria

- The default graph tells the production application story without test noise.
- Test dependencies are still available in a dedicated graph/view.
- Selecting a component leads directly to evidence, docs, tasks, workflows, and prompts.
