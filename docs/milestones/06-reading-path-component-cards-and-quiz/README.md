# Milestone 6 - Reading Path, Component Cards, And Quiz

Purpose: track onboarding path, component card, and quiz generation work.

## Goal

Turn static analysis into a guided onboarding journey.

## Required Files

- `repoquest/reading_path.py`
- `repoquest/quest.py`
- `tests/test_reading_path.py`

## Implementation Tasks

- Generate a 30-minute reading path.
- Start with `README.md` when present.
- Prioritize backend entry, routes, services, models, frontend entry, pages, API client, components, and tests for full-stack repos.
- Generate component/file cards for important files.
- Include connections, detected routes/items, why it matters, test ideas, and Bob-ready prompts.
- Use careful phrases like "likely role" and "detected evidence."
- Generate 4-8 deterministic quiz questions.

## Tests/Checks

- Reading path starts with `README.md` for demo repo.
- Reading path includes backend route file.
- Reading path includes frontend entry or page file.
- Component card for backend route includes detected routes.
- Quiz includes a question about the route file or frontend entry point.

## Exit Criteria

- The app feels like an onboarding quest, not just a file table.
- A new contributor can follow the generated path without needing a chatbot.
