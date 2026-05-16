"""Generate test intelligence and coverage insights from repository analysis."""

import re
from repoquest.models import (
  RepositorySnapshot,
  FileInfo,
  RouteInfo,
  ImportEdge,
  ComponentCard,
  TestInsight,
  TestIntelligence,
)


def get_test_inventory(snapshot: RepositorySnapshot) -> list[FileInfo]:
  """
  Get all test files from the snapshot, excluding __init__.py package markers.

  Args:
    snapshot: Repository snapshot

  Returns:
    List of test FileInfo objects
  """
  test_files = []
  for file_info in snapshot.files:
    if file_info.skipped:
      continue

    # Skip __init__.py unless substantial
    if file_info.name == "__init__.py" and file_info.line_count < 50:
      continue

    # Check if it's a test file
    if file_info.is_test:
      test_files.append(file_info)

  return test_files


def detect_test_framework(file_info: FileInfo) -> str:
  """
  Detect the test framework used in a test file.

  Args:
    file_info: Test file info

  Returns:
    Framework name or "unknown"
  """
  if not file_info.text_preview:
    return "unknown"

  content = file_info.text_preview.lower()

  # Python frameworks
  if "import pytest" in content or "from pytest" in content or "def test_" in content:
    return "pytest"
  if "import unittest" in content or "from unittest" in content:
    return "unittest"

  # JavaScript/TypeScript frameworks - check vitest first
  if "vitest" in content or "import { describe" in content or "import { it" in content:
    return "vitest"
  if "jest" in content or "describe(" in content or "it(" in content:
    return "jest"

  # Generic detection using file name patterns
  if file_info.suffix == ".py" and ("test_" in file_info.name or "_test" in file_info.name):
    return "pytest (inferred)"

  # Check for compound extensions like.test.ts,.spec.js
  if file_info.name.endswith((".test.ts", ".test.js", ".test.tsx", ".test.jsx")):
    return "jest/vitest (inferred)"
  if file_info.name.endswith((".spec.ts", ".spec.js", ".spec.tsx", ".spec.jsx")):
    return "jest/vitest (inferred)"

  return "unknown"


def extract_test_imports(file_info: FileInfo) -> list[str]:
  """
  Extract import statements from a test file.

  Args:
    file_info: Test file info

  Returns:
    List of import statements
  """
  if not file_info.text_preview:
    return []

  imports = []
  lines = file_info.text_preview.split('\n')

  for line in lines[:50]: # Check first 50 lines
    line = line.strip()

    # Python imports
    if line.startswith('import ') or line.startswith('from '):
      imports.append(line)

    # JS/TS imports
    if line.startswith('import ') and ' from ' in line:
      imports.append(line)

  return imports[:20] # Limit to 20 imports


def extract_test_quality_signals(file_info: FileInfo) -> dict[str, int | bool]:
  """
  Extract quality signals from a test file.

  Args:
    file_info: Test file info

  Returns:
    Dict with quality signal metrics
  """
  if not file_info.text_preview:
    return {
      "assertion_count": 0,
      "has_fixtures": False,
      "has_mocks": False,
      "has_test_client": False,
      "skipped_count": 0,
    }

  content = file_info.text_preview
  content_lower = content.lower()

  # Count assertions
  assertion_count = 0
  assertion_patterns = [
    r'\bassert\s+',
    r'\.assert',
    r'expect\(',
    r'\.toBe\(',
    r'\.toEqual\(',
  ]
  for pattern in assertion_patterns:
    assertion_count += len(re.findall(pattern, content))

  # Pytest fixtures
  has_fixtures = '@pytest.fixture' in content or ('def ' in content and 'fixture' in content_lower)

  # Skipped tests
  skipped_count = 0
  if '@pytest.mark.skip' in content:
    skipped_count += content.count('@pytest.mark.skip')
  if '@unittest.skip' in content:
    skipped_count += content.count('@unittest.skip')
  if 'it.skip(' in content:
    skipped_count += content.count('it.skip(')

  # Mocking/patching
  has_mocks = 'mock' in content_lower or 'patch' in content_lower or 'spy' in content_lower

  # TestClient (FastAPI)
  has_test_client = 'TestClient' in content

  return {
    "assertion_count": assertion_count,
    "has_fixtures": has_fixtures,
    "has_mocks": has_mocks,
    "has_test_client": has_test_client,
    "skipped_count": skipped_count,
  }


def map_test_to_likely_targets(
  test_file: FileInfo,
  snapshot: RepositorySnapshot,
  import_edges: list[ImportEdge],
) -> list[str]:
  """
  Map a test file to likely production targets it covers.

  Args:
    test_file: Test file info
    import_edges: Import relationships
    snapshot: Repository snapshot

  Returns:
    List of likely target file paths
  """
  targets = []

  # First, use import edges - most reliable
  for edge in import_edges:
    if edge.source == test_file.path:
      # Check if target is not a test file
      target_file = next((f for f in snapshot.files if f.path == edge.target), None)
      if target_file and not target_file.is_test:
        if edge.target not in targets:
          targets.append(edge.target)

  # If we have import edges, prefer those
  if targets:
    return targets[:10]

  # Fallback: parse imports from text conservatively
  if test_file.text_preview:
    imports = extract_test_imports(test_file)
    test_dir = "/".join(test_file.path.split("/")[:-1]) # Get test directory

    for imp in imports:
      # Parse Python imports: from backend.main import app
      if "from " in imp and " import " in imp:
        module_part = imp.split("from ")[1].split(" import ")[0].strip()
        # Convert module path to file path: backend.main -> backend/main.py
        potential_path = module_part.replace(".", "/") + ".py"

        # Check if this file exists in snapshot
        for file_info in snapshot.files:
          if file_info.is_test or file_info.skipped:
            continue
          if file_info.path == potential_path and file_info.path not in targets:
            targets.append(file_info.path)

      # Parse relative imports: import../services/api
      elif "../" in imp or "./" in imp:
        # Extract path from import
        import_path = imp.split("from ")[-1].split("import")[0].strip().strip("'\"")
        # Resolve relative to test file location
        # This is simplified - real resolution would need path normalization
        pass # Skip complex relative path resolution for now

  return targets[:10] # Limit to 10 targets


def infer_covered_routes(
  test_file: FileInfo,
  likely_targets: list[str],
  routes: list[RouteInfo],
) -> list[str]:
  """
  Infer which routes are likely covered by a test file.

  Only marks a route as covered if there's strong evidence in the test content.

  Args:
    test_file: Test file info
    likely_targets: Likely production files this test covers
    routes: All detected routes

  Returns:
    List of covered route strings (e.g., "GET /api/trips")
  """
  covered = []

  if not test_file.text_preview:
    return covered

  content = test_file.text_preview
  content_lower = content.lower()

  for route in routes:
    route_str = f"{route.method} {route.path}"

    # Only mark as covered if we find strong evidence in test content
    evidence_found = False

    # Look for HTTP client calls with the route path
    # e.g., client.get("/api/trips"), fetch("/api/trips"), request.get("/api/trips")
    method_lower = route.method.lower()

    # Pattern: method_name("path") or method_name('path')
    if f'{method_lower}("{route.path}")' in content_lower or f"{method_lower}('{route.path}')" in content_lower:
      evidence_found = True

    # Pattern: method_name(url + "path") or similar
    elif f'"{route.path}"' in content or f"'{route.path}'" in content:
      # Check if HTTP method appears nearby (within reasonable distance)
      if method_lower in content_lower:
        # Additional check: make sure it's not just "/" appearing in imports
        if len(route.path) > 1 or (route.path == "/" and f'{method_lower}("/")' in content_lower):
          evidence_found = True

    # Function name appears in test content
    if not evidence_found and route.function_name and route.function_name in content:
      evidence_found = True

    if evidence_found and route_str not in covered:
      covered.append(route_str)

  return covered


def find_missing_coverage(
  snapshot: RepositorySnapshot,
  routes: list[RouteInfo],
  component_cards: list[ComponentCard],
  test_insights: list[TestInsight],
) -> list[str]:
  """
  Find app files, routes, and components that appear untested.

  Args:
    snapshot: Repository snapshot
    routes: All detected routes
    component_cards: Component cards
    test_insights: Test insights

  Returns:
    List of missing coverage descriptions
  """
  missing = []

  # Collect all covered targets and routes
  covered_targets = set()
  covered_routes = set()

  for insight in test_insights:
    covered_targets.update(insight.likely_targets)
    covered_routes.update(insight.covered_routes)

  # Check routes
  for route in routes:
    route_str = f"{route.method} {route.path}"
    if route_str not in covered_routes:
      missing.append(f"Route: {route_str} (in {route.file_path})")

  # Check important component files
  important_roles = ["backend_service", "model", "api_client", "frontend_page"]

  for file_info in snapshot.files:
    if file_info.skipped or file_info.is_test:
      continue

    # Skip __init__.py
    if file_info.name == "__init__.py" and file_info.line_count < 50:
      continue

    if file_info.role in important_roles:
      if file_info.path not in covered_targets:
        role_name = file_info.role.replace('_', ' ').title()
        missing.append(f"{role_name}: {file_info.path}")

  return missing[:15] # Limit to 15 items


def generate_suggested_next_tests(
  snapshot: RepositorySnapshot,
  routes: list[RouteInfo],
  component_cards: list[ComponentCard],
  test_insights: list[TestInsight],
) -> list[str]:
  """
  Generate concrete suggested test cases.

  Args:
    snapshot: Repository snapshot
    routes: All detected routes
    component_cards: Component cards
    test_insights: Test insights

  Returns:
    List of concrete test suggestions
  """
  suggestions = []

  # Collect covered routes
  covered_routes = set()
  for insight in test_insights:
    covered_routes.update(insight.covered_routes)

  # Suggest tests for uncovered routes
  for route in routes[:5]: # Limit to first 5 routes
    route_str = f"{route.method} {route.path}"

    if route_str not in covered_routes:
      # Suggest basic test
      suggestions.append(f"Test {route_str} with valid data")

      # Suggest edge cases
      if route.method in ["POST", "PUT", "PATCH"]:
        suggestions.append(f"Test {route_str} with missing required fields")
        suggestions.append(f"Test {route_str} with invalid data types")

      if route.method == "DELETE":
        suggestions.append(f"Test {route_str} with nonexistent resource ID")

      if route.method == "GET" and "{" in route.path:
        suggestions.append(f"Test {route_str} with invalid ID format")

  # Suggest tests for API clients
  api_clients = [f for f in snapshot.files if f.role == "api_client" and not f.skipped]
  for client in api_clients[:2]: # Limit to 2
    suggestions.append(f"Test {client.path} handles failed fetch responses")
    suggestions.append(f"Test {client.path} handles network timeout")

  # Suggest tests for models
  models = [f for f in snapshot.files if f.role == "model" and not f.skipped
       and not (f.name == "__init__.py" and f.line_count < 50)]
  for model in models[:2]: # Limit to 2
    suggestions.append(f"Test {model.path} validation for missing required fields")
    suggestions.append(f"Test {model.path} serialization and deserialization")

  # Suggest tests for services
  services = [f for f in snapshot.files if f.role == "backend_service" and not f.skipped
        and not (f.name == "__init__.py" and f.line_count < 50)]
  for service in services[:2]: # Limit to 2
    suggestions.append(f"Test {service.path} business logic with edge cases")
    suggestions.append(f"Test {service.path} error handling")

  return suggestions[:12] # Limit to 12 suggestions


def generate_test_plan(
  test_insights: list[TestInsight],
  missing_coverage: list[str],
  suggested_tests: list[str],
) -> str:
  """
  Generate an IBM Bob / agent test plan prompt.

  Args:
    test_insights: Test insights
    missing_coverage: Missing coverage items
    suggested_tests: Suggested test cases

  Returns:
    Test plan prompt string
  """
  lines = []

  lines.append("# Test Coverage Improvement Plan")
  lines.append("")
  lines.append("## Current Test Coverage")
  lines.append("")

  if test_insights:
    lines.append(f"Detected {len(test_insights)} test files:")
    for insight in test_insights[:5]:
      lines.append(f"- {insight.test_file} ({insight.framework})")
      if insight.covered_routes:
        lines.append(f" Covers: {', '.join(insight.covered_routes[:3])}")
  else:
    lines.append("No test files detected.")

  lines.append("")
  lines.append("## Missing Coverage")
  lines.append("")

  if missing_coverage:
    for item in missing_coverage[:8]:
      lines.append(f"- {item}")
  else:
    lines.append("No obvious gaps detected.")

  lines.append("")
  lines.append("## Suggested Next Tests")
  lines.append("")

  if suggested_tests:
    for i, suggestion in enumerate(suggested_tests[:8], 1):
      lines.append(f"{i}. {suggestion}")
  else:
    lines.append("No specific suggestions at this time.")

  lines.append("")
  lines.append("## Implementation Steps")
  lines.append("")
  lines.append("1. Review the missing coverage and suggested tests above")
  lines.append("2. Choose the highest-priority test cases")
  lines.append("3. Add test functions following existing test patterns")
  lines.append("4. In a trusted local clone: Run pytest -v to verify tests pass")
  lines.append("5. Check test coverage increased")
  lines.append("")
  lines.append("Note: Do not execute uploaded code. This plan is for the developer's own trusted repository.")

  return "\n".join(lines)


def generate_test_intelligence(
  snapshot: RepositorySnapshot,
  routes: list[RouteInfo],
  import_edges: list[ImportEdge],
  component_cards: list[ComponentCard],
) -> TestIntelligence:
  """
  Generate complete test intelligence for a repository.

  Args:
    snapshot: Repository snapshot
    routes: Detected routes
    import_edges: Import relationships
    component_cards: Component cards

  Returns:
    TestIntelligence with test insights, missing coverage, suggested tests, and test plan
  """
  # Get test inventory
  test_files = get_test_inventory(snapshot)

  # Generate insights for each test file
  test_insights = []

  for test_file in test_files:
    framework = detect_test_framework(test_file)
    imports = extract_test_imports(test_file)
    quality_signals = extract_test_quality_signals(test_file)
    likely_targets = map_test_to_likely_targets(test_file, snapshot, import_edges)
    covered_routes = infer_covered_routes(test_file, likely_targets, routes)

    # Generate missing cases for this specific test
    missing_cases = []
    if quality_signals.get("assertion_count", 0) == 0:
      missing_cases.append("Add assertions to verify behavior")

    # Suggest specific tests based on covered routes
    suggested_tests = []
    for route in routes[:3]:
      route_str = f"{route.method} {route.path}"
      if route_str in covered_routes:
        if route.method in ["POST", "PUT"]:
          suggested_tests.append(f"Add edge case: {route_str} with invalid data")
        if route.method == "DELETE":
          suggested_tests.append(f"Add edge case: {route_str} with nonexistent ID")

    test_insights.append(TestInsight(
      test_file=test_file.path,
      framework=framework,
      imports=imports,
      likely_targets=likely_targets,
      covered_routes=covered_routes,
      missing_cases=missing_cases,
      suggested_tests=suggested_tests[:3],
      quality_signals=quality_signals,
    ))

  # Find missing coverage
  missing_coverage = find_missing_coverage(snapshot, routes, component_cards, test_insights)

  # Generate suggested tests
  suggested_tests = generate_suggested_next_tests(snapshot, routes, component_cards, test_insights)

  # Generate test plan
  test_plan = generate_test_plan(test_insights, missing_coverage, suggested_tests)

  return TestIntelligence(
    test_insights=test_insights,
    missing_coverage=missing_coverage,
    suggested_tests=suggested_tests,
    test_plan=test_plan,
  )
