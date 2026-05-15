# Milestone 4 - Framework Detection And Repo Fingerprint

Purpose: track deterministic framework detection, entry point detection, and project fingerprinting work.

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
