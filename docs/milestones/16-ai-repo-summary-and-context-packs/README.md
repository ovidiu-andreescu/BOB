# Milestone 16 - AI Context Packs And Component Documentation

Purpose: feed assistant mode with safe context and generate component-based documentation.

MVP 2 phase: Optional AI Code Assistant.

## Goal

Create bounded context packs and generated docs pages that can be produced deterministically first, then enhanced by optional AI.

## Planned Interface

```python
@dataclass
class GeneratedDocPage:
    title: str
    category: str
    source_files: list[str]
    content: str
    evidence: list[str]
    related_components: list[str]
```

## Context Pack Contents

- Project fingerprint.
- Framework evidence.
- Entry points.
- Application graph summary without test files.
- Test impact summary.
- Routes.
- Component cards.
- Reading path details and snippets.
- Deterministic epics/tasks/workflows.
- Warnings and skipped files.
- Short evidence snippets.

## Component Documentation Pages

Generate documentation pages like reference docs:

- API Routes reference.
- Models/Schemas reference.
- Services/business logic notes.
- Frontend pages/components reference.
- API client reference.
- Test reference.
- Agent workflows.
- Known gaps and improvement opportunities.

Each generated page should include:

- Purpose.
- Source files.
- Evidence snippets.
- Dependencies.
- Related tests.
- Improvement ideas.
- Bob/AI prompts.

## Context Pack Rules

- Never include full large files.
- Never include binary files.
- Respect size limits.
- Include file paths for citations.
- Include scan warnings and skipped-file warnings.
- Keep deterministic packs stable for the same snapshot.
- Show "what context was sent" for transparency when AI mode is enabled.

## Tests/Checks

- Context pack excludes skipped files and full large files.
- Context pack includes route evidence, component evidence, test insights, and workflows for the demo repo.
- Generated docs include API route pages and frontend component pages.
- AI-enhanced docs cite existing file paths.
- Mock AI docs with invalid citations are rejected.

## Exit Criteria

- RepoQuest can generate reference-style documentation from discovered components.
- Optional AI can enhance docs without becoming the source of truth.
