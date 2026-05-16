# Milestone 17 - AI Code Recommendations And Agent Workflows

Purpose: use optional AI mode for code-assistance recommendations grounded in RepoQuest evidence.

MVP 2 phase: Optional AI Code Assistant.

## Goal

Generate AI-assisted epics, tasks, workflows, test plans, documentation plans, and code recommendations that a developer or IBM Bob can act on.

## Outputs

- Application summary.
- Suggested epics and milestones.
- Task backlog.
- Agent workflows.
- Test plans.
- Component documentation plans.
- Code recommendation cards.
- Copyable IBM Bob prompts.

## Recommendation Schema

```python
@dataclass
class CodeRecommendation:
    title: str
    category: str
    priority: str
    files: list[str]
    evidence: list[str]
    rationale: str
    proposed_change_summary: str
    test_plan: list[str]
    workflow: str
    confidence: float
```

## Guardrails

- Do not generate patches in this milestone.
- Do not claim tests pass unless verified separately.
- Require evidence file paths for every recommendation.
- Mark AI suggestions as suggestions, not facts.
- Show deterministic tasks beside AI-enhanced tasks.
- Reject or downgrade uncited recommendations.

## UI Requirements

- Add an Assistant Recommendations view only when assistant mode is enabled.
- Group recommendations by epic, task type, and priority.
- Show source evidence next to every recommendation.
- Provide copyable agent workflows and Bob prompts.
- Show validation status for AI outputs.
- Make it obvious which items are deterministic and which are AI-assisted.

## Tests/Checks

- Mock provider produces schema-valid workflows and code recommendations for the demo repo.
- Every AI recommendation links to existing file evidence.
- AI recommendation without evidence is not shown as trusted.
- AI output referencing nonexistent files is rejected.
- Deterministic task generator still works when assistant mode is disabled.

## Exit Criteria

- Assistant mode feels like a code assistant, not only a summarizer.
- AI recommendations are actionable, evidence-linked, and visibly validated.
