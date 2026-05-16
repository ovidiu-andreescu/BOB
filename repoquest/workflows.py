"""Generate actionable work plans, tasks, and agent workflows from repo analysis."""

from repoquest.models import (
  RepositorySnapshot,
  ProjectFingerprint,
  RouteInfo,
  ImportEdge,
  ReadingPathItem,
  ComponentCard,
  TaskSuggestion,
  AgentWorkflow,
  SuggestedMilestone,
  WorkPlan,
)
from repoquest.response_templates import get_work_plan_epic_goal


def _is_visible_analysis_file(file_info) -> bool:
  """Return whether a file should be used in deterministic work-plan output."""
  return not file_info.skipped and not (file_info.name == "__init__.py" and file_info.line_count < 50)


def _file_paths_by_role(snapshot: RepositorySnapshot, role: str) -> list[str]:
  """Return visible file paths for a role."""
  return [file_info.path for file_info in snapshot.files
      if file_info.role == role and _is_visible_analysis_file(file_info)]


def _readme_paths(snapshot: RepositorySnapshot) -> list[str]:
  """Return visible README paths using their actual repo-relative locations."""
  return [
    file_info.path for file_info in snapshot.files
    if file_info.name.lower() == "readme.md" and _is_visible_analysis_file(file_info)
  ]


def generate_task_suggestions(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
  import_edges: list[ImportEdge],
  reading_path: list[ReadingPathItem],
  component_cards: list[ComponentCard],
) -> list[TaskSuggestion]:
  """
  Generate deterministic task suggestions based on repo analysis.

  Args:
    snapshot: Repository snapshot
    fingerprint: Project fingerprint
    routes: Detected API routes
    import_edges: Import relationships
    reading_path: Suggested reading path
    component_cards: Component cards

  Returns:
    List of TaskSuggestion objects
  """
  tasks = []

  backend_routes = _file_paths_by_role(snapshot, "backend_route")
  backend_services = _file_paths_by_role(snapshot, "backend_service")
  models = _file_paths_by_role(snapshot, "model")
  api_clients = _file_paths_by_role(snapshot, "api_client")
  frontend_pages = _file_paths_by_role(snapshot, "frontend_page")
  frontend_components = _file_paths_by_role(snapshot, "frontend_component")
  test_files = _file_paths_by_role(snapshot, "test")

  # Task 1: Expand backend route tests
  if backend_routes and routes:
    evidence = [
      f"Detected {len(routes)} API routes",
      f"Found {len(backend_routes)} route files",
    ]
    if test_files:
      evidence.append(f"Existing tests found in {len(test_files)} files")
    else:
      evidence.append("No test files detected")

    tasks.append(TaskSuggestion(
      epic="Testing & Quality",
      priority="high",
      files=backend_routes + test_files,
      evidence=evidence,
      why="API routes are the entry points to backend functionality. Comprehensive tests ensure reliability and catch edge cases.",
      acceptance_criteria=[
        "Tests cover all detected routes",
        "Tests include edge cases (missing fields, invalid data)",
        "Tests verify error responses",
        "All tests pass",
      ],
      suggested_workflow="Add missing edge-case tests for API routes",
    ))

  # Task 2: Document API endpoints
  if backend_routes and routes:
    readme_files = _readme_paths(snapshot)
    evidence = [
      f"Detected {len(routes)} API routes",
      f"README found: {', '.join(readme_files[:3])}" if readme_files else "README.md not found",
    ]

    tasks.append(TaskSuggestion(
      epic="Documentation",
      priority="medium",
      files=backend_routes + readme_files,
      evidence=evidence,
      why="API documentation helps developers understand available endpoints, request/response formats, and usage examples.",
      acceptance_criteria=[
        "All routes documented with method and path",
        "Request parameters documented",
        "Response formats documented",
        "Example requests included",
      ],
      suggested_workflow="Generate API documentation",
    ))

  # Task 3: Harden API client error handling
  if api_clients:
    evidence = [
      f"Found {len(api_clients)} API client files",
      "API clients handle frontend-backend communication",
    ]

    tasks.append(TaskSuggestion(
      epic="Reliability & Error Handling",
      priority="high",
      files=api_clients,
      evidence=evidence,
      why="Robust error handling in API clients improves user experience by gracefully handling network failures and API errors.",
      acceptance_criteria=[
        "All API calls have error handling",
        "Network timeouts handled",
        "User-friendly error messages",
        "Retry logic for transient failures",
      ],
      suggested_workflow="Improve API client error handling",
    ))

  # Task 4: Add model validation
  if models:
    evidence = [
      f"Found {len(models)} data model files",
      "Models define data structures",
    ]

    tasks.append(TaskSuggestion(
      epic="Data Integrity",
      priority="medium",
      files=models,
      evidence=evidence,
      why="Data validation at the model level prevents invalid data from entering the system and catches bugs early.",
      acceptance_criteria=[
        "Required fields validated",
        "Data types validated",
        "Constraints enforced",
        "Validation tests added",
      ],
      suggested_workflow="Add model validation rules",
    ))

  # Task 5: Improve UI component accessibility
  if frontend_components or frontend_pages:
    ui_files = frontend_components + frontend_pages
    evidence = [
      f"Found {len(ui_files)} UI files",
      "Accessibility improves usability for all users",
    ]

    tasks.append(TaskSuggestion(
      epic="Accessibility & UX",
      priority="medium",
      files=ui_files[:5], # Limit to first 5
      evidence=evidence,
      why="Accessible components ensure the application is usable by everyone, including users with disabilities.",
      acceptance_criteria=[
        "ARIA labels added where needed",
        "Keyboard navigation works",
        "Color contrast meets standards",
        "Screen reader friendly",
      ],
      suggested_workflow="Accessibility audit and improvements",
    ))

  # Task 6: Add service layer tests
  if backend_services:
    evidence = [
      f"Found {len(backend_services)} service files",
      "Services contain business logic",
    ]
    if test_files:
      evidence.append(f"Existing tests found")

    tasks.append(TaskSuggestion(
      epic="Testing & Quality",
      priority="medium",
      files=backend_services + test_files,
      evidence=evidence,
      why="Service layer tests verify business logic correctness and catch edge cases in data processing.",
      acceptance_criteria=[
        "Unit tests for each service function",
        "Edge cases covered",
        "Error handling tested",
        "All tests pass",
      ],
      suggested_workflow="Add service layer unit tests",
    ))

  # Task 7: Improve onboarding documentation
  readme_files = _readme_paths(snapshot)
  if readme_files:
    evidence = [
      "README.md exists",
      f"Project type: {fingerprint.project_type}",
    ]

    tasks.append(TaskSuggestion(
      epic="Documentation",
      priority="low",
      files=readme_files,
      evidence=evidence,
      why="Clear onboarding documentation helps new contributors get started quickly and reduces onboarding time.",
      acceptance_criteria=[
        "Setup instructions clear and complete",
        "Architecture overview included",
        "Common tasks documented",
        "Troubleshooting section added",
      ],
      suggested_workflow="Enhance README and onboarding docs",
    ))

  return tasks


def generate_agent_workflows(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
  tasks: list[TaskSuggestion],
  component_cards: list[ComponentCard],
) -> list[AgentWorkflow]:
  """
  Generate agent-ready workflows from tasks and repo analysis.

  Args:
    snapshot: Repository snapshot
    fingerprint: Project fingerprint
    routes: Detected API routes
    tasks: Generated task suggestions
    component_cards: Component cards

  Returns:
    List of AgentWorkflow objects
  """
  workflows = []

  backend_routes = _file_paths_by_role(snapshot, "backend_route")
  test_files = _file_paths_by_role(snapshot, "test")
  api_clients = _file_paths_by_role(snapshot, "api_client")

  # Workflow 1: Add route edge-case tests
  if backend_routes and routes:
    route_file = backend_routes[0]
    test_file = test_files[0] if test_files else f"{route_file.replace('.py', '_test.py')}"

    route_list = [f"{r.method} {r.path}" for r in routes[:3]]

    workflows.append(AgentWorkflow(
      title="Add missing edge-case tests for API routes",
      goal="Ensure all API routes have comprehensive test coverage including edge cases",
      ordered_steps=[
        "Read the route file to understand endpoint implementations",
        "Read existing test file to see current coverage",
        "Identify missing test cases (invalid inputs, missing fields, edge cases)",
        "Add new test functions for uncovered scenarios",
        "Run pytest to verify all tests pass",
      ],
      files_to_read=[route_file] + (test_files[:1] if test_files else []),
      files_to_change=[test_file],
      validation_steps=[
        "In a trusted local clone: Run pytest -v",
        "Verify all new tests pass",
        "Check test coverage increased",
      ],
      expected_output="Updated test file with comprehensive edge-case coverage for all routes",
      prompt=f"""Analyze {route_file} which contains these routes: {', '.join(route_list)}.

Review the existing tests in {test_file if test_files else 'the test directory'}.

Add pytest tests for these edge cases:
1. Missing required fields
2. Invalid data types
3. Deleting non-existent resources
4. Boundary conditions

Ensure tests are clear, well-documented, and follow existing test patterns.

Do not execute the uploaded code. Only analyze and generate tests.""",
    ))

  # Workflow 2: Improve API client error handling
  if api_clients:
    api_client = api_clients[0]

    workflows.append(AgentWorkflow(
      title="Improve frontend API client error handling",
      goal="Add robust error handling, timeouts, and user-friendly error messages to API client",
      ordered_steps=[
        "Read the API client file to understand current implementation",
        "Identify API calls without proper error handling",
        "Add try-catch blocks with specific error types",
        "Add timeout handling",
        "Add user-friendly error messages",
        "Consider adding retry logic for transient failures",
      ],
      files_to_read=[api_client],
      files_to_change=[api_client],
      validation_steps=[
        "For the developer's own trusted repo: Test with network disconnected",
        "Test with slow network (timeout scenarios)",
        "Test with API returning errors",
        "Verify user sees helpful error messages",
      ],
      expected_output="API client with comprehensive error handling and user-friendly messages",
      prompt=f"""Review {api_client} and improve error handling.

Add:
1. Try-catch blocks for all API calls
2. Timeout handling (e.g., 10 second timeout)
3. Specific error types (NetworkError, TimeoutError, APIError)
4. User-friendly error messages
5. Optional: Retry logic for transient failures

Maintain existing functionality while adding robustness.

Do not execute the uploaded code. Only analyze and suggest improvements.""",
    ))

  # Workflow 3: Document API routes
  if backend_routes and routes:
    readme_files = _readme_paths(snapshot)
    readme_file = readme_files[0] if readme_files else "README.md"

    route_list = "\n".join([f"- {r.method} {r.path}" for r in routes[:5]])

    workflows.append(AgentWorkflow(
      title="Generate API documentation",
      goal="Create comprehensive API documentation for all detected routes",
      ordered_steps=[
        "Read route files to understand endpoint implementations",
        "Extract request/response schemas",
        "Document each endpoint with method, path, parameters, and responses",
        "Add example requests and responses",
        "Update README.md with API documentation section",
      ],
      files_to_read=backend_routes[:3],
      files_to_change=[readme_file],
      validation_steps=[
        "Verify all routes documented",
        "Check examples are accurate",
        "Ensure formatting is clear",
      ],
      expected_output="README.md with complete API documentation section",
      prompt=f"""Analyze these route files: {', '.join(backend_routes[:3])}.

Detected routes:
{route_list}

Generate API documentation including:
1. Endpoint list with HTTP methods and paths
2. Request parameters and body schemas
3. Response formats
4. Example requests using curl or similar
5. Error responses

Add this documentation to {readme_file} in a new "API Documentation" section.

Do not execute the uploaded code. Only analyze and generate documentation.""",
    ))

  return workflows


def group_tasks_into_milestones(tasks: list[TaskSuggestion]) -> list[SuggestedMilestone]:
  """
  Group tasks into logical milestones based on epics.

  Args:
    tasks: List of task suggestions

  Returns:
    List of SuggestedMilestone objects
  """
  # Group tasks by epic
  epic_tasks: dict[str, list[TaskSuggestion]] = {}
  for task in tasks:
    if task.epic not in epic_tasks:
      epic_tasks[task.epic] = []
    epic_tasks[task.epic].append(task)

  milestones = []

  # Create milestone for each epic
  for epic, epic_task_list in epic_tasks.items():
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    epic_task_list.sort(key=lambda t: priority_order.get(t.priority, 3))

    milestones.append(SuggestedMilestone(
      title=f"Milestone: {epic}",
      goal=get_work_plan_epic_goal(epic),
      tasks=epic_task_list,
    ))

  # Sort milestones by priority (based on highest priority task in each)
  def milestone_priority(m: SuggestedMilestone) -> int:
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return min(priority_order.get(t.priority, 3) for t in m.tasks)

  milestones.sort(key=milestone_priority)

  return milestones


def generate_work_plan(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
  routes: list[RouteInfo],
  import_edges: list[ImportEdge],
  reading_path: list[ReadingPathItem],
  component_cards: list[ComponentCard],
) -> WorkPlan:
  """
  Generate a complete work plan with epics, tasks, milestones, and workflows.

  Args:
    snapshot: Repository snapshot
    fingerprint: Project fingerprint
    routes: Detected API routes
    import_edges: Import relationships
    reading_path: Suggested reading path
    component_cards: Component cards

  Returns:
    WorkPlan object
  """
  # Generate tasks
  tasks = generate_task_suggestions(
    snapshot, fingerprint, routes, import_edges, reading_path, component_cards
  )

  # Extract unique epics
  epics = list(dict.fromkeys(task.epic for task in tasks))

  # Generate workflows
  workflows = generate_agent_workflows(
    snapshot, fingerprint, routes, tasks, component_cards
  )

  # Group into milestones
  milestones = group_tasks_into_milestones(tasks)

  return WorkPlan(
    epics=epics,
    tasks=tasks,
    milestones=milestones,
    workflows=workflows,
  )


def export_workflows_markdown(work_plan: WorkPlan, project_name: str) -> str:
  """
  Export work plan as Markdown.

  Args:
    work_plan: WorkPlan object
    project_name: Name of the project

  Returns:
    Markdown string
  """
  lines = [
    f"# RepoQuest Work Plan: {project_name}",
    "",
    "This work plan was generated by RepoQuest based on deterministic repository analysis.",
    "",
    "## Summary",
    "",
    f"- **Epics**: {len(work_plan.epics)}",
    f"- **Tasks**: {len(work_plan.tasks)}",
    f"- **Milestones**: {len(work_plan.milestones)}",
    f"- **Agent Workflows**: {len(work_plan.workflows)}",
    "",
  ]

  # Epics
  lines.extend([
    "## Epics",
    "",
  ])
  for epic in work_plan.epics:
    epic_tasks = [t for t in work_plan.tasks if t.epic == epic]
    lines.append(f"- **{epic}** ({len(epic_tasks)} tasks)")
  lines.append("")

  # Milestones
  lines.extend([
    "## Suggested Milestones",
    "",
  ])
  for milestone in work_plan.milestones:
    lines.extend([
      f"### {milestone.title}",
      "",
      f"**Goal**: {milestone.goal}",
      "",
      f"**Tasks** ({len(milestone.tasks)}):",
      "",
    ])
    for task in milestone.tasks:
      lines.append(f"- [{task.priority.upper()}] {task.why}")
    lines.append("")

  # Tasks
  lines.extend([
    "## Tasks",
    "",
  ])
  for task in work_plan.tasks:
    lines.extend([
      f"### {task.epic}: {task.why[:80]}...",
      "",
      f"**Priority**: {task.priority}",
      "",
      "**Files**:",
      "",
    ])
    for file in task.files[:5]:
      lines.append(f"- `{file}`")
    lines.extend([
      "",
      "**Evidence**:",
      "",
    ])
    for evidence in task.evidence:
      lines.append(f"- {evidence}")
    lines.extend([
      "",
      "**Why it matters**:",
      "",
      task.why,
      "",
      "**Acceptance Criteria**:",
      "",
    ])
    for criterion in task.acceptance_criteria:
      lines.append(f"- {criterion}")
    lines.extend([
      "",
      "---",
      "",
    ])

  # Workflows
  lines.extend([
    "## Agent Workflows",
    "",
    "These workflows are ready to use with an AI coding assistant.",
    "",
  ])
  for workflow in work_plan.workflows:
    lines.extend([
      f"### Workflow: {workflow.title}",
      "",
      f"**Goal**: {workflow.goal}",
      "",
      "**Files to read**:",
      "",
    ])
    for file in workflow.files_to_read:
      lines.append(f"- `{file}`")
    lines.extend([
      "",
      "**Files likely to change**:",
      "",
    ])
    for file in workflow.files_to_change:
      lines.append(f"- `{file}`")
    lines.extend([
      "",
      "**Ordered steps**:",
      "",
    ])
    for i, step in enumerate(workflow.ordered_steps, 1):
      lines.append(f"{i}. {step}")
    lines.extend([
      "",
      "**Validation steps**:",
      "",
    ])
    for step in workflow.validation_steps:
      lines.append(f"- {step}")
    lines.extend([
      "",
      f"**Expected output**: {workflow.expected_output}",
      "",
      "**AI Assistant Action**:",
      "",
      "```",
      workflow.prompt,
      "```",
      "",
      "---",
      "",
    ])

  return "\n".join(lines)

# Made with Bob
