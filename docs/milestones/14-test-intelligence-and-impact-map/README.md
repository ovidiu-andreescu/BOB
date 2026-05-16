# Milestone 14 - Useful Test Intelligence

Purpose: make the Tests tab answer useful engineering questions instead of only listing test files.

MVP 2 phase: Deterministic Code Assistant.

## Goal

The Tests view should explain what exists, what app files are covered, what routes/components look untested, and what tests should be added next.

## Planned Interface

```python
@dataclass
class TestInsight:
    test_file: str
    framework: str
    imports: list[str]
    likely_targets: list[str]
    covered_routes: list[str]
    missing_cases: list[str]
    suggested_tests: list[str]
```

## Required View Sections

- **Test Inventory:** detected test files, framework hints, line counts, and assertion hints.
- **Impact Table:** test file -> imports -> likely covered app files -> covered routes/components.
- **Missing Coverage:** app routes/components/models/services with no related tests.
- **Quality Signals:** assertions found, fixtures found, skipped tests, async tests, mocked clients, and weak/no assertions.
- **Suggested Next Tests:** deterministic test cases from routes, components, services, models, and API clients.
- **Bob/Agent Test Plan:** copyable prompt and ordered steps for adding tests.

## Required Behavior

- Default application graph continues to exclude tests.
- Test files appear in this Tests view and optional graph debug mode.
- Test imports map to likely production targets when possible.
- Route coverage is inferred by matching imported app files, route files, endpoint names, and detected route paths.
- Suggestions should be concrete: "test DELETE /api/trips/{trip_id} for nonexistent id" is better than "add more tests."

## Tests/Checks

- Demo repo test file appears in Test Inventory.
- Impact Table maps `backend/tests/test_trips.py` to `backend/main.py` and likely FastAPI routes.
- Missing Coverage identifies at least one route/component or edge case worth testing.
- Suggested test plan includes validation command text but does not execute uploaded repo code inside RepoQuest.
- Exported report includes Test Intelligence and Suggested Next Tests sections.

## Exit Criteria

- Tests tab becomes an engineering tool for coverage and next-test planning.
- Test data feeds component cards, task generation, workflows, and generated docs.
