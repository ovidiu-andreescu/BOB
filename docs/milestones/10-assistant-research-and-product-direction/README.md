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

- Application-only graph by default (tests excluded from main view).
- Reading path with code/docs previews and inline evidence.
- Useful test impact and quality view (separate from application graph).
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

## MVP 2 Product Direction

### What does this application do?

MVP 2 transforms RepoQuest from "onboarding report generator" to **RepoQuest Code Assistant Workbench**.

The workbench helps developers:
1. **Understand** the application through evidence-backed analysis
2. **Improve** the codebase with deterministic task/epic/workflow generation
3. **Document** components with generated API/reference docs
4. **Test** effectively with test impact and quality analysis
5. **Delegate** work to IBM Bob or AI agents with structured workflows

### Where is the production application flow?

**Main application graph (default view):**
- Shows production code only: entrypoints, routes, services, models, pages, components, API clients
- Excludes test files, `__init__.py` package markers, and build artifacts
- Provides clean architecture visualization for understanding the running application

**Test impact view (separate tab):**
- Shows test files and their likely coverage targets
- Identifies missing test cases
- Suggests new test scenarios
- Maps tests to production code

**Debug graph mode (optional):**
- Shows everything including tests, configs, and package markers
- Useful for comprehensive dependency analysis

### What tests exist and what do they cover?

**Test Intelligence features:**
- Detect test framework (pytest, unittest, Jest, etc.)
- Parse test file imports to identify likely coverage targets
- Extract test function names and infer what they test
- Identify covered routes, services, models, and components
- Suggest missing test cases based on detected routes/components
- Generate test ideas for untested code paths

**Test Quality metrics:**
- Test file count vs production file count
- Covered vs uncovered routes
- Covered vs uncovered models
- Test-to-code ratio by role (routes, services, models)

### What should a developer read, with actual evidence?

**Enhanced Reading Path includes:**
- File path and role
- Inline code snippet (first 20-30 lines or key section)
- README/docs excerpt if relevant
- Detected routes, imports, or key patterns
- "What to understand" checklist
- "Improvement opportunities" list
- Related tasks and workflows
- AI Assistant action for deeper exploration

**Example Reading Path Item:**
```
File: backend/routes/trips.py
Role: Backend route handler

Snippet:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/trips")
async def list_trips(destination: str):
 ...
```

What to understand:
- How trip search requests are handled
- What validation is applied to destination parameter
- How recommendations service is called

Improvement opportunities:
- Add pagination support
- Add input validation for destination
- Add rate limiting

Related tasks:
- Add pagination to trip search endpoint
- Implement destination validation
- Add integration tests for trip routes

AI Assistant action:
"Review backend/routes/trips.py, identify edge cases for GET /trips, and generate pytest tests covering valid search, missing destination, and pagination."
```

### What can be improved next?

**Deterministic Epic/Task/Workflow Generator produces:**

**Epics** (high-level improvement areas):
- Add pagination to API endpoints
- Improve error handling
- Add comprehensive test coverage
- Implement input validation
- Add API documentation

**Tasks** (specific actionable items):
- Add pagination to GET /trips endpoint
- Add validation for trip destination parameter
- Write tests for trip search edge cases
- Document trip API endpoints
- Add rate limiting to search endpoint

**Workflows** (step-by-step agent instructions):
```
Workflow: Add pagination to trip search endpoint

Goal: Implement pagination for GET /trips to handle large result sets

Files to read:
- backend/routes/trips.py
- backend/services/recommendations.py
- backend/models/trip.py

Files to change:
- backend/routes/trips.py (add limit/offset parameters)
- backend/services/recommendations.py (implement pagination logic)

Steps:
1. Read current trip search implementation
2. Add limit and offset query parameters to route
3. Update recommendations service to support pagination
4. Add pagination metadata to response
5. Write tests for pagination edge cases
6. Update API documentation

Validation:
- Tests pass
- Pagination works with limit=10, offset=0
- Pagination works with limit=10, offset=10
- Invalid limit/offset values are rejected

Expected output:
- Modified backend/routes/trips.py with pagination parameters
- Modified backend/services/recommendations.py with pagination logic
- New tests in backend/tests/test_trips.py
- Updated API documentation

AI Assistant action:
"Implement pagination for GET /trips endpoint in backend/routes/trips.py. Add limit and offset query parameters, update recommendations.py service, write pytest tests, and update documentation."
```

### What tasks/workflows should IBM Bob or another coding agent follow?

**Workflow types:**
1. **Feature workflows** - Add new functionality
2. **Refactoring workflows** - Improve code quality
3. **Testing workflows** - Add test coverage
4. **Documentation workflows** - Generate/update docs
5. **Bug fix workflows** - Address identified issues

**Workflow structure:**
- Title and goal
- Files to read (for context)
- Files to change (expected modifications)
- Ordered steps
- Validation criteria
- Expected output
- AI Assistant action

**Agent-ready format:**
- Machine-readable JSON/YAML
- Clear success criteria
- Bounded scope (single feature/fix)
- Testable outcomes

### What documentation can be generated from discovered components?

**Component-based documentation:**

**API Reference** (from detected routes):
- Endpoint path and method
- Source file and function
- Detected parameters
- Related models
- Example request/response
- Related tests

**Component Reference** (from frontend components):
- Component name and path
- Detected props/interfaces
- Related pages
- Usage examples
- Related tests

**Service Reference** (from backend services):
- Service name and path
- Public functions
- Related routes and models
- Business logic summary
- Related tests

**Model Reference** (from data models):
- Model name and path
- Fields and types
- Validation rules
- Related routes and services
- Related tests

**Test Coverage Report**:
- Test files and frameworks
- Covered components
- Missing test cases
- Suggested test scenarios

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

## Bridge to Milestones 11-14

### Milestone 11 - Interactive Graph Explorer
- Implement application-only graph (exclude tests by default)
- Add test impact graph (separate view)
- Add debug graph mode (show everything)
- Support node selection and filtering
- Generate JSON graph model for future interactivity

### Milestone 12 - Evidence Preview Workbench
- Add inline code snippets to reading path
- Add README/docs excerpts
- Show detected routes, imports, patterns
- Add "what to understand" checklists
- Add "improvement opportunities" lists
- Add related tasks and workflows

### Milestone 13 - Deterministic Epic/Task/Workflow Generator
- Generate epics from detected patterns
- Generate tasks from improvement opportunities
- Generate agent-ready workflows
- Include validation criteria
- Include AI Assistant actions
- Export as JSON/YAML

### Milestone 14 - Test Intelligence and Impact Map
- Detect test frameworks
- Parse test imports and targets
- Identify covered vs uncovered code
- Suggest missing test cases
- Generate test quality metrics
- Map tests to production code

## Exit Criteria

- MVP 2 is clearly named RepoQuest Code Assistant Workbench.
- Deterministic assistant features are the next target.
- Optional AI is defined as testable, evidence-linked, and disabled by default.
- The rest of the MVP 2 milestones can be implemented without product ambiguity.
- Product direction answers all key questions with concrete examples.
- Bridge to Milestones 11-14 is clear and actionable.
