"""AI assistant providers for RepoQuest."""

import json
import os
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from typing import Protocol

from repoquest.assistant_models import AssistantRequest, AssistantResponse, AssistantCitation


DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
CERTIFICATE_ERROR_MESSAGE = (
  "Network error: Python could not verify the TLS certificate for the AI provider. "
  "This usually means your local Python certificate trust store is missing or outdated. "
  "Update your OS or Python certificates, then try again. "
  "RepoQuest did not disable SSL verification."
)


def _load_local_env(env_path: str = ".env") -> None:
  """Load simple KEY=value pairs from local.env files without extra dependencies."""
  candidates = [
    Path(env_path),
    Path(__file__).resolve().parents[1] / env_path,
  ]

  path = next((candidate for candidate in candidates if candidate.exists()), None)
  if path is None:
    return

  for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if key and not os.environ.get(key):
      os.environ[key] = value


def _streamlit_secret(name: str) -> object | None:
  """Read a Streamlit secret if Streamlit is available and configured."""
  try:
    import streamlit as st

    if hasattr(st, "secrets") and name in st.secrets:
      return st.secrets[name]
  except (ImportError, FileNotFoundError, KeyError):
    return None
  return None


def _is_truthy(value: object | None) -> bool:
  """Parse bool-like environment/secret values."""
  if isinstance(value, bool):
    return value
  if value is None:
    return False
  return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_assistant_config() -> tuple[bool, str, str]:
  """Return assistant enabled flag, Claude API key, and Claude model."""
  _load_local_env()

  enabled_value = os.getenv("REPOQUEST_AI_ENABLED")
  if enabled_value is None:
    enabled_value = _streamlit_secret("REPOQUEST_AI_ENABLED")

  api_key = os.getenv("CLAUDE_API_KEY", "").strip()
  if not api_key:
    secret_key = _streamlit_secret("CLAUDE_API_KEY")
    api_key = str(secret_key or "").strip()

  model = os.getenv("CLAUDE_MODEL", "").strip()
  if not model:
    secret_model = _streamlit_secret("CLAUDE_MODEL")
    model = str(secret_model or "").strip()
  if not model:
    model = DEFAULT_CLAUDE_MODEL

  return _is_truthy(enabled_value), api_key, model


def _build_ssl_context() -> ssl.SSLContext:
  """Build a verifying TLS context, using certifi if it is already available."""
  try:
    import certifi  # type: ignore[import-not-found]

    return ssl.create_default_context(cafile=certifi.where())
  except (ImportError, OSError):
    return ssl.create_default_context()


def _is_certificate_verification_error(error: BaseException) -> bool:
  """Return True when urllib surfaced a TLS certificate trust failure."""
  if isinstance(error, ssl.SSLCertVerificationError):
    return True
  if isinstance(error, urllib.error.URLError) and error.reason is not None:
    reason = error.reason
    if isinstance(reason, ssl.SSLCertVerificationError):
      return True
    return "CERTIFICATE_VERIFY_FAILED" in str(reason) or "certificate verify failed" in str(reason)
  return "CERTIFICATE_VERIFY_FAILED" in str(error) or "certificate verify failed" in str(error)


class AssistantProvider(Protocol):
  """Protocol for AI assistant providers."""

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Generate a response from the AI assistant."""
    ...


class DisabledAssistantProvider:
  """Provider that always returns disabled status."""

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Return disabled status."""
    return AssistantResponse(
      status="disabled",
      response_text="",
      provider="disabled",
      model="none",
      message="AI Assistant is disabled. Enable it by setting REPOQUEST_AI_ENABLED=true and providing a CLAUDE_API_KEY.",
    )


class MockAssistantProvider:
  """Mock provider for testing."""

  def __init__(self, mock_response: str = "This is a mock AI response.", mock_citations: list[AssistantCitation] | None = None):
    self.mock_response = mock_response
    self.mock_citations = mock_citations or []

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Return a mock response."""
    return AssistantResponse(
      status="ok",
      response_text=self.mock_response,
      citations=self.mock_citations,
      provider="mock",
      model="mock-model",
    )


class ClaudeAssistantProvider:
  """Provider using Claude API via Anthropic Messages API."""

  def __init__(self, api_key: str | None = None, model: str | None = None):
    _, configured_api_key, configured_model = get_assistant_config()
    self.api_key = api_key if api_key is not None else configured_api_key
    self.model = model if model is not None else configured_model
    self.api_url = "https://api.anthropic.com/v1/messages"
    self.api_version = "2023-06-01"
    self.ssl_context = _build_ssl_context()

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Generate a response using Claude API."""
    if not self.api_key:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="claude",
        model=self.model,
        message="CLAUDE_API_KEY is not configured.",
      )

    try:
      # Build system message with safety instructions
      system_message = """You are a code analysis assistant for RepoQuest, a static repository analyzer.

IMPORTANT RULES:
1. Use ONLY the provided context and code snippets
2. Cite specific file paths when making file-specific claims
3. Label uncertainty clearly (e.g., "likely", "appears to", "suggests")
4. Do NOT claim that tests were run or executed
5. Do NOT instruct RepoQuest to execute uploaded code
6. Do NOT install dependencies or run commands
7. This is STATIC ANALYSIS ONLY - no code execution occurred

Your response should be:
- Concise and actionable
- Evidence-based with file path citations
- Honest about limitations
- Focused on the user's goal"""

      # Build user message from request
      user_message = request.to_prompt()

      # Prepare API request
      data = {
        "model": self.model,
        "max_tokens": request.max_tokens,
        "system": system_message,
        "messages": [
          {
            "role": "user",
            "content": user_message
          }
        ]
      }

      # Make API request
      req = urllib.request.Request(
        self.api_url,
        data=json.dumps(data).encode('utf-8'),
        headers={
          "Content-Type": "application/json",
          "x-api-key": self.api_key,
          "anthropic-version": self.api_version,
        },
        method="POST"
      )

      with urllib.request.urlopen(req, timeout=30, context=self.ssl_context) as response:
        result = json.loads(response.read().decode('utf-8'))

      # Extract response text
      if "content" in result and len(result["content"]) > 0:
        response_text = result["content"][0].get("text", "")
      else:
        response_text = ""

      if not response_text:
        return AssistantResponse(
          status="error",
          response_text="",
          provider="claude",
          model=self.model,
          message="Empty response from Claude API",
        )

      # Extract citations from response (simple heuristic: look for file paths in backticks)
      citations = self._extract_citations(response_text, request.evidence_files)

      return AssistantResponse(
        status="ok",
        response_text=response_text,
        citations=citations,
        provider="claude",
        model=self.model,
      )

    except urllib.error.HTTPError as e:
      error_body = e.read().decode('utf-8') if e.fp else ""
      return AssistantResponse(
        status="error",
        response_text="",
        provider="claude",
        model=self.model,
        message=f"Claude API error ({e.code}): {error_body[:200]}",
      )

    except urllib.error.URLError as e:
      if _is_certificate_verification_error(e):
        return AssistantResponse(
          status="error",
          response_text="",
          provider="claude",
          model=self.model,
          message=CERTIFICATE_ERROR_MESSAGE,
        )
      return AssistantResponse(
        status="error",
        response_text="",
        provider="claude",
        model=self.model,
        message=f"Network error: {str(e)}",
      )

    except Exception as e:
      if _is_certificate_verification_error(e):
        return AssistantResponse(
          status="error",
          response_text="",
          provider="claude",
          model=self.model,
          message=CERTIFICATE_ERROR_MESSAGE,
        )
      return AssistantResponse(
        status="error",
        response_text="",
        provider="claude",
        model=self.model,
        message=f"Unexpected error: {str(e)}",
      )

  def _extract_citations(self, response_text: str, evidence_files: list[str]) -> list[AssistantCitation]:
    """Extract file path citations from response text."""
    citations = []

    # Look for file paths mentioned in the response
    for file_path in evidence_files:
      if file_path in response_text or f"`{file_path}`" in response_text:
        citations.append(AssistantCitation(
          file_path=file_path,
          relevance="mentioned in response"
        ))

    return citations


def get_assistant_provider() -> AssistantProvider:
  """Get the appropriate assistant provider based on configuration."""
  ai_enabled, api_key, model = get_assistant_config()

  if not ai_enabled:
    return DisabledAssistantProvider()

  if not api_key:
    return DisabledAssistantProvider()

  return ClaudeAssistantProvider(api_key=api_key, model=model)

# Made with Bob
