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


@dataclass
class AssistantRunResult:
  """Result of running an assistant action."""
  section_id: str
  section_title: str
  request: AssistantRequest
  response: AssistantResponse
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
