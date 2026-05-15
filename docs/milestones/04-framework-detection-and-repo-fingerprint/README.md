# Milestone 4 - Framework Detection And Repo Fingerprint

Purpose: track deterministic framework detection, entry point detection, and project fingerprinting work.

Status: implemented for the MVP. Milestone 7 should now make the findings easier to read in the Overview tab.

## Goal

Turn file inventory into a clear answer to "what kind of codebase is this?"

## Required Files

- `repoquest/framework_rules.py`
- `repoquest/detectors.py`
- `tests/test_detectors.py`

## Implementation Tasks

- Detect React/Vite, Next.js, Express, FastAPI, Flask, Streamlit, Django, Python packages, and CLI/tooling projects with deterministic evidence.
- Classify project type with confidence.
- Detect and rank entry points.
- Detect key folders.
- Return evidence strings for every framework finding.
- Use cautious language when confidence is low.
- Do not claim certainty unless evidence supports it.

## Tests/Checks

- Demo repo detects React/Vite.
- Demo repo detects FastAPI.
- Demo repo is classified as a full-stack web application.
- Streamlit fixture detects Streamlit.
- Unknown fixture falls back without overclaiming.
- Entry point detection includes at least one frontend and one backend entry point for the demo repo.

## Exit Criteria

- Overview tab can show project type, confidence, frameworks, entry points, key folders, and warnings.
- Demo repo fingerprint clearly says it is a React/Vite + FastAPI full-stack web application.

## Carry Forward To UI

- Show framework evidence as short, inspectable claims rather than a raw file dump.
- Link each entry point to its component card or preview when possible.
- Keep cautious fallback language for unknown or mixed repos.
