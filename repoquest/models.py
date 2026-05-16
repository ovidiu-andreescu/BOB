"""Data models for RepoQuest."""

from dataclasses import dataclass
from typing import Literal

# Graph view modes for filtering
GraphViewMode = Literal["application", "tests", "all_debug"]


@dataclass
class FileInfo:
  """Information about a scanned file."""
  path: str
  name: str
  suffix: str
  size_bytes: int
  language: str
  role: str
  text_preview: str
  line_count: int
  skipped: bool = False
  skip_reason: str | None = None

  @property
  def is_test(self) -> bool:
    """Check if this file is a test file."""
    path_lower = self.path.lower()
    return (
      self.role == "test"
      or "/tests/" in path_lower
      or "/__tests__/" in path_lower
      or path_lower.startswith("test_")
      or path_lower.startswith("tests/")
      or "_test." in path_lower
      or ".test." in path_lower
      or ".spec." in path_lower
    )


@dataclass
class RepositorySnapshot:
  """Snapshot of a scanned repository."""
  source_name: str
  files: list[FileInfo]
  total_files_seen: int
  total_files_scanned: int
  warnings: list[str]


@dataclass
class ImportEdge:
  """Represents an import relationship between files."""
  source: str
  target: str
  kind: str # "python_import", "js_import", "ts_import"
  confidence: float
  evidence: str = "" # Evidence snippet showing the import

  @property
  def is_test_edge(self) -> bool:
    """Check if this edge involves test files."""
    source_lower = self.source.lower()
    target_lower = self.target.lower()

    def is_test_path(path: str) -> bool:
      return (
        "/tests/" in path
        or "/__tests__/" in path
        or path.startswith("test_")
        or path.startswith("tests/")
        or "_test." in path
        or ".test." in path
        or ".spec." in path
      )

    return is_test_path(source_lower) or is_test_path(target_lower)


@dataclass
class RouteInfo:
  """Information about a detected API route."""
  framework: str # "fastapi", "flask", "express"
  method: str # "GET", "POST", "DELETE", etc.
  path: str # "/trips", "/trips/{trip_id}"
  file_path: str
  function_name: str | None = None


@dataclass
class FrameworkFinding:
  """Information about a detected framework."""
  name: str
  category: str # "frontend", "backend", "testing", "tooling"
  confidence: float # 0.0 to 1.0
  evidence: list[str]


@dataclass
class ProjectFingerprint:
  """High-level classification of a repository."""
  project_type: str
  confidence: float # 0.0 to 1.0
  frameworks: list[FrameworkFinding]
  entry_points: list[str]
  key_folders: list[str]
  summary: str
  warnings: list[str]


@dataclass
class ReadingPathItem:
  """An item in the suggested reading path."""
  order: int
  path: str
  reason: str
  estimated_minutes: int


@dataclass
class ComponentCard:
  """Detailed information card for an important file/component."""
  path: str
  title: str
  role: str
  why_it_matters: str
  connected_to: list[str]
  detected_items: list[str]
  suggested_test_ideas: list[str]
  suggested_bob_prompt: str


@dataclass
class QuizQuestion:
  """A quiz question for onboarding verification."""
  question: str
  options: list[str]
  correct_answer: str
  explanation: str


@dataclass
class GraphNode:
  """JSON-first graph node representation."""
  id: str # FileInfo.path
  label: str # FileInfo.name
  path: str
  role: str
  language: str
  size_bytes: int
  line_count: int
  is_test: bool


@dataclass
class GraphEdge:
  """JSON-first graph edge representation."""
  source: str # node id (file path)
  target: str # node id (file path)
  kind: str # "python_import", "js_import", "ts_import", "api_call", "inferred"
  confidence: float
  evidence: str
  is_test_edge: bool


@dataclass
class GraphData:
  """Complete graph data structure (JSON-first)."""
  nodes: list[GraphNode]
  edges: list[GraphEdge]
  view_mode: GraphViewMode
  filtered_roles: list[str] # roles included in this view


@dataclass
class TaskSuggestion:
  """A suggested development task based on repo analysis."""
  epic: str
  priority: str # "high", "medium", "low"
  files: list[str]
  evidence: list[str]
  why: str
  acceptance_criteria: list[str]
  suggested_workflow: str


@dataclass
class AgentWorkflow:
  """A structured workflow for an AI coding agent."""
  title: str
  goal: str
  ordered_steps: list[str]
  files_to_read: list[str]
  files_to_change: list[str]
  validation_steps: list[str]
  expected_output: str
  prompt: str


@dataclass
class SuggestedMilestone:
  """A grouping of related tasks into a milestone."""
  title: str
  goal: str
  tasks: list[TaskSuggestion]


@dataclass
class WorkPlan:
  """Complete work plan with epics, tasks, milestones, and workflows."""
  epics: list[str]
  tasks: list[TaskSuggestion]
  milestones: list[SuggestedMilestone]
  workflows: list[AgentWorkflow]


@dataclass
class TestInsight:
  """Intelligence about a test file and what it covers."""
  __test__ = False # Tell pytest this is not a test class

  test_file: str
  framework: str
  imports: list[str]
  likely_targets: list[str]
  covered_routes: list[str]
  missing_cases: list[str]
  suggested_tests: list[str]
  quality_signals: dict[str, int | bool]


@dataclass
class TestIntelligence:
  """Complete test intelligence for a repository."""
  __test__ = False # Tell pytest this is not a test class

  test_insights: list[TestInsight]
  missing_coverage: list[str]
  suggested_tests: list[str]
  test_plan: str
