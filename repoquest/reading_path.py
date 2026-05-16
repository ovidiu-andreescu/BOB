"""Generate a suggested reading path for repository onboarding."""

from repoquest.models import (
  RepositorySnapshot,
  ProjectFingerprint,
  FileInfo,
  ReadingPathItem,
)
from repoquest.config import MAX_READING_PATH_ITEMS
from repoquest.response_templates import (
  estimate_reading_minutes,
  get_assistant_action_for_file,
  get_improvement_ideas_for_file,
  get_language_for_code,
  get_reading_priority,
  get_reading_reason,
  get_understand_points_for_file,
)


def _calculate_file_priority(file_info: FileInfo, fingerprint: ProjectFingerprint) -> tuple[int, int]:
  """Calculate priority for a file in the reading path.

  Returns:
    Tuple of (category_priority, subcategory_priority) where lower is higher priority
  """
  return get_reading_priority(file_info)


def _estimate_reading_minutes(file_info: FileInfo) -> int:
  """Estimate how many minutes to spend reading a file."""
  return estimate_reading_minutes(file_info)


def _generate_reading_reason(file_info: FileInfo, fingerprint: ProjectFingerprint) -> str:
  """Generate a reason why this file should be read."""
  return get_reading_reason(file_info)


def generate_reading_path(
  snapshot: RepositorySnapshot,
  fingerprint: ProjectFingerprint,
) -> list[ReadingPathItem]:
  """Generate a suggested 30-minute reading path for onboarding.

  Args:
    snapshot: The repository snapshot
    fingerprint: The project fingerprint

  Returns:
    List of ReadingPathItem objects in suggested reading order
  """
  # Filter to non-skipped files and exclude __init__.py unless it's substantial
  candidates = []
  for f in snapshot.files:
    if f.skipped:
      continue
    # Skip __init__.py files unless they have substantial content (>50 lines)
    if f.name == "__init__.py" and f.line_count < 50:
      continue
    candidates.append(f)

  # Sort by priority
  candidates.sort(key=lambda f: _calculate_file_priority(f, fingerprint))

  # Build reading path
  reading_path = []
  total_minutes = 0
  target_minutes = 30

  for file_info in candidates:
    if len(reading_path) >= MAX_READING_PATH_ITEMS:
      break

    # Stop if we've exceeded target time (but always include at least 3 items)
    if total_minutes >= target_minutes and len(reading_path) >= 3:
      break

    minutes = _estimate_reading_minutes(file_info)
    reason = _generate_reading_reason(file_info, fingerprint)

    reading_path.append(ReadingPathItem(
      order=len(reading_path) + 1,
      path=file_info.path,
      reason=reason,
      estimated_minutes=minutes,
    ))

    total_minutes += minutes

  return reading_path


def get_language_for_st_code(file_info: FileInfo) -> str | None:
  """
  Get the language string for st.code() syntax highlighting.

  Args:
    file_info: FileInfo object

  Returns:
    Language string for st.code() or None for no highlighting
  """
  return get_language_for_code(file_info)


def get_understand_points(file_info: FileInfo) -> list[str]:
  """
  Generate deterministic "what to understand" points for a file.

  Args:
    file_info: FileInfo object

  Returns:
    List of understanding points
  """
  return get_understand_points_for_file(file_info)


def get_improvement_ideas(file_info: FileInfo) -> list[str]:
  """
  Generate deterministic improvement suggestions for a file.

  Args:
    file_info: FileInfo object

  Returns:
    List of improvement ideas
  """
  return get_improvement_ideas_for_file(file_info)


def get_bob_prompt_for_file(file_info: FileInfo) -> str:
  """
  Generate an AI assistant action for deeper analysis of a file.

  Args:
    file_info: FileInfo object

  Returns:
    Suggested AI assistant action string
  """
  return get_assistant_action_for_file(file_info)
