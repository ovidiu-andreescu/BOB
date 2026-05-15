# Milestone 5 - Imports, Routes, And Architecture

Purpose: track import graph, route extraction, and architecture map work.

## Goal

Show how important files connect and where requests enter the app.

This is the milestone where RepoQuest should first generate the tree/graph data for the architecture map and dependency graph.

## Required Files

- `repoquest/import_graph.py`
- `repoquest/route_extractors.py`
- `repoquest/architecture.py`
- `tests/test_import_graph.py`
- `tests/test_route_extractors.py`

## Implementation Tasks

- Parse Python imports with `ast`.
- Parse basic JS/TS imports and `require(...)` calls with simple regex.
- Resolve local imports where practical.
- Mark external packages as external, but omit them from the main graph unless useful for framework evidence.
- Detect FastAPI route decorators.
- Add Flask and Express route extraction if simple.
- Generate DOT strings for architecture and dependency graphs.
- Keep the architecture map human-friendly and judge-readable.
- Limit graph size with `MAX_GRAPH_NODES`.

## Tests/Checks

- Python local imports resolve for a small fixture.
- JS/TS relative imports resolve for the demo frontend.
- FastAPI routes are extracted from demo backend.
- Graph generation respects node limit.
- DOT output is valid enough for `st.graphviz_chart`.

## Exit Criteria

- Architecture Map tab shows a human-friendly graph, technical dependency graph, and detected route table.
- Demo architecture shows the path from frontend page/API client to backend route/service/model.
- Graph data is ready for the Streamlit UI milestone to render with `st.graphviz_chart`.
