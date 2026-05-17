# RepoQuest One-Pager

## Tagline

RepoQuest turns an unfamiliar repo into a guided onboarding quest.

## Problem

Developers waste time figuring out where to start in unfamiliar codebases. They open random files, miss entry points, misunderstand architecture, and struggle to know what questions a new contributor should answer before making changes.

## Solution

RepoQuest analyzes a small codebase and generates a guided onboarding journey:

- project fingerprint
- detected frameworks
- main entry points
- architecture map
- dependency graph
- 30-minute reading path
- component/file cards
- test intelligence
- onboarding quiz
- exportable Markdown guide
- AI-ready follow-up prompts
- optional AI Fusion analysis

## What Makes It Different

RepoQuest is not a generic chatbot. It does deterministic static analysis first, then uses optional AI Fusion only when configured.

The deterministic layer provides the facts:

- scanned files
- file roles
- framework evidence
- routes
- imports
- graph data
- warnings

The AI Fusion layer provides interpretation:

- confirms or challenges project classification
- improves architecture summaries
- adds reading and component notes
- highlights risks
- recommends next actions

AI cannot rewrite hard facts unless it passes evidence checks.

## Demo Repo

The bundled demo repo is a mini React + Vite and FastAPI travel planner. It gives judges a clear full-stack story:

- frontend pages and components
- frontend API client
- backend FastAPI entry point
- backend routes
- services
- models
- tests

## Safety

RepoQuest never executes uploaded code and never installs uploaded dependencies. ZIP uploads are scanned defensively with limits for size, file count, binary files, and path traversal.

## Deployment

RepoQuest runs locally and on Streamlit Community Cloud.

Default mode requires:

- no secrets
- no external infrastructure
- no paid APIs
- no database

Optional AI mode can use Claude, a local OpenAI-compatible model server, or Ollama through the local provider settings.

## Pitch

Developers waste time figuring out unfamiliar repos. RepoQuest turns that confusion into a guided onboarding journey: it detects the project type, maps the architecture, identifies key files, creates a reading path, generates component cards, builds a quiz, and exports a Markdown guide. It is safe by default, deterministic at the evidence layer, and AI-enhanced when configured.

