"""Framework detection and project fingerprinting for RepoQuest.

This module orchestrates framework detection using the rules defined in framework_rules.py
and produces a ProjectFingerprint that answers "what kind of codebase is this?"
"""

from pathlib import Path

from repoquest.models import (
  RepositorySnapshot,
  FrameworkFinding,
  ProjectFingerprint,
)
from repoquest.indicator_rules import (
  ALL_FRAMEWORK_RULES,
  FrameworkRule,
  ENTRY_POINT_RULES,
  classify_project_type,
  KEY_FOLDERS,
  entry_point_priority,
  format_evidence,
)


def detect_framework(rule: FrameworkRule, snapshot: RepositorySnapshot) -> FrameworkFinding | None:
  """Detect a framework using a specific rule.

  Args:
    rule: The framework detection rule to apply
    snapshot: The repository snapshot to analyze

  Returns:
    FrameworkFinding if detected with sufficient confidence, None otherwise
  """
  evidence = []
  confidence = 0.0
  found_any_evidence = False

  # Check for required files (must have ALL)
  if rule.required_files:
    required_found = all(
      any(f.name == req_file for f in snapshot.files)
      for req_file in rule.required_files
    )
    if not required_found:
      return None # Missing required files, framework not present

  # Check for indicator files (having ANY increases confidence)
  indicator_file_found = False
  if rule.indicator_files:
    for indicator_file in rule.indicator_files:
      for file in snapshot.files:
        if file.name == indicator_file:
          evidence.append(format_evidence(file.path, f"Found {indicator_file}"))
          confidence += rule.file_match_boost
          found_any_evidence = True
          indicator_file_found = True

  # For frameworks with indicator_files, require at least one to be found
  # This prevents false positives from path/content matches alone
  if rule.indicator_files and not indicator_file_found:
    return None

  # Check for content patterns
  if rule.content_patterns:
    for pattern in rule.content_patterns:
      for file in snapshot.files:
        if file.skipped:
          continue
        if pattern.lower() in file.text_preview.lower():
          evidence.append(format_evidence(file.path, f"Contains '{pattern}'"))
          confidence += rule.content_match_boost
          found_any_evidence = True
          break # Only count each pattern once

  # Check for indicator paths
  if rule.indicator_paths:
    for indicator_path in rule.indicator_paths:
      for file in snapshot.files:
        if indicator_path.lower() in file.path.lower():
          evidence.append(format_evidence(file.path, f"Matches path pattern '{indicator_path}'"))
          confidence += rule.path_match_boost
          found_any_evidence = True
          break # Only count each path pattern once

  # If we found any evidence, add base confidence
  if found_any_evidence:
    confidence += rule.base_confidence

  # Cap confidence at 1.0
  confidence = min(confidence, 1.0)

  # Only return if we have meaningful confidence (>= 0.3)
  if confidence >= 0.3 and evidence:
    return FrameworkFinding(
      name=rule.name,
      category=rule.category,
      confidence=confidence,
      evidence=evidence[:5], # Limit evidence to top 5 items
    )

  return None


def detect_entry_points(snapshot: RepositorySnapshot) -> list[str]:
  """Detect likely entry points in the repository.

  Args:
    snapshot: The repository snapshot to analyze

  Returns:
    List of entry point paths (clean paths only, no descriptions)
  """
  entry_points = []

  for file in snapshot.files:
    if file.skipped:
      continue

    # Check against known entry point patterns
    for rule in ENTRY_POINT_RULES:
      pattern = rule.pattern
      if file.path.endswith(pattern) or pattern in file.path:
        entry_points.append(file.path)
        break

  entry_points.sort(key=entry_point_priority)

  return entry_points


def detect_key_folders(snapshot: RepositorySnapshot) -> list[str]:
  """Detect key folders in the repository.

  Args:
    snapshot: The repository snapshot to analyze

  Returns:
    List of key folder paths (clean paths only, no descriptions)
  """
  found_folders = set()
  key_folder_list = []

  for file in snapshot.files:
    path_parts = Path(file.path).parts

    # Check each part of the path
    for part in path_parts[:-1]: # Exclude the filename itself
      folder_key = part + "/"
      if folder_key in KEY_FOLDERS and folder_key not in found_folders:
        found_folders.add(folder_key)
        key_folder_list.append(folder_key)

  return sorted(key_folder_list)


def generate_fingerprint(snapshot: RepositorySnapshot) -> ProjectFingerprint:
  """Generate a project fingerprint from a repository snapshot.

  This is the main entry point for framework detection and project classification.

  Args:
    snapshot: The repository snapshot to analyze

  Returns:
    ProjectFingerprint with detected frameworks, project type, and metadata
  """
  warnings = list(snapshot.warnings) # Copy warnings from snapshot

  # Detect all frameworks
  frameworks = []
  for rule in ALL_FRAMEWORK_RULES:
    finding = detect_framework(rule, snapshot)
    if finding:
      frameworks.append(finding)

  # Sort frameworks by confidence (highest first)
  frameworks.sort(key=lambda f: f.confidence, reverse=True)

  # Detect entry points
  entry_points = detect_entry_points(snapshot)

  # Detect key folders
  key_folders = detect_key_folders(snapshot)

  # Classify project type
  framework_names = [f.name for f in frameworks]
  project_type, type_confidence = classify_project_type(framework_names, entry_points)

  # Generate summary
  if frameworks:
    top_frameworks = ", ".join(f.name for f in frameworks[:3])
    summary = f"Detected as {project_type} with {top_frameworks}"
  else:
    summary = f"Classified as {project_type} with limited framework detection"
    warnings.append("RepoQuest could not confidently detect specific frameworks")

  # Add warnings for low confidence
  if type_confidence < 0.5:
    warnings.append(
      "RepoQuest could not confidently classify this repo, "
      "but it found these likely entry points and important files"
    )

  # Add warning if no entry points found
  if not entry_points:
    warnings.append("No standard entry points detected")

  return ProjectFingerprint(
    project_type=project_type,
    confidence=type_confidence,
    frameworks=frameworks,
    entry_points=entry_points,
    key_folders=key_folders,
    summary=summary,
    warnings=warnings,
  )

# Made with Bob
