"""Build bounded context packs for AI assistant from deterministic RepoQuest data."""

from repoquest.models import (
  RepositorySnapshot,
  ProjectFingerprint,
  FileInfo,
  RouteInfo,
  ReadingPathItem,
  ComponentCard,
  TestIntelligence,
  WorkPlan,
)
from repoquest.assistant_models import AssistantRequest

# Maximum snippet size to send to AI
MAX_SNIPPET_CHARS = 800


def _cap_snippet(text: str, max_chars: int = MAX_SNIPPET_CHARS) -> str:
  """Cap a text snippet to a maximum size."""
  if len(text) <= max_chars:
    return text
  return text[:max_chars] + "\n... (truncated)"


def _is_safe_file(file_info: FileInfo) -> bool:
  """Check if a file is safe to include in context."""
  if file_info.skipped:
    return False

  # Skip env files and secrets
  name_lower = file_info.name.lower()
  if any(pattern in name_lower for pattern in [".env", "secret", "password", "token", "key", "credential"]):
    return False

  # Skip binary-like files
  if file_info.suffix in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz"]:
    return False

  return True


def build_overview_context(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
) -> AssistantRequest:
  """Build context for overview/summary AI action."""
  context_lines = []
  context_lines.append(f"**Project Type:** {fingerprint.project_type}")
  context_lines.append(f"**Confidence:** {fingerprint.confidence * 100:.0f}%")
  context_lines.append("")
  context_lines.append(fingerprint.summary)
  context_lines.append("")

  if fingerprint.frameworks:
    context_lines.append("**Detected Frameworks:**")
    for fw in fingerprint.frameworks[:5]:
      context_lines.append(f"- {fw.name} ({fw.category})")
    context_lines.append("")

  if fingerprint.entry_points:
    context_lines.append("**Entry Points:**")
    for ep in fingerprint.entry_points[:5]:
      context_lines.append(f"- `{ep}`")
    context_lines.append("")

  context_lines.append(f"**Files Scanned:** {snapshot.total_files_scanned}")
  context_lines.append("")
  context_lines.append("*Note: This analysis is based on static code scanning without executing the code.*")

  # Collect evidence files
  evidence_files = fingerprint.entry_points[:5]

  # Collect snippets from entry points
  snippets = {}
  for ep in fingerprint.entry_points[:3]:
    file_info = next((f for f in snapshot.files if f.path == ep), None)
    if file_info and _is_safe_file(file_info) and file_info.text_preview:
      snippets[ep] = _cap_snippet(file_info.text_preview)

  return AssistantRequest(
    section_id="overview",
    section_title="Repository Overview",
    user_goal="Generate a concise summary of this repository's purpose, architecture, and key components",
    context_summary="\n".join(context_lines),
    evidence_files=evidence_files,
    capped_snippets=snippets,
    max_tokens=1000,
  )


def build_file_context(
  file_info: FileInfo,
  snapshot: RepositorySnapshot,
  routes: list[RouteInfo] | None = None,
) -> AssistantRequest:
  """Build context for a specific file AI action."""
  context_lines = []
  context_lines.append(f"**File:** `{file_info.path}`")
  context_lines.append(f"**Role:** {file_info.role.replace('_', ' ').title()}")
  context_lines.append(f"**Language:** {file_info.language}")
  context_lines.append(f"**Lines:** {file_info.line_count}")
  context_lines.append("")

  # Add route info if this is a route file
  if routes:
    file_routes = [r for r in routes if r.file_path == file_info.path]
    if file_routes:
      context_lines.append("**Detected Routes:**")
      for route in file_routes[:10]:
        context_lines.append(f"- {route.method} {route.path}")
      context_lines.append("")

  context_lines.append("*Note: This is static analysis without code execution.*")

  snippets = {}
  if _is_safe_file(file_info) and file_info.text_preview:
    snippets[file_info.path] = _cap_snippet(file_info.text_preview)

  return AssistantRequest(
    section_id=f"file_{file_info.path}",
    section_title=f"File Analysis: {file_info.name}",
    user_goal=f"Explain the purpose and key functionality of {file_info.path}, identify potential issues, and suggest improvements",
    context_summary="\n".join(context_lines),
    evidence_files=[file_info.path],
    capped_snippets=snippets,
    max_tokens=1200,
  )


def build_component_context(
  component_card: ComponentCard,
  snapshot: RepositorySnapshot,
) -> AssistantRequest:
  """Build context for a component card AI action."""
  context_lines = []
  context_lines.append(f"**Component:** `{component_card.path}`")
  context_lines.append(f"**Role:** {component_card.role}")
  context_lines.append("")
  context_lines.append(f"**Why it matters:** {component_card.why_it_matters}")
  context_lines.append("")

  if component_card.connected_to:
    context_lines.append("**Connected to:**")
    for conn in component_card.connected_to[:5]:
      context_lines.append(f"- `{conn}`")
    context_lines.append("")

  if component_card.detected_items:
    context_lines.append("**Detected items:**")
    for item in component_card.detected_items[:5]:
      context_lines.append(f"- {item}")
    context_lines.append("")

  context_lines.append("*Note: This is static analysis without code execution.*")

  # Get file snippet
  file_info = next((f for f in snapshot.files if f.path == component_card.path), None)
  snippets = {}
  if file_info and _is_safe_file(file_info) and file_info.text_preview:
    snippets[component_card.path] = _cap_snippet(file_info.text_preview)

  return AssistantRequest(
    section_id=f"component_{component_card.path}",
    section_title=f"Component: {component_card.title}",
    user_goal="Identify risks, edge cases, and suggest specific test cases for this component",
    context_summary="\n".join(context_lines),
    evidence_files=[component_card.path] + component_card.connected_to[:3],
    capped_snippets=snippets,
    max_tokens=1000,
  )


def build_test_context(
  test_intelligence: TestIntelligence,
  snapshot: RepositorySnapshot,
) -> AssistantRequest:
  """Build context for test intelligence AI action."""
  context_lines = []
  context_lines.append(f"**Test Files:** {len(test_intelligence.test_insights)}")
  context_lines.append("")

  if test_intelligence.test_insights:
    context_lines.append("**Test Inventory:**")
    for insight in test_intelligence.test_insights[:5]:
      context_lines.append(f"- `{insight.test_file}` ({insight.framework})")
      context_lines.append(f" - Covers: {len(insight.likely_targets)} files")
      context_lines.append(f" - Routes: {len(insight.covered_routes)}")
    context_lines.append("")

  if test_intelligence.missing_coverage:
    context_lines.append(f"**Missing Coverage:** {len(test_intelligence.missing_coverage)} items")
    for item in test_intelligence.missing_coverage[:5]:
      context_lines.append(f"- {item}")
    context_lines.append("")

  context_lines.append("*Note: This is static analysis. No tests were actually executed.*")

  # Collect test file snippets
  snippets = {}
  for insight in test_intelligence.test_insights[:3]:
    file_info = next((f for f in snapshot.files if f.path == insight.test_file), None)
    if file_info and _is_safe_file(file_info) and file_info.text_preview:
      snippets[insight.test_file] = _cap_snippet(file_info.text_preview)

  evidence_files = [t.test_file for t in test_intelligence.test_insights[:5]]

  return AssistantRequest(
    section_id="test_intelligence",
    section_title="Test Intelligence",
    user_goal="Generate a comprehensive test expansion plan with specific test cases to add",
    context_summary="\n".join(context_lines),
    evidence_files=evidence_files,
    capped_snippets=snippets,
    max_tokens=1200,
  )


def build_workflow_context(
  work_plan: WorkPlan,
  snapshot: RepositorySnapshot,
) -> AssistantRequest:
  """Build context for work plan/workflow AI action."""
  context_lines = []
  context_lines.append(f"**Epics:** {len(work_plan.epics)}")
  context_lines.append(f"**Tasks:** {len(work_plan.tasks)}")
  context_lines.append(f"**Workflows:** {len(work_plan.workflows)}")
  context_lines.append("")

  if work_plan.epics:
    context_lines.append("**Epics:**")
    for epic in work_plan.epics[:5]:
      context_lines.append(f"- {epic}")
    context_lines.append("")

  if work_plan.tasks:
    context_lines.append("**Sample Tasks:**")
    for task in work_plan.tasks[:5]:
      context_lines.append(f"- [{task.priority}] {task.why}")
    context_lines.append("")

  context_lines.append("*Note: This is based on static analysis without code execution.*")

  # Collect evidence files from tasks
  evidence_files = []
  for task in work_plan.tasks[:5]:
    evidence_files.extend(task.files[:2])
  evidence_files = list(set(evidence_files))[:10] # Dedupe and limit

  return AssistantRequest(
    section_id="work_plan",
    section_title="Work Plan & Workflows",
    user_goal="Refine the work plan, prioritize tasks, and suggest implementation strategies",
    context_summary="\n".join(context_lines),
    evidence_files=evidence_files,
    capped_snippets={},
    max_tokens=1200,
  )


def build_documentation_context(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
) -> AssistantRequest:
  """Build context for documentation/export AI action."""
  context_lines = []
  context_lines.append(f"**Project:** {fingerprint.project_type}")
  context_lines.append(f"**Files:** {snapshot.total_files_scanned}")
  context_lines.append("")

  # Check for existing README
  readme = next((f for f in snapshot.files if f.name.lower() == "readme.md"), None)
  if readme and readme.text_preview:
    context_lines.append("**Existing README found**")
    context_lines.append("")

  context_lines.append("**Frameworks:**")
  for fw in fingerprint.frameworks[:5]:
    context_lines.append(f"- {fw.name}")
  context_lines.append("")

  context_lines.append("*Note: This is static analysis without code execution.*")

  snippets = {}
  if readme and _is_safe_file(readme) and readme.text_preview:
    snippets["README.md"] = _cap_snippet(readme.text_preview)

  return AssistantRequest(
    section_id="documentation",
    section_title="Documentation Enhancement",
    user_goal="Suggest improvements to the onboarding documentation and README",
    context_summary="\n".join(context_lines),
    evidence_files=["README.md"] if readme else [],
    capped_snippets=snippets,
    max_tokens=1000,
  )

# Made with Bob
