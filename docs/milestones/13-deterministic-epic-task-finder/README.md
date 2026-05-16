# Milestone 13 - Epic, Task, Milestone, And Agent Workflow Generator

Purpose: generate actionable work plans for developers, IBM Bob, and AI coding agents.

MVP 2 phase: Deterministic Code Assistant.

## Goal

Turn static repo findings into epics, tasks, milestones, and agent-ready workflows.

This is a key hackathon differentiator: RepoQuest should not only explain a repo, it should produce structured work that a coding assistant can follow.

## Planned Interfaces

```python
@dataclass
class TaskSuggestion:
    epic: str
    priority: str
    files: list[str]
    evidence: list[str]
    why: str
    acceptance_criteria: list[str]
    suggested_workflow: str

@dataclass
class AgentWorkflow:
    title: str
    goal: str
    ordered_steps: list[str]
    files_to_read: list[str]
    files_to_change: list[str]
    validation_steps: list[str]
    expected_output: str
    prompt: str
```

## Workflow Types

Generate deterministic workflows for:

- Onboarding walkthrough.
- Bug hunt.
- Test expansion.
- API documentation generation.
- Component documentation generation.
- Refactor preparation.
- Feature implementation.
- Accessibility pass.
- Error-handling hardening.

## Required Behavior

- Group tasks into epics.
- Group epics into suggested milestones.
- Link every task and workflow to files and evidence.
- Provide acceptance criteria for tasks.
- Provide validation steps for workflows.
- Export workflows as Markdown prompts for IBM Bob or another AI coding agent.
- Keep deterministic workflows separate from optional AI-generated workflows.

## Example Workflow Shape

```text
Goal: Add missing edge-case tests for trip routes.
Files to read: backend/routes/trips.py, backend/tests/test_trips.py
Files likely to change: backend/tests/test_trips.py
Steps:
1. Inspect detected routes and current tests.
2. Add tests for missing destination and deleting a nonexistent trip.
3. Run pytest.
Expected output: updated pytest coverage for route edge cases.
```

## Tests/Checks

- Demo repo produces deterministic epics, tasks, and at least three workflows.
- Workflow export includes files to read, files to change, validation steps, expected output, and prompt.
- Every generated task has file evidence.
- No workflow asks an agent to execute uploaded code inside RepoQuest.

## Exit Criteria

- RepoQuest can hand a developer or AI agent a clear next-work plan.
- Generated work is grounded in the repo snapshot and does not invent unsupported behavior.
