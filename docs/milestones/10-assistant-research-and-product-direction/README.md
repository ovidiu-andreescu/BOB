# Milestone 10 - MVP 2 Code Assistant Direction

Purpose: define MVP 2 as a capable code assistant workbench, not a loose set of polish tasks.

MVP 2 phase: Product direction.

## Goal

Reframe RepoQuest around helping a developer understand, improve, document, test, and hand work to IBM Bob or another AI coding agent.

MVP 1 is complete and remains the deterministic hackathon-safe app. MVP 2 should build on it without making runtime AI mandatory.

## Product Thesis

RepoQuest Code Assistant Workbench should answer:

- What does this application do?
- Where is the production application flow?
- What tests exist and what do they actually cover?
- What should a developer read, with actual code/docs excerpts?
- What can be improved next?
- What tasks, milestones, and workflows should Bob or an AI agent follow?
- What documentation can be generated from the discovered components?

## MVP 2 Product Layers

### Deterministic Code Assistant

- Application-only graph by default.
- Reading path with code/docs previews.
- Useful test impact and quality view.
- Deterministic epics, tasks, milestones, and workflows.
- Component-based generated documentation.
- Clean UI separation between RepoQuest meta and analyzed repo data.
- No secrets and no runtime AI required.

### Optional Testable AI

- Disabled by default.
- Uses bounded context packs, not raw repos.
- Produces schema-shaped summaries, docs, tasks, workflows, and recommendations.
- Uses a mock provider for tests.
- Requires citations to deterministic file evidence.
- Fails closed when output is invalid, uncited, or references nonexistent paths.

## Research Notes

- `st.graphviz_chart` is useful as a fallback renderer, but a graph workbench needs a JSON graph model and node-selection UI.
- Streamlit custom components can support bidirectional graph interactions if a later version needs true clickable graph nodes.
- Streamlit secrets can support optional hosted assistant mode, but the default demo must not require secrets.
- Structured AI outputs are important because workflows, tasks, docs pages, and recommendations must be machine-checkable.
- AI should synthesize from RepoQuest's deterministic scan, not inspect the repo directly.

Useful references:

- Streamlit custom components: https://docs.streamlit.io/develop/api-reference/custom-components
- Streamlit chart elements and GraphViz: https://docs.streamlit.io/develop/api-reference/charts
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI API authentication: https://developers.openai.com/api/reference/overview

## Exit Criteria

- MVP 2 is clearly named RepoQuest Code Assistant Workbench.
- Deterministic assistant features are the next target.
- Optional AI is defined as testable, evidence-linked, and disabled by default.
- The rest of the MVP 2 milestones can be implemented without product ambiguity.
