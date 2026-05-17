"""AI-first hybrid fusion layer for RepoQuest.

The fusion layer lets AI reinterpret deterministic findings without replacing
the scanner, route extractor, import graph, or safety warnings as facts.
"""

import json

from repoquest.assistant_context import build_context_pack
from repoquest.assistant_models import (
  AIFusionClaim,
  AIFusionOverride,
  AIFusionReport,
  AssistantRequest,
  AssistantResponse,
  FusedAnalysisResult,
)
from repoquest.assistant_validation import detect_secrets, validate_assistant_response
from repoquest.models import (
  ComponentCard,
  ImportEdge,
  ProjectFingerprint,
  ReadingPathItem,
  RepositorySnapshot,
  RouteInfo,
  TestIntelligence,
  WorkPlan,
)


ALLOWED_OVERRIDE_TARGETS = {
  "project_type",
  "framework_label",
  "framework_confidence",
  "entry_point_ranking",
  "architecture_summary",
  "reading_path_note",
  "component_note",
  "improvement_risk",
  "code_recommendation",
}

HIGH_DETERMINISTIC_CONFIDENCE = 0.75
PROJECT_TYPE_OVERRIDE_MIN_CONFIDENCE = 0.75
HIGH_CONFIDENCE_OVERRIDE_MARGIN = 0.10


def build_ai_fusion_request(
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    routes: list[RouteInfo],
    import_edges: list[ImportEdge],
    reading_path: list[ReadingPathItem],
    component_cards: list[ComponentCard],
    work_plan: WorkPlan | None = None,
    test_intelligence: TestIntelligence | None = None,
) -> AssistantRequest:
  """Build a bounded structured request for AI Fusion."""
  context_pack = build_context_pack(
    snapshot=snapshot,
    fingerprint=fingerprint,
    routes=routes,
    component_cards=component_cards,
    test_intelligence=test_intelligence,
    work_plan=work_plan,
  )

  role_counts: dict[str, int] = {}
  for file_info in snapshot.files:
    if file_info.skipped:
      continue
    role_counts[file_info.role] = role_counts.get(file_info.role, 0) + 1

  framework_evidence = [
    {
      "name": framework.name,
      "category": framework.category,
      "confidence": framework.confidence,
      "evidence": framework.evidence,
    }
    for framework in fingerprint.frameworks[:10]
  ]

  route_evidence = [
    {
      "method": route.method,
      "path": route.path,
      "file_path": route.file_path,
      "function_name": route.function_name,
    }
    for route in routes[:25]
  ]

  edge_summary = [
    {
      "source": edge.source,
      "target": edge.target,
      "kind": edge.kind,
      "confidence": edge.confidence,
    }
    for edge in import_edges[:40]
  ]

  reading_items = [
    {
      "order": item.order,
      "path": item.path,
      "reason": item.reason,
      "estimated_minutes": item.estimated_minutes,
    }
    for item in reading_path[:12]
  ]

  component_summary = [
    {
      "path": card.path,
      "role": card.role,
      "why_it_matters": card.why_it_matters,
      "connected_to": card.connected_to[:5],
      "detected_items": card.detected_items[:8],
    }
    for card in component_cards[:20]
  ]

  deterministic_context = {
    "project": {
      "source_name": snapshot.source_name,
      "project_type": fingerprint.project_type,
      "confidence": fingerprint.confidence,
      "summary": fingerprint.summary,
      "entry_points": fingerprint.entry_points,
      "key_folders": fingerprint.key_folders,
      "warnings": fingerprint.warnings,
    },
    "scan": {
      "total_files_seen": snapshot.total_files_seen,
      "total_files_scanned": snapshot.total_files_scanned,
      "warnings": snapshot.warnings,
      "role_counts": role_counts,
      "skipped_files": [
        {"path": file_info.path, "reason": file_info.skip_reason}
        for file_info in snapshot.files
        if file_info.skipped
      ][:20],
    },
    "framework_evidence": framework_evidence,
    "routes": route_evidence,
    "import_edges": edge_summary,
    "reading_path": reading_items,
    "component_cards": component_summary,
    "context_pack": context_pack.to_dict(),
  }

  evidence_files = _collect_evidence_files(
    snapshot=snapshot,
    fingerprint=fingerprint,
    routes=routes,
    component_cards=component_cards,
    reading_path=reading_path,
    context_snippet_paths=list(context_pack.evidence_snippets.keys()),
  )

  prompt = {
    "task": "AI Fusion: audit and improve RepoQuest deterministic interpretation.",
    "rules": [
      "Return one strict JSON object only. No markdown fences.",
      "Use only the provided deterministic context and snippets.",
      "Do not claim tests were run or code was executed.",
      "Do not ask RepoQuest to install dependencies or execute uploaded code.",
      "Only propose interpretation-level overrides.",
      "Every override must cite existing file paths in its evidence list.",
      "If deterministic analysis is already accurate, provide claims and no overrides.",
    ],
    "allowed_override_targets": sorted(ALLOWED_OVERRIDE_TARGETS),
    "schema": {
      "summary": "string",
      "claims": [
        {
          "claim_type": "string",
          "value": "string",
          "confidence": 0.0,
          "evidence": ["existing/path.py"],
          "rationale": "string",
        }
      ],
      "overrides": [
        {
          "target": "project_type",
          "original_value": "string or list",
          "proposed_value": "string or list",
          "confidence": 0.0,
          "evidence": ["existing/path.py"],
          "rationale": "string",
        }
      ],
      "architecture_summary": "string",
      "reading_path_notes": {"existing/path.py": "string"},
      "component_notes": {"existing/path.py": "string"},
      "risks": ["string"],
      "recommendations": ["string"],
    },
    "deterministic_context": deterministic_context,
  }

  return AssistantRequest(
    section_id="ai_fusion",
    section_title="AI Fusion Analyzer",
    user_goal=(
      "Challenge, confirm, or refine the deterministic project analysis using "
      "only cited repository evidence."
    ),
    context_summary=json.dumps(prompt, indent=2, sort_keys=True),
    evidence_files=evidence_files,
    capped_snippets=context_pack.evidence_snippets,
    max_tokens=2200,
  )


def run_ai_fusion(
    provider,
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    routes: list[RouteInfo],
    import_edges: list[ImportEdge],
    reading_path: list[ReadingPathItem],
    component_cards: list[ComponentCard],
    work_plan: WorkPlan | None = None,
    test_intelligence: TestIntelligence | None = None,
    source_id: str = "",
) -> FusedAnalysisResult:
  """Run AI Fusion through a provider and return a validated fused result."""
  request = build_ai_fusion_request(
    snapshot=snapshot,
    fingerprint=fingerprint,
    routes=routes,
    import_edges=import_edges,
    reading_path=reading_path,
    component_cards=component_cards,
    work_plan=work_plan,
    test_intelligence=test_intelligence,
  )
  response = provider.generate(request)
  response = validate_assistant_response(response, snapshot)
  return parse_ai_fusion_response(
    response=response,
    snapshot=snapshot,
    fingerprint=fingerprint,
    source_id=source_id,
  )


def parse_ai_fusion_response(
    response: AssistantResponse,
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    source_id: str = "",
) -> FusedAnalysisResult:
  """Parse and validate an AI Fusion response."""
  fallback = FusedAnalysisResult.deterministic(
    project_type=fingerprint.project_type,
    confidence=fingerprint.confidence,
    summary=fingerprint.summary,
    entry_points=fingerprint.entry_points,
    source_id=source_id,
  )

  if response.status != "ok":
    report = AIFusionReport(
      summary=response.message or "AI Fusion was unavailable; deterministic analysis is shown.",
      claims=[],
      overrides=[],
      provider=response.provider,
      model=response.model,
      validation_status="invalid",
      warnings=[response.message or "AI Fusion provider did not return a usable response."],
    )
    fallback.report = report
    return fallback

  try:
    data = json.loads(response.response_text.strip())
  except json.JSONDecodeError as exc:
    report = AIFusionReport(
      summary="AI Fusion returned non-JSON output; deterministic analysis is shown.",
      claims=[],
      overrides=[],
      provider=response.provider,
      model=response.model,
      validation_status="invalid",
      warnings=[f"Strict JSON parse failed: {exc}"],
    )
    fallback.report = report
    return fallback

  if not isinstance(data, dict):
    report = AIFusionReport(
      summary="AI Fusion returned an invalid schema; deterministic analysis is shown.",
      claims=[],
      overrides=[],
      provider=response.provider,
      model=response.model,
      validation_status="invalid",
      warnings=["AI Fusion response must be a JSON object."],
    )
    fallback.report = report
    return fallback

  report = AIFusionReport.from_dict(data)
  report.provider = response.provider
  report.model = response.model

  valid_paths = {file_info.path for file_info in snapshot.files if not file_info.skipped}
  report.claims = _validate_claims(report.claims, valid_paths, report.warnings)
  report.overrides = [
    _validate_override(override, valid_paths, fingerprint)
    for override in report.overrides
  ]
  report.reading_path_notes = _validate_path_map(
    report.reading_path_notes, valid_paths, report.warnings, "reading path note"
  )
  report.component_notes = _validate_path_map(
    report.component_notes, valid_paths, report.warnings, "component note"
  )

  applied = [override for override in report.overrides if override.is_applied]
  rejected = [override for override in report.overrides if override.status == "rejected"]
  disagreements = [
    override for override in report.overrides if override.status == "disagreement"
  ]

  report.validation_status = "valid"
  if rejected or disagreements or report.warnings:
    report.validation_status = "partial"
  if detect_secrets(response.response_text):
    report.validation_status = "invalid"
    report.warnings.append("AI Fusion response contained potential secrets.")

  final_project_type = fingerprint.project_type
  final_confidence = fingerprint.confidence
  final_summary = fingerprint.summary
  final_entry_points = list(fingerprint.entry_points)
  mode = "ai-confirmed" if report.validation_status in {"valid", "partial"} else "deterministic"

  for override in applied:
    if override.target == "project_type":
      final_project_type = str(override.proposed_value)
      final_confidence = max(fingerprint.confidence, override.confidence)
      final_summary = (
        f"AI Fusion adjusted the classification from {fingerprint.project_type} "
        f"to {final_project_type}: {override.rationale}"
      )
      mode = "ai-overridden"
    elif override.target == "entry_point_ranking":
      ranked = _coerce_string_list(override.proposed_value)
      if ranked:
        final_entry_points = ranked
        mode = "ai-overridden"

  if not applied and report.summary:
    final_summary = report.summary

  return FusedAnalysisResult(
    mode=mode,
    final_project_type=final_project_type,
    final_confidence=final_confidence,
    final_summary=final_summary,
    final_entry_points=final_entry_points,
    report=report,
    source_id=source_id,
  )


def generate_mock_fusion_response(request: AssistantRequest) -> AssistantResponse:
  """Generate a deterministic schema-valid mock AI Fusion response."""
  evidence = request.evidence_files[:3]
  primary = evidence[0] if evidence else ""
  payload = {
    "summary": (
      "AI Fusion reviewed the deterministic evidence and agrees with the "
      "current high-level repository interpretation."
    ),
    "claims": [
      {
        "claim_type": "project_classification",
        "value": "Deterministic classification is well supported by scanned evidence.",
        "confidence": 0.82,
        "evidence": evidence[:2],
        "rationale": "The detected entry points, framework evidence, and file roles align.",
      }
    ] if evidence else [],
    "overrides": [],
    "architecture_summary": (
      "The application appears to follow the deterministic layer map; use the "
      "dependency graph as the audit trail for file-level relationships."
    ),
    "reading_path_notes": {
      primary: "Start here because it anchors the detected application shape."
    } if primary else {},
    "component_notes": {},
    "risks": [
      "AI Fusion is evidence-bounded; skipped or oversized files may hide context."
    ],
    "recommendations": [
      "Use the deterministic route and import tables as the source of truth before editing."
    ],
  }
  return AssistantResponse(
    status="ok",
    response_text=json.dumps(payload),
    provider="mock",
    model="mock-fusion",
  )


def _collect_evidence_files(
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
    routes: list[RouteInfo],
    component_cards: list[ComponentCard],
    reading_path: list[ReadingPathItem],
    context_snippet_paths: list[str],
) -> list[str]:
  """Collect existing paths likely to matter for fusion evidence."""
  valid_paths = {file_info.path for file_info in snapshot.files if not file_info.skipped}
  ordered: list[str] = []

  candidates = []
  candidates.extend(fingerprint.entry_points)
  candidates.extend(route.file_path for route in routes)
  candidates.extend(item.path for item in reading_path)
  candidates.extend(card.path for card in component_cards)
  candidates.extend(context_snippet_paths)

  for path in candidates:
    if path in valid_paths and path not in ordered:
      ordered.append(path)

  return ordered[:20]


def _validate_claims(
    claims: list[AIFusionClaim],
    valid_paths: set[str],
    warnings: list[str],
) -> list[AIFusionClaim]:
  """Keep only claims whose evidence paths exist."""
  valid_claims = []
  for claim in claims:
    claim_warnings = _validate_evidence_paths(claim.evidence, valid_paths)
    if claim_warnings:
      warnings.append(
        f"Dropped AI claim '{claim.claim_type}' because {claim_warnings[0]}"
      )
      continue
    if not claim.evidence:
      warnings.append(f"Dropped AI claim '{claim.claim_type}' because evidence is missing.")
      continue
    if not 0.0 <= claim.confidence <= 1.0:
      warnings.append(f"Dropped AI claim '{claim.claim_type}' because confidence is invalid.")
      continue
    valid_claims.append(claim)
  return valid_claims


def _validate_override(
    override: AIFusionOverride,
    valid_paths: set[str],
    fingerprint: ProjectFingerprint,
) -> AIFusionOverride:
  """Validate one override and mark it applied, rejected, or disagreement."""
  warnings = []

  if override.target not in ALLOWED_OVERRIDE_TARGETS:
    warnings.append(f"Unsupported override target: {override.target}")

  if not 0.0 <= override.confidence <= 1.0:
    warnings.append("Confidence must be between 0.0 and 1.0.")

  warnings.extend(_validate_evidence_paths(override.evidence, valid_paths))
  missing_evidence = not override.evidence
  if missing_evidence:
    warnings.append("Every AI override must cite evidence paths.")

  if override.target == "project_type":
    if override.confidence < PROJECT_TYPE_OVERRIDE_MIN_CONFIDENCE:
      warnings.append("Project type override confidence is below 0.75.")
    if len(override.evidence) < 2:
      warnings.append("Project type override requires at least two evidence paths.")

  if missing_evidence:
    override.status = "disagreement"
    override.warnings = warnings
    return override

  if warnings:
    override.status = "rejected"
    override.warnings = warnings
    return override

  if (
      fingerprint.confidence >= HIGH_DETERMINISTIC_CONFIDENCE
      and override.confidence < fingerprint.confidence + HIGH_CONFIDENCE_OVERRIDE_MARGIN
  ):
    override.status = "disagreement"
    override.warnings = [
      (
        "Deterministic confidence is high; AI confidence must exceed it by "
        "0.10 before this can override the final interpretation."
      )
    ]
    return override

  if override.target == "entry_point_ranking":
    proposed_paths = _coerce_string_list(override.proposed_value)
    missing = [path for path in proposed_paths if path not in valid_paths]
    if missing:
      override.status = "rejected"
      override.warnings = [f"Proposed entry points are not scanned files: {', '.join(missing[:3])}"]
      return override

  override.status = "applied"
  override.warnings = []
  return override


def _validate_evidence_paths(evidence: list[str], valid_paths: set[str]) -> list[str]:
  """Return warnings for evidence items that are not exact scanned file paths."""
  missing = [path for path in evidence if path not in valid_paths]
  if missing:
    return [f"evidence paths are not in the current snapshot: {', '.join(missing[:3])}"]
  return []


def _validate_path_map(
    path_map: dict[str, str],
    valid_paths: set[str],
    warnings: list[str],
    label: str,
) -> dict[str, str]:
  """Drop path-keyed notes that do not reference scanned files."""
  clean: dict[str, str] = {}
  for path, note in path_map.items():
    if path not in valid_paths:
      warnings.append(f"Dropped AI {label} for nonexistent path: {path}")
      continue
    clean[path] = note
  return clean


def _coerce_string_list(value: object) -> list[str]:
  """Coerce string or list values into a list of strings."""
  if isinstance(value, list):
    return [str(item) for item in value]
  if isinstance(value, str):
    return [value] if value else []
  return []
