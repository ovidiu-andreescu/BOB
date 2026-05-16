# Milestone 11 - Application Graph Explorer

Purpose: make the graph an application exploration surface while keeping tests out of the default architecture story.

MVP 2 phase: Deterministic Code Assistant.

## Goal

Users should inspect the application graph, switch between application/tests/debug modes, and select a file/component to see role, metadata, dependencies, routes, related tests, and optional assistant actions.

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
- The UI exposes view mode and max-node controls only. Role filtering remains internal and is not shown in the product UI.
- The rendered graph shows connected nodes only so config/docs files do not float disconnected from the application story.
- The DOT graph uses a horizontal layout with an embedded legend. Legend labels must stay short enough to avoid overflow.
- The dashed API boundary legend appears only when a dashed API edge is actually rendered.

## Selected Node Panel

Selecting a node should show:

- File path, role, language, and size.
- Short summary of what the file does.
- Incoming and outgoing application dependencies.
- Related tests from Test Impact data.
- Related routes.
- Optional AI Assistant action for this file.

Code previews do not belong in the Architecture Map inspector. Full file preview and fullscreen reading controls live in the Reading Path workbench.

## Implementation Notes

- Start with Streamlit widgets around the existing graph if needed.
- Keep `st.graphviz_chart` as the safe fallback for Community Cloud.
- If a third-party or custom graph component is introduced later, keep the same graph JSON contract.

## Tests/Checks

- Demo repo `backend/tests/test_trips.py` does not appear in default graph output.
- Demo repo test edge appears in `tests` or `all_debug` mode.
- Application graph still includes frontend and backend production edges.
- Application graph has no disconnected orphan nodes.
- Graph legend includes only roles present in the graph.
- Tests mode includes a purple Tests legend row when test nodes are present.
- No stale "Backend route/service" overflow label appears in the legend.
- Architecture inspector does not show a code preview.
- Selected node detail can be built for `backend/routes/trips.py`, `frontend/src/pages/TripsPage.tsx`, and `frontend/src/services/api.ts`.

## Exit Criteria

- The default graph tells the production application story without test noise.
- Test dependencies are still available in a dedicated graph/view.
- Selecting a component leads directly to dependencies, route context, related tests, and optional assistant actions.
- The input/sidebar controls are hidden after analysis so graph exploration has room on the page.
