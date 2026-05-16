"""Reusable deterministic text templates for RepoQuest outputs.

This module keeps "what to say" separate from analysis code. The templates are
role-based and generic; they should not depend on the bundled demo repo.
"""

from dataclasses import dataclass

from repoquest.models import FileInfo, RouteInfo


@dataclass(frozen=True)
class RoleResponseTemplate:
  """Deterministic copy and display metadata for a file role."""

  role: str
  label: str
  reading_priority: int
  reading_reason: str
  why_it_matters: str
  understand_points: tuple[str, ...]
  improvement_ideas: tuple[str, ...]
  test_ideas: tuple[str, ...] = ()
  assistant_action: str = (
    "Explain {path} and its role in the application, then suggest improvements and tests."
  )


ROLE_TEMPLATES = {
  "documentation": RoleResponseTemplate(
    role="documentation",
    label="Documentation",
    reading_priority=0,
    reading_reason="Provides context and documentation for the project",
    why_it_matters="This file explains project purpose, setup, or usage.",
    understand_points=(
      "Documented concepts and workflows",
      "API or component usage examples",
      "Configuration options",
    ),
    improvement_ideas=(
      "Add code examples where missing",
      "Update outdated information",
      "Add links to related docs",
    ),
    assistant_action="Review {path} and suggest improvements: missing sections, outdated info, or unclear explanations.",
  ),
  "entrypoint": RoleResponseTemplate(
    role="entrypoint",
    label="Entrypoint",
    reading_priority=1,
    reading_reason="Application entry point - shows how the app starts",
    why_it_matters="This is where the application starts. Understanding this file shows how the app is configured and initialized.",
    understand_points=(
      "App initialization flow",
      "Root component structure",
      "Global providers or context",
      "Routing setup",
    ),
    improvement_ideas=(
      "Document initialization assumptions",
      "Check configuration defaults",
      "Add smoke tests for startup behavior",
    ),
    assistant_action="Explain {path}, identify the initialization flow and configuration, and suggest improvements.",
  ),
  "backend_route": RoleResponseTemplate(
    role="backend_route",
    label="Backend Route",
    reading_priority=2,
    reading_reason="Defines API endpoints - this is where frontend requests enter the backend",
    why_it_matters="This file defines API endpoints. Frontend requests enter the backend here.",
    understand_points=(
      "API endpoint paths and HTTP methods",
      "Request/response schemas",
      "Route handler function signatures",
      "Dependencies on services and models",
    ),
    improvement_ideas=(
      "Add input validation for edge cases",
      "Document endpoint behavior and responses",
      "Add error handling for failure scenarios",
      "Write tests for happy path and edge cases",
    ),
    test_ideas=(
      "Test valid requests with expected data",
      "Test requests with missing required fields",
      "Test requests with invalid data types",
    ),
    assistant_action="Explain {path}, identify edge cases in the route handlers, and generate pytest tests for all detected endpoints.",
  ),
  "backend_service": RoleResponseTemplate(
    role="backend_service",
    label="Backend Service",
    reading_priority=3,
    reading_reason="Contains business logic and data processing",
    why_it_matters="This file contains business logic. It processes data and implements core functionality.",
    understand_points=(
      "Business logic and data processing",
      "External API calls or database queries",
      "Error handling patterns",
      "Service dependencies",
    ),
    improvement_ideas=(
      "Add error handling and logging",
      "Write unit tests for business logic",
      "Document complex algorithms or workflows",
      "Consider extracting reusable utilities",
    ),
    test_ideas=(
      "Test the main business logic with valid inputs",
      "Test edge cases and boundary conditions",
      "Test error handling for invalid inputs",
    ),
    assistant_action="Explain {path}, identify the business logic and potential edge cases, and generate unit tests.",
  ),
  "model": RoleResponseTemplate(
    role="model",
    label="Model",
    reading_priority=4,
    reading_reason="Defines data structures and schemas used throughout the app",
    why_it_matters="This file defines data structures. Understanding these models is key to understanding the data flow.",
    understand_points=(
      "Data structure fields and types",
      "Validation rules",
      "Relationships to other models",
      "Default values and constraints",
    ),
    improvement_ideas=(
      "Add field documentation/comments",
      "Add validation rules where appropriate",
      "Consider adding helper methods",
      "Write tests for validation logic",
    ),
    test_ideas=(
      "Test data validation rules",
      "Test serialization and deserialization",
      "Test default values and optional fields",
    ),
    assistant_action="Explain {path}, identify validation rules and constraints, and suggest test cases for the data model.",
  ),
  "frontend_page": RoleResponseTemplate(
    role="frontend_page",
    label="Frontend Page",
    reading_priority=6,
    reading_reason="Main UI page - shows how users interact with the app",
    why_it_matters="This is a main UI page. It shows how users interact with the application.",
    understand_points=(
      "Page component structure",
      "Props and state management",
      "User interaction flows",
      "API calls and data fetching",
    ),
    improvement_ideas=(
      "Add loading and error states",
      "Test empty state handling",
      "Improve accessibility",
      "Add integration tests for user flows",
    ),
    assistant_action="Explain {path}, identify user flows and state management, and suggest integration tests.",
  ),
  "api_client": RoleResponseTemplate(
    role="api_client",
    label="API Client",
    reading_priority=7,
    reading_reason="Handles communication between frontend and backend",
    why_it_matters="This file handles frontend-backend communication. It is the bridge between UI and API.",
    understand_points=(
      "API endpoint URLs",
      "Request/response handling",
      "Error handling and retries",
      "Type definitions for API responses",
    ),
    improvement_ideas=(
      "Add timeout handling",
      "Improve error messages and typing",
      "Add retry logic for transient failures",
      "Write tests for API call scenarios",
    ),
    test_ideas=(
      "Test successful API calls",
      "Test error handling for failed requests",
      "Test request timeout scenarios",
    ),
    assistant_action="Explain {path}, identify API endpoints and error handling, and suggest tests for success and failure scenarios.",
  ),
  "test": RoleResponseTemplate(
    role="test",
    label="Test",
    reading_priority=8,
    reading_reason="Test file - shows expected behavior and edge cases",
    why_it_matters="This file shows expected behavior and existing test coverage.",
    understand_points=(
      "What functionality is being tested",
      "Test setup and fixtures",
      "Assertions and expected behavior",
      "Edge cases covered",
    ),
    improvement_ideas=(
      "Add tests for negative cases",
      "Test error handling paths",
      "Add edge case coverage",
      "Improve test descriptions",
    ),
    assistant_action="Explain {path}, identify what it tests and any missing test coverage, and suggest additional test cases.",
  ),
  "frontend_component": RoleResponseTemplate(
    role="frontend_component",
    label="Frontend Component",
    reading_priority=9,
    reading_reason="Reusable UI component - shows how the interface is built",
    why_it_matters="This is a reusable UI component. Understanding it helps you see how the interface is built.",
    understand_points=(
      "Component props interface",
      "Internal state and effects",
      "Event handlers",
      "Child component composition",
    ),
    improvement_ideas=(
      "Test edge cases such as empty data and long text",
      "Improve accessibility",
      "Add prop validation or TypeScript types",
      "Write component tests",
    ),
    test_ideas=(
      "Test component renders correctly with props",
      "Test user interactions and event handlers",
      "Test edge cases like empty or null data",
    ),
    assistant_action="Explain {path}, identify props and event handlers, and suggest component tests including edge cases.",
  ),
  "config": RoleResponseTemplate(
    role="config",
    label="Config",
    reading_priority=10,
    reading_reason="Configuration file - shows project dependencies and settings",
    why_it_matters="This file controls project configuration, dependencies, or runtime settings.",
    understand_points=(
      "Configuration options",
      "Environment-specific settings",
      "Feature flags or toggles",
    ),
    improvement_ideas=(
      "Document configuration options",
      "Add validation for required settings",
      "Consider environment-specific configs",
    ),
  ),
}

DEFAULT_ROLE_TEMPLATE = RoleResponseTemplate(
  role="unknown",
  label="Unknown",
  reading_priority=99,
  reading_reason="Important file for understanding the codebase",
  why_it_matters="This file plays an important role in the codebase.",
  understand_points=(
    "File purpose and responsibility",
    "Key functions or exports",
    "Dependencies and imports",
  ),
  improvement_ideas=(
    "Add documentation comments",
    "Write tests if missing",
    "Improve error handling",
  ),
)

LANGUAGE_TO_ST_CODE = {
  "Python": "python",
  "JavaScript": "javascript",
  "TypeScript": "typescript",
  "JSON": "json",
  "Markdown": "markdown",
  "CSS": "css",
  "HTML": "html",
  "YAML": "yaml",
  "TOML": "toml",
  "Shell": "bash",
}

READING_TIME_RULES = {
  "documentation": (3, 1, 50),
  "config": (1, 1, 50),
  "entrypoint": (5, 2, 30),
  "backend_route": (4, 2, 40),
  "backend_service": (4, 2, 40),
  "model": (4, 2, 40),
  "frontend_page": (4, 2, 40),
  "frontend_component": (4, 2, 40),
  "api_client": (4, 2, 40),
  "test": (3, 1, 50),
}

ROLE_DISTRACTOR_GROUPS = {
  "entrypoint": ("backend_route", "api_client", "model"),
  "backend_route": ("backend_service", "model", "entrypoint"),
  "frontend_page": ("frontend_component", "api_client", "entrypoint"),
  "api_client": ("frontend_page", "frontend_component", "backend_route"),
  "model": ("backend_service", "backend_route"),
}

ROLE_CONNECTION_TARGETS = {
  "backend_route": ("backend_service", "model"),
  "backend_service": ("model",),
  "frontend_page": ("frontend_component", "api_client"),
  "api_client": ("backend_route",),
}

WORK_PLAN_EPIC_GOALS = {
  "Testing & Quality": "Improve test coverage and code quality",
  "Documentation": "Enhance documentation for developers and users",
  "Reliability & Error Handling": "Improve error handling and system reliability",
  "Data Integrity": "Ensure data validation and integrity",
  "Accessibility & UX": "Improve user experience and accessibility",
}


def get_role_template(role: str) -> RoleResponseTemplate:
  """Return response template for a role."""
  return ROLE_TEMPLATES.get(role, DEFAULT_ROLE_TEMPLATE)


def get_role_label(role: str) -> str:
  """Return a human-friendly label for a role."""
  return get_role_template(role).label


def format_likely_role(role: str) -> str:
  """Format a role label for component cards."""
  return f"Likely role: {get_role_label(role).lower()}"


def is_readme(file_info: FileInfo) -> bool:
  """Return whether a file is a README."""
  return file_info.name.lower() == "readme.md"


def is_likely_backend_entry(file_info: FileInfo) -> bool:
  """Return whether an entrypoint looks backend-oriented."""
  path_lower = file_info.path.lower()
  return "backend" in path_lower or file_info.name.lower() in ("main.py", "app.py")


def get_reading_priority(file_info: FileInfo) -> tuple[int, int]:
  """Return reading path priority as (category, subcategory)."""
  if is_readme(file_info):
    return (0, 0)

  template = get_role_template(file_info.role)

  if file_info.role == "entrypoint":
    return (1, 0) if is_likely_backend_entry(file_info) else (5, 0)

  if file_info.role == "frontend_component":
    name_lower = file_info.name.lower()
    priority_names = ("search", "form", "card", "list")
    return (template.reading_priority, 0 if any(token in name_lower for token in priority_names) else 1)

  return (template.reading_priority, 0)


def estimate_reading_minutes(file_info: FileInfo) -> int:
  """Estimate how many minutes to spend reading a file."""
  max_minutes, min_minutes, divisor = READING_TIME_RULES.get(file_info.role, (3, 1, 50))
  return min(max_minutes, max(min_minutes, file_info.line_count // divisor))


def get_reading_reason(file_info: FileInfo) -> str:
  """Return deterministic reading-path reason for a file."""
  if is_readme(file_info):
    return "Start here to understand the project's purpose and setup"

  if file_info.role == "entrypoint" and is_likely_backend_entry(file_info):
    return "Main backend entry point - shows how the API server is configured"

  if file_info.role == "entrypoint" and "frontend" in file_info.path.lower():
    return "Main frontend entry point - shows how the UI is initialized"

  return get_role_template(file_info.role).reading_reason


def get_why_it_matters(file_info: FileInfo) -> str:
  """Return role-based explanation for component cards."""
  return get_role_template(file_info.role).why_it_matters


def get_understand_points_for_file(file_info: FileInfo) -> list[str]:
  """Return deterministic understanding points for a file."""
  if is_readme(file_info):
    return [
      "Project purpose and goals",
      "Setup and installation steps",
      "Key features and capabilities",
      "Architecture overview if present",
    ]

  if file_info.role == "entrypoint" and is_likely_backend_entry(file_info):
    return [
      "Server initialization and configuration",
      "Middleware and plugins setup",
      "Route registration",
      "Database or external service connections",
    ]

  if file_info.role == "config" and file_info.name.lower() == "package.json":
    return ["Project dependencies", "Scripts and build commands", "Project metadata"]

  if file_info.role == "config" and file_info.name.lower() in ("requirements.txt", "pyproject.toml"):
    return ["Python dependencies", "Version constraints", "Development vs production packages"]

  return list(get_role_template(file_info.role).understand_points)


def get_improvement_ideas_for_file(file_info: FileInfo) -> list[str]:
  """Return deterministic improvement ideas for a file."""
  if is_readme(file_info):
    return [
      "Add missing setup steps or prerequisites",
      "Document API endpoints if not present",
      "Include architecture diagram or overview",
      "Add troubleshooting section",
    ]

  return list(get_role_template(file_info.role).improvement_ideas)


def get_test_ideas_for_file(file_info: FileInfo, routes: list[RouteInfo] | None = None) -> list[str]:
  """Return deterministic test ideas for a file."""
  ideas = list(get_role_template(file_info.role).test_ideas)

  if file_info.role == "backend_route" and routes:
    file_routes = [route for route in routes if route.file_path == file_info.path]
    if any(route.method.lower() == "delete" for route in file_routes):
      ideas.append("Test deleting non-existent resources")

  return ideas[:3]


def get_assistant_action_for_file(
  file_info: FileInfo,
  routes: list[RouteInfo] | None = None,
) -> str:
  """Return a deterministic manual assistant action for a file."""
  template = get_role_template(file_info.role).assistant_action

  if file_info.role == "backend_route" and routes:
    file_routes = [route for route in routes if route.file_path == file_info.path]
    if file_routes:
      route_list = ", ".join(f"{route.method} {route.path}" for route in file_routes[:3])
      return (
        f"Explain {file_info.path}, identify edge cases for routes ({route_list}), "
        "and generate pytest tests for the detected endpoints."
      )

  return template.format(path=file_info.path)


def get_language_for_code(file_info: FileInfo) -> str | None:
  """Return syntax highlighting language for Streamlit code blocks."""
  return LANGUAGE_TO_ST_CODE.get(file_info.language)


def get_distractor_roles(role: str) -> tuple[str, ...]:
  """Return related roles to use as plausible quiz distractors."""
  return ROLE_DISTRACTOR_GROUPS.get(role, ())


def get_connection_target_roles(role: str) -> tuple[str, ...]:
  """Return roles that are likely connected to a source role."""
  return ROLE_CONNECTION_TARGETS.get(role, ())


def get_work_plan_epic_goal(epic: str) -> str:
  """Return generic milestone goal copy for a work-plan epic."""
  return WORK_PLAN_EPIC_GOALS.get(epic, f"Complete {epic} tasks")

# Made with Bob
