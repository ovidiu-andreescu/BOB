"""Data models for AI assistant functionality."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AssistantCitation:
  """A citation/evidence reference in an AI response."""
  file_path: str
  line_range: str | None = None
  snippet: str | None = None
  relevance: str | None = None

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "file_path": self.file_path,
      "line_range": self.line_range,
      "snippet": self.snippet,
      "relevance": self.relevance,
    }

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "AssistantCitation":
    """Build a citation from service JSON."""
    return cls(
      file_path=str(data.get("file_path", "")),
      line_range=_optional_str(data.get("line_range")),
      snippet=_optional_str(data.get("snippet")),
      relevance=_optional_str(data.get("relevance")),
    )


@dataclass
class AssistantRequest:
  """Request to the AI assistant."""
  section_id: str
  section_title: str
  user_goal: str
  context_summary: str
  evidence_files: list[str]
  capped_snippets: dict[str, str] # file_path -> snippet
  max_tokens: int = 1000

  def to_prompt(self) -> str:
    """Convert request to a prompt string."""
    lines = []
    lines.append(f"# {self.section_title}")
    lines.append("")
    lines.append(f"**Goal:** {self.user_goal}")
    lines.append("")
    lines.append("## Context")
    lines.append(self.context_summary)
    lines.append("")

    if self.evidence_files:
      lines.append("## Evidence Files")
      for file_path in self.evidence_files[:10]: # Limit to 10
        lines.append(f"- `{file_path}`")
      lines.append("")

    if self.capped_snippets:
      lines.append("## Code Snippets")
      for file_path, snippet in list(self.capped_snippets.items())[:5]: # Limit to 5
        lines.append(f"### {file_path}")
        lines.append("```")
        lines.append(snippet[:500]) # Cap each snippet
        if len(snippet) > 500:
          lines.append("... (truncated)")
        lines.append("```")
        lines.append("")

    return "\n".join(lines)

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "section_id": self.section_id,
      "section_title": self.section_title,
      "user_goal": self.user_goal,
      "context_summary": self.context_summary,
      "evidence_files": list(self.evidence_files),
      "capped_snippets": dict(self.capped_snippets),
      "max_tokens": self.max_tokens,
    }

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "AssistantRequest":
    """Build a request from service JSON."""
    evidence_files = data.get("evidence_files", [])
    capped_snippets = data.get("capped_snippets", {})

    return cls(
      section_id=str(data.get("section_id", "")),
      section_title=str(data.get("section_title", "")),
      user_goal=str(data.get("user_goal", "")),
      context_summary=str(data.get("context_summary", "")),
      evidence_files=(
        [str(item) for item in evidence_files]
        if isinstance(evidence_files, list)
        else []
      ),
      capped_snippets={
        str(key): str(value)
        for key, value in capped_snippets.items()
      } if isinstance(capped_snippets, dict) else {},
      max_tokens=int(data.get("max_tokens", 1000)),
    )


@dataclass
class AssistantResponse:
  """Response from the AI assistant."""
  status: Literal["disabled", "ok", "error", "invalid"]
  response_text: str
  citations: list[AssistantCitation] = field(default_factory=list)
  provider: str = "unknown"
  model: str = "unknown"
  message: str | None = None # Error or status message

  @property
  def is_valid(self) -> bool:
    """Check if response is valid and usable."""
    return self.status == "ok" and bool(self.response_text)

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "status": self.status,
      "response_text": self.response_text,
      "citations": [citation.to_dict() for citation in self.citations],
      "provider": self.provider,
      "model": self.model,
      "message": self.message,
    }

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "AssistantResponse":
    """Build a response from service JSON."""
    status = str(data.get("status", "error"))
    if status not in {"disabled", "ok", "error", "invalid"}:
      status = "error"

    citations = data.get("citations", [])
    return cls(
      status=status,  # type: ignore[arg-type]
      response_text=str(data.get("response_text", "")),
      citations=[
        AssistantCitation.from_dict(item)
        for item in citations
        if isinstance(item, dict)
      ] if isinstance(citations, list) else [],
      provider=str(data.get("provider", "unknown")),
      model=str(data.get("model", "unknown")),
      message=_optional_str(data.get("message")),
    )


@dataclass
class AssistantRunResult:
  """Result of running an assistant action."""
  section_id: str
  section_title: str
  request: AssistantRequest
  response: AssistantResponse
  source_id: str = ""  # Ties this result to a specific source snapshot
  timestamp: str = ""

  def __post_init__(self):
    """Set timestamp if not provided."""
    if not self.timestamp:
      from datetime import datetime, timezone
      self.timestamp = datetime.now(timezone.utc).isoformat()

  @property
  def is_success(self) -> bool:
    """Check if the run was successful."""
    return self.response.status == "ok"


@dataclass
class AssistantJobStatus:
  """Status returned by the asynchronous assistant service."""
  job_id: str
  status: Literal["queued", "running", "ok", "error", "invalid"]
  response: AssistantResponse | None = None
  message: str | None = None

  @property
  def is_terminal(self) -> bool:
    """Return True when the service finished processing this job."""
    return self.status in {"ok", "error", "invalid"}

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "AssistantJobStatus":
    """Build a job status from service JSON."""
    status = str(data.get("status", "error"))
    if status not in {"queued", "running", "ok", "error", "invalid"}:
      status = "error"

    response_data = data.get("response")
    return cls(
      job_id=str(data.get("job_id", "")),
      status=status,  # type: ignore[arg-type]
      response=(
        AssistantResponse.from_dict(response_data)
        if isinstance(response_data, dict)
        else None
      ),
      message=_optional_str(data.get("message")),
    )


@dataclass
class GeneratedDocPage:
  """AI-generated documentation page with validation."""
  title: str
  category: str
  source_files: list[str]
  content: str
  evidence: list[str]
  related_components: list[str] = field(default_factory=list)
  warnings: list[str] = field(default_factory=list)

  @property
  def is_valid(self) -> bool:
    """Check if the generated doc page is valid."""
    return bool(self.title and self.content and self.source_files)

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "title": self.title,
      "category": self.category,
      "source_files": list(self.source_files),
      "content": self.content,
      "evidence": list(self.evidence),
      "related_components": list(self.related_components),
      "warnings": list(self.warnings),
    }

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "GeneratedDocPage":
    """Build a doc page from JSON."""
    source_files = data.get("source_files", [])
    evidence = data.get("evidence", [])
    related_components = data.get("related_components", [])
    warnings = data.get("warnings", [])

    return cls(
      title=str(data.get("title", "")),
      category=str(data.get("category", "")),
      source_files=[str(f) for f in source_files] if isinstance(source_files, list) else [],
      content=str(data.get("content", "")),
      evidence=[str(e) for e in evidence] if isinstance(evidence, list) else [],
      related_components=[str(c) for c in related_components] if isinstance(related_components, list) else [],
      warnings=[str(w) for w in warnings] if isinstance(warnings, list) else [],
    )


@dataclass
class ContextPack:
  """Bounded context pack for AI assistant requests."""
  project_summary: str
  frameworks: list[str]
  entry_points: list[str]
  routes_summary: str
  component_summary: str
  test_summary: str
  workflow_summary: str
  evidence_snippets: dict[str, str]  # file_path -> capped snippet
  warnings: list[str]
  total_files_scanned: int

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "project_summary": self.project_summary,
      "frameworks": list(self.frameworks),
      "entry_points": list(self.entry_points),
      "routes_summary": self.routes_summary,
      "component_summary": self.component_summary,
      "test_summary": self.test_summary,
      "workflow_summary": self.workflow_summary,
      "evidence_snippets": dict(self.evidence_snippets),
      "warnings": list(self.warnings),
      "total_files_scanned": self.total_files_scanned,
    }


@dataclass
class CodeRecommendation:
  """AI-generated code recommendation with validation."""
  title: str
  category: str  # testing, documentation, api, frontend, backend, data_model, error_handling, refactor, developer_experience, unknown
  priority: str  # high, medium, low
  files: list[str]
  evidence: list[str]
  rationale: str
  proposed_change_summary: str
  test_plan: list[str]
  workflow: str
  confidence: float
  validation_status: str = "pending"  # pending, valid, invalid, downgraded
  validation_warnings: list[str] = field(default_factory=list)

  @property
  def is_valid(self) -> bool:
    """Check if recommendation passed validation."""
    return self.validation_status == "valid"

  @property
  def is_trusted(self) -> bool:
    """Check if recommendation can be shown as trusted."""
    return self.validation_status in {"valid", "downgraded"}

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "title": self.title,
      "category": self.category,
      "priority": self.priority,
      "files": list(self.files),
      "evidence": list(self.evidence),
      "rationale": self.rationale,
      "proposed_change_summary": self.proposed_change_summary,
      "test_plan": list(self.test_plan),
      "workflow": self.workflow,
      "confidence": self.confidence,
      "validation_status": self.validation_status,
      "validation_warnings": list(self.validation_warnings),
    }

  @classmethod
  def from_dict(cls, data: dict[str, object]) -> "CodeRecommendation":
    """Build a recommendation from JSON."""
    files = data.get("files", [])
    evidence = data.get("evidence", [])
    test_plan = data.get("test_plan", [])
    validation_warnings = data.get("validation_warnings", [])

    return cls(
      title=str(data.get("title", "")),
      category=str(data.get("category", "unknown")),
      priority=str(data.get("priority", "low")),
      files=[str(f) for f in files] if isinstance(files, list) else [],
      evidence=[str(e) for e in evidence] if isinstance(evidence, list) else [],
      rationale=str(data.get("rationale", "")),
      proposed_change_summary=str(data.get("proposed_change_summary", "")),
      test_plan=[str(t) for t in test_plan] if isinstance(test_plan, list) else [],
      workflow=str(data.get("workflow", "")),
      confidence=float(data.get("confidence", 0.0)),
      validation_status=str(data.get("validation_status", "pending")),
      validation_warnings=[str(w) for w in validation_warnings] if isinstance(validation_warnings, list) else [],
    )


@dataclass
class AIRecommendationResult:
  """Result of AI recommendation generation."""
  recommendations: list[CodeRecommendation]
  provider: str
  model: str
  context_pack: ContextPack
  timestamp: str = ""
  warnings: list[str] = field(default_factory=list)

  def __post_init__(self):
    """Set timestamp if not provided."""
    if not self.timestamp:
      from datetime import datetime, timezone
      self.timestamp = datetime.now(timezone.utc).isoformat()

  @property
  def valid_recommendations(self) -> list[CodeRecommendation]:
    """Return only validated recommendations."""
    return [r for r in self.recommendations if r.is_valid]

  @property
  def trusted_recommendations(self) -> list[CodeRecommendation]:
    """Return recommendations that can be shown as trusted."""
    return [r for r in self.recommendations if r.is_trusted]

  def to_dict(self) -> dict[str, object]:
    """Return a JSON-serializable representation."""
    return {
      "recommendations": [r.to_dict() for r in self.recommendations],
      "provider": self.provider,
      "model": self.model,
      "context_pack": self.context_pack.to_dict(),
      "timestamp": self.timestamp,
      "warnings": list(self.warnings),
    }


def _optional_str(value: object | None) -> str | None:
  """Return a stripped string or None for empty optional values."""
  if value is None:
    return None
  text = str(value)
  return text if text else None
