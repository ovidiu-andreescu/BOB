# Milestone 7 - Streamlit Demo UI

Purpose: track the Streamlit interface and 1-2 minute demo flow work.

## Goal

Make the app demoable in 1-2 minutes.

This is the milestone where the tree/graph display should become visible in the running Streamlit app.

## Required Files

- `app/streamlit_app.py`

## Implementation Tasks

- Add input mode for demo repo and ZIP upload.
- Add a single "Generate Onboarding Quest" action.
- Add tabs: Overview, Architecture Map, Reading Path, Components, Quest & Quiz, Export, Built with IBM Bob.
- Show limits in the sidebar.
- Keep the first result screen focused on project type and framework evidence.
- Use `st.graphviz_chart` for graphs.
- Use `st.download_button` for Markdown export.
- Include a Built with IBM Bob section without implying runtime AI usage.
- Keep the demo flow clear before adding polish.

## Tests/Checks

- Demo repo flow produces useful output within seconds.
- Invalid ZIP produces a friendly error.
- Empty/unknown repo still produces a cautious fallback.
- No UI text mentions private development tools or hidden review process.

## Exit Criteria

- Judge can understand the product in one short live demo.
- Main tabs match the required RepoQuest flow.
- Architecture and dependency graphs render in the Architecture Map tab.
