"""Tests for workflow generation."""

import pytest
from repoquest.models import (
  RepositorySnapshot,
  FileInfo,
  ProjectFingerprint,
  FrameworkFinding,
  RouteInfo,
  ImportEdge,
  ReadingPathItem,
  ComponentCard,
)
from repoquest.workflows import (
  generate_task_suggestions,
  generate_agent_workflows,
  group_tasks_into_milestones,
  generate_work_plan,
  export_workflows_markdown,
)


@pytest.fixture
def demo_snapshot():
  """Create a demo repository snapshot for testing."""
  files = [
    FileInfo(
      path="backend/main.py",
      name="main.py",
      suffix=".py",
      size_bytes=1000,
      language="Python",
      role="entrypoint",
      text_preview="from fastapi import FastAPI\napp = FastAPI()",
      line_count=50,
    ),
    FileInfo(
      path="backend/routes/trips.py",
      name="trips.py",
      suffix=".py",
      size_bytes=2000,
      language="Python",
      role="backend_route",
      text_preview="@router.get('/trips')\nasync def list_trips():\n  pass",
      line_count=100,
    ),
    FileInfo(
      path="backend/services/recommendations.py",
      name="recommendations.py",
      suffix=".py",
      size_bytes=1500,
      language="Python",
      role="backend_service",
      text_preview="def get_recommendations():\n  pass",
      line_count=75,
    ),
    FileInfo(
      path="backend/models/trip.py",
      name="trip.py",
      suffix=".py",
      size_bytes=800,
      language="Python",
      role="model",
      text_preview="class Trip:\n  pass",
      line_count=40,
    ),
    FileInfo(
      path="backend/tests/test_trips.py",
      name="test_trips.py",
      suffix=".py",
      size_bytes=1200,
      language="Python",
      role="test",
      text_preview="def test_list_trips():\n  pass",
      line_count=60,
    ),
    FileInfo(
      path="frontend/src/services/api.ts",
      name="api.ts",
      suffix=".ts",
      size_bytes=1000,
      language="TypeScript",
      role="api_client",
      text_preview="export async function fetchTrips() {}",
      line_count=50,
    ),
    FileInfo(
      path="frontend/src/pages/TripsPage.tsx",
      name="TripsPage.tsx",
      suffix=".tsx",
      size_bytes=1500,
      language="TypeScript",
      role="frontend_page",
      text_preview="export function TripsPage() {}",
      line_count=75,
    ),
    FileInfo(
      path="frontend/src/components/TripCard.tsx",
      name="TripCard.tsx",
      suffix=".tsx",
      size_bytes=800,
      language="TypeScript",
      role="frontend_component",
      text_preview="export function TripCard() {}",
      line_count=40,
    ),
    FileInfo(
      path="README.md",
      name="README.md",
      suffix=".md",
      size_bytes=500,
      language="Markdown",
      role="documentation",
      text_preview="# Mini Travel Planner",
      line_count=25,
    ),
  ]

  return RepositorySnapshot(
    source_name="mini_travel_planner",
    files=files,
    total_files_seen=9,
    total_files_scanned=9,
    warnings=[],
  )


@pytest.fixture
def demo_fingerprint():
  """Create a demo project fingerprint."""
  return ProjectFingerprint(
    project_type="Full-stack web application",
    confidence=0.9,
    frameworks=[
      FrameworkFinding(
        name="FastAPI",
        category="backend",
        confidence=0.95,
        evidence=["backend/main.py: from fastapi import FastAPI"],
      ),
      FrameworkFinding(
        name="React",
        category="frontend",
        confidence=0.9,
        evidence=["frontend/src/pages/TripsPage.tsx: React component"],
      ),
    ],
    entry_points=["backend/main.py", "frontend/src/App.tsx"],
    key_folders=["backend/", "frontend/"],
    summary="Full-stack web application with FastAPI backend and React frontend",
    warnings=[],
  )


@pytest.fixture
def demo_routes():
  """Create demo API routes."""
  return [
    RouteInfo(
      framework="fastapi",
      method="GET",
      path="/api/trips",
      file_path="backend/routes/trips.py",
      function_name="list_trips",
    ),
    RouteInfo(
      framework="fastapi",
      method="POST",
      path="/api/trips",
      file_path="backend/routes/trips.py",
      function_name="create_trip",
    ),
    RouteInfo(
      framework="fastapi",
      method="DELETE",
      path="/api/trips/{trip_id}",
      file_path="backend/routes/trips.py",
      function_name="delete_trip",
    ),
  ]


@pytest.fixture
def demo_import_edges():
  """Create demo import edges."""
  return [
    ImportEdge(
      source="backend/routes/trips.py",
      target="backend/services/recommendations.py",
      kind="python_import",
      confidence=1.0,
    ),
    ImportEdge(
      source="backend/routes/trips.py",
      target="backend/models/trip.py",
      kind="python_import",
      confidence=1.0,
    ),
  ]


@pytest.fixture
def demo_reading_path():
  """Create demo reading path."""
  return [
    ReadingPathItem(
      order=1,
      path="README.md",
      reason="Start here",
      estimated_minutes=2,
    ),
    ReadingPathItem(
      order=2,
      path="backend/main.py",
      reason="Backend entry point",
      estimated_minutes=3,
    ),
  ]


@pytest.fixture
def demo_component_cards():
  """Create demo component cards."""
  return [
    ComponentCard(
      path="backend/routes/trips.py",
      title="trips.py",
      role="backend_route",
      why_it_matters="Defines API endpoints",
      connected_to=["backend/services/recommendations.py"],
      detected_items=["GET /api/trips", "POST /api/trips"],
      suggested_test_ideas=["Test valid requests", "Test missing fields"],
      suggested_bob_prompt="Explain backend/routes/trips.py",
    ),
  ]


def test_generate_task_suggestions(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test task generation."""
  tasks = generate_task_suggestions(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  # Should generate multiple tasks
  assert len(tasks) > 0

  # Each task should have required fields
  for task in tasks:
    assert task.epic
    assert task.priority in ["high", "medium", "low"]
    assert len(task.files) > 0
    assert len(task.evidence) > 0
    assert task.why
    assert len(task.acceptance_criteria) > 0
    assert task.suggested_workflow


def test_documentation_task_uses_actual_readme_path(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test documentation tasks cite nested README files by their real paths."""
  files = [
    file_info for file_info in demo_snapshot.files
    if file_info.name.lower() != "readme.md"
  ]
  files.append(FileInfo(
    path="docs/README.md",
    name="README.md",
    suffix=".md",
    size_bytes=500,
    language="Markdown",
    role="documentation",
    text_preview="# Project Docs",
    line_count=25,
  ))
  snapshot = RepositorySnapshot(
    source_name=demo_snapshot.source_name,
    files=files,
    total_files_seen=len(files),
    total_files_scanned=len(files),
    warnings=[],
  )

  tasks = generate_task_suggestions(
    snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  documentation_task = next(
    task for task in tasks
    if task.suggested_workflow == "Generate API documentation"
  )
  assert "docs/README.md" in documentation_task.files
  assert "README.md" not in documentation_task.files


def test_generate_agent_workflows(
  demo_snapshot, demo_fingerprint, demo_routes, demo_component_cards
):
  """Test workflow generation."""
  tasks = generate_task_suggestions(
    demo_snapshot, demo_fingerprint, demo_routes, [], [], demo_component_cards
  )

  workflows = generate_agent_workflows(
    demo_snapshot, demo_fingerprint, demo_routes, tasks, demo_component_cards
  )

  # Should generate at least 3 workflows for demo repo
  assert len(workflows) >= 3

  # Each workflow should have required fields
  for workflow in workflows:
    assert workflow.title
    assert workflow.goal
    assert len(workflow.ordered_steps) > 0
    assert len(workflow.files_to_read) > 0
    assert len(workflow.files_to_change) > 0
    assert len(workflow.validation_steps) > 0
    assert workflow.expected_output
    assert workflow.prompt

    # Prompt should not ask to execute uploaded code
    assert "execute" not in workflow.prompt.lower() or "do not execute" in workflow.prompt.lower()


def test_group_tasks_into_milestones(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test milestone grouping."""
  tasks = generate_task_suggestions(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  milestones = group_tasks_into_milestones(tasks)

  # Should create milestones
  assert len(milestones) > 0

  # Each milestone should have tasks
  for milestone in milestones:
    assert milestone.title
    assert milestone.goal
    assert len(milestone.tasks) > 0


def test_generate_work_plan(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test complete work plan generation."""
  work_plan = generate_work_plan(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  # Should have all components
  assert len(work_plan.epics) > 0
  assert len(work_plan.tasks) > 0
  assert len(work_plan.milestones) > 0
  assert len(work_plan.workflows) >= 3 # At least 3 workflows for demo repo

  # Epics should match task epics
  task_epics = set(task.epic for task in work_plan.tasks)
  assert set(work_plan.epics) == task_epics


def test_export_workflows_markdown(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test Markdown export."""
  work_plan = generate_work_plan(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  markdown = export_workflows_markdown(work_plan, "test_project")

  # Should contain key sections
  assert "# RepoQuest Work Plan" in markdown
  assert "## Summary" in markdown
  assert "## Epics" in markdown
  assert "## Suggested Milestones" in markdown
  assert "## Tasks" in markdown
  assert "## Agent Workflows" in markdown

  # Should contain workflow details
  assert "Files to read" in markdown
  assert "Files likely to change" in markdown
  assert "Validation steps" in markdown
  assert "Expected output" in markdown
  assert "AI Assistant Action" in markdown


def test_task_has_file_evidence(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test that every task has file evidence."""
  tasks = generate_task_suggestions(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  for task in tasks:
    # Every task must reference at least one file
    assert len(task.files) > 0, f"Task '{task.why}' has no files"

    # Every task must have evidence
    assert len(task.evidence) > 0, f"Task '{task.why}' has no evidence"


def test_workflow_no_execute_uploaded_code(
  demo_snapshot, demo_fingerprint, demo_routes, demo_component_cards
):
  """Test that workflows don't ask to execute uploaded code."""
  tasks = generate_task_suggestions(
    demo_snapshot, demo_fingerprint, demo_routes, [], [], demo_component_cards
  )

  workflows = generate_agent_workflows(
    demo_snapshot, demo_fingerprint, demo_routes, tasks, demo_component_cards
  )

  for workflow in workflows:
    prompt_lower = workflow.prompt.lower()

    # Should not ask to execute code
    if "execute" in prompt_lower:
      assert "do not execute" in prompt_lower, f"Workflow '{workflow.title}' may ask to execute uploaded code"


def test_deterministic_generation(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test that generation is deterministic."""
  # Generate twice
  work_plan1 = generate_work_plan(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  work_plan2 = generate_work_plan(
    demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  # Should produce same number of items
  assert len(work_plan1.epics) == len(work_plan2.epics)
  assert len(work_plan1.tasks) == len(work_plan2.tasks)
  assert len(work_plan1.milestones) == len(work_plan2.milestones)
  assert len(work_plan1.workflows) == len(work_plan2.workflows)

  # Task titles should be in same order
  task_titles1 = [t.why for t in work_plan1.tasks]
  task_titles2 = [t.why for t in work_plan2.tasks]
  assert task_titles1 == task_titles2

  # Workflow titles should be in same order
  workflow_titles1 = [w.title for w in work_plan1.workflows]
  workflow_titles2 = [w.title for w in work_plan2.workflows]
  assert workflow_titles1 == workflow_titles2


def test_init_files_excluded_from_tasks(
  demo_snapshot, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
):
  """Test that __init__.py files are excluded from task files."""
  # Add some __init__.py files to snapshot
  init_files = [
    FileInfo(
      path="backend/routes/__init__.py",
      name="__init__.py",
      suffix=".py",
      size_bytes=50,
      language="Python",
      role="backend_route",
      text_preview="",
      line_count=2,
    ),
    FileInfo(
      path="backend/models/__init__.py",
      name="__init__.py",
      suffix=".py",
      size_bytes=30,
      language="Python",
      role="model",
      text_preview="",
      line_count=1,
    ),
    FileInfo(
      path="backend/tests/__init__.py",
      name="__init__.py",
      suffix=".py",
      size_bytes=0,
      language="Python",
      role="test",
      text_preview="",
      line_count=0,
    ),
  ]

  snapshot_with_inits = RepositorySnapshot(
    source_name=demo_snapshot.source_name,
    files=demo_snapshot.files + init_files,
    total_files_seen=demo_snapshot.total_files_seen + len(init_files),
    total_files_scanned=demo_snapshot.total_files_scanned + len(init_files),
    warnings=demo_snapshot.warnings,
  )

  tasks = generate_task_suggestions(
    snapshot_with_inits, demo_fingerprint, demo_routes, demo_import_edges, demo_reading_path, demo_component_cards
  )

  # Check that no task includes __init__.py files
  for task in tasks:
    for file in task.files:
      assert "__init__.py" not in file, f"Task '{task.why}' includes __init__.py file: {file}"


def test_init_files_excluded_from_workflows(
  demo_snapshot, demo_fingerprint, demo_routes, demo_component_cards
):
  """Test that __init__.py files are excluded from workflow files."""
  # Add some __init__.py files to snapshot
  init_files = [
    FileInfo(
      path="backend/routes/__init__.py",
      name="__init__.py",
      suffix=".py",
      size_bytes=50,
      language="Python",
      role="backend_route",
      text_preview="",
      line_count=2,
    ),
    FileInfo(
      path="backend/services/__init__.py",
      name="__init__.py",
      suffix=".py",
      size_bytes=30,
      language="Python",
      role="backend_service",
      text_preview="",
      line_count=1,
    ),
  ]

  snapshot_with_inits = RepositorySnapshot(
    source_name=demo_snapshot.source_name,
    files=demo_snapshot.files + init_files,
    total_files_seen=demo_snapshot.total_files_seen + len(init_files),
    total_files_scanned=demo_snapshot.total_files_scanned + len(init_files),
    warnings=demo_snapshot.warnings,
  )

  tasks = generate_task_suggestions(
    snapshot_with_inits, demo_fingerprint, demo_routes, [], [], demo_component_cards
  )

  workflows = generate_agent_workflows(
    snapshot_with_inits, demo_fingerprint, demo_routes, tasks, demo_component_cards
  )

  # Check that no workflow includes __init__.py files
  for workflow in workflows:
    for file in workflow.files_to_read:
      assert "__init__.py" not in file, f"Workflow '{workflow.title}' files_to_read includes __init__.py: {file}"

    for file in workflow.files_to_change:
      assert "__init__.py" not in file, f"Workflow '{workflow.title}' files_to_change includes __init__.py: {file}"

# Made with Bob
