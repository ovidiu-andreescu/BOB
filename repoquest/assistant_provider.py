"""AI assistant providers for RepoQuest."""

import json
import os
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Protocol

from repoquest.assistant_models import (
  AssistantRequest,
  AssistantResponse,
  AssistantCitation,
  AssistantJobStatus,
  AIRecommendationResult,
)


DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_SERVICE_TIMEOUT_SECONDS = 45.0
DEFAULT_SERVICE_POLL_INTERVAL_SECONDS = 0.5
CERTIFICATE_ERROR_MESSAGE = (
  "Network error: Python could not verify the TLS certificate for the AI provider. "
  "This usually means your local Python certificate trust store is missing or outdated. "
  "Update your OS or Python certificates, then try again. "
  "RepoQuest did not disable SSL verification."
)
LOCAL_MODEL_404_MESSAGE = (
  "Local model API returned 404 for the chat completions endpoint. "
  "RepoQuest expects an OpenAI-compatible endpoint at "
  "{api_url}. If /v1/models works but this endpoint does not, update your local model server "
  "or use an OpenAI-compatible server/profile. For Ollama, use a recent Ollama version and "
  "REPOQUEST_LOCAL_MODEL_BASE_URL=http://localhost:11434/v1."
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
    if key and key not in os.environ:
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


def get_assistant_config() -> tuple[bool, str, str, str, str, str]:
  """Return assistant enabled flag, provider type, Claude API key, Claude model, local base URL, and local model name."""
  _load_local_env()

  enabled_value = os.getenv("REPOQUEST_AI_ENABLED")
  if enabled_value is None:
    enabled_value = _streamlit_secret("REPOQUEST_AI_ENABLED")

  provider = os.getenv("REPOQUEST_ASSISTANT_PROVIDER", "").strip().lower()
  if not provider:
    secret_provider = _streamlit_secret("REPOQUEST_ASSISTANT_PROVIDER")
    provider = str(secret_provider or "").strip().lower()
  if not provider:
    provider = "claude"

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

  local_base_url = os.getenv("REPOQUEST_LOCAL_MODEL_BASE_URL", "").strip()
  if not local_base_url:
    secret_url = _streamlit_secret("REPOQUEST_LOCAL_MODEL_BASE_URL")
    local_base_url = str(secret_url or "").strip()

  local_model_name = os.getenv("REPOQUEST_LOCAL_MODEL_NAME", "").strip()
  if not local_model_name:
    secret_name = _streamlit_secret("REPOQUEST_LOCAL_MODEL_NAME")
    local_model_name = str(secret_name or "").strip()

  return _is_truthy(enabled_value), provider, api_key, model, local_base_url, local_model_name


def get_assistant_service_config() -> tuple[str, float]:
  """Return optional assistant service URL and timeout."""
  _load_local_env()

  service_url = os.getenv("REPOQUEST_ASSISTANT_SERVICE_URL", "").strip()
  if not service_url:
    secret_url = _streamlit_secret("REPOQUEST_ASSISTANT_SERVICE_URL")
    service_url = str(secret_url or "").strip()

  timeout_value = os.getenv("REPOQUEST_ASSISTANT_SERVICE_TIMEOUT_SECONDS", "").strip()
  if not timeout_value:
    secret_timeout = _streamlit_secret("REPOQUEST_ASSISTANT_SERVICE_TIMEOUT_SECONDS")
    timeout_value = str(secret_timeout or "").strip()

  try:
    timeout_seconds = float(timeout_value) if timeout_value else DEFAULT_SERVICE_TIMEOUT_SECONDS
  except ValueError:
    timeout_seconds = DEFAULT_SERVICE_TIMEOUT_SECONDS

  return service_url.rstrip("/"), max(1.0, timeout_seconds)


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


def _normalize_openai_base_url(base_url: str) -> str:
  """Normalize local OpenAI-compatible base URLs to include /v1 once."""
  cleaned = base_url.strip().rstrip("/")
  if not cleaned:
    return ""
  return cleaned if cleaned.endswith("/v1") else f"{cleaned}/v1"


class AssistantProvider(Protocol):
  """Protocol for AI assistant providers."""

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Generate a response from the AI assistant."""
    ...

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Generate code recommendations from repository analysis."""
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

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Return empty recommendations when disabled."""
    return AIRecommendationResult(
      recommendations=[],
      provider="disabled",
      model="none",
      context_pack=context_pack,
      warnings=["AI Assistant is disabled"],
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

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Generate mock recommendations for testing."""
    from repoquest.recommendation_generator import generate_mock_recommendations
    return generate_mock_recommendations(
      snapshot, fingerprint, routes, component_cards, work_plan, context_pack
    )


class AssistantServiceProvider:
  """Provider that submits requests to an asynchronous assistant service."""

  def __init__(self, service_url: str, timeout_seconds: float = DEFAULT_SERVICE_TIMEOUT_SECONDS):
    self.service_url = service_url.rstrip("/")
    self.timeout_seconds = timeout_seconds

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Generate recommendations via assistant service."""
    from repoquest.recommendation_generator import (
      create_recommendation_prompt,
      parse_ai_recommendations,
    )
    
    # Create recommendation request
    prompt = create_recommendation_prompt(context_pack, work_plan)
    request = AssistantRequest(
      section_id="recommendations",
      section_title="Code Recommendations",
      user_goal="Generate actionable code recommendations",
      context_summary=prompt,
      evidence_files=list(context_pack.evidence_snippets.keys()),
      capped_snippets=context_pack.evidence_snippets,
      max_tokens=2000,
    )
    
    # Get AI response
    response = self.generate(request)
    
    if response.status != "ok":
      return AIRecommendationResult(
        recommendations=[],
        provider="assistant-service",
        model="remote",
        context_pack=context_pack,
        warnings=[response.message or "Failed to generate recommendations"],
      )
    
    # Parse recommendations
    recommendations = parse_ai_recommendations(response.response_text, snapshot)
    
    return AIRecommendationResult(
      recommendations=recommendations,
      provider="assistant-service",
      model="remote",
      context_pack=context_pack,
    )

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Submit a request to the service and poll until it completes."""
    if not self.service_url:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message="REPOQUEST_ASSISTANT_SERVICE_URL is not configured.",
      )

    try:
      job_id = self._submit_job(request)
      return self._wait_for_job(job_id)
    except urllib.error.HTTPError as e:
      body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
      return AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message=f"Assistant service error ({e.code}): {body[:200]}",
      )
    except urllib.error.URLError as e:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message=f"Assistant service network error: {str(e)}",
      )
    except TimeoutError as e:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message=str(e),
      )
    except (ValueError, json.JSONDecodeError) as e:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message=f"Invalid assistant service response: {str(e)}",
      )

  def _submit_job(self, request: AssistantRequest) -> str:
    """Create a service job and return its id."""
    payload = json.dumps({"request": request.to_dict()}).encode("utf-8")
    http_request = urllib.request.Request(
      f"{self.service_url}/jobs",
      data=payload,
      headers={"Content-Type": "application/json"},
      method="POST",
    )

    with urllib.request.urlopen(http_request, timeout=10) as response:
      data = json.loads(response.read().decode("utf-8"))

    job_id = str(data.get("job_id", ""))
    if not job_id:
      raise ValueError("assistant service did not return a job_id")
    return job_id

  def _wait_for_job(self, job_id: str) -> AssistantResponse:
    """Poll service job status until a response is ready."""
    deadline = time.monotonic() + self.timeout_seconds

    while time.monotonic() < deadline:
      status = self._get_job_status(job_id)
      if status.is_terminal:
        if status.response:
          return status.response
        return AssistantResponse(
          status="error",
          response_text="",
          provider="assistant-service",
          model="remote",
          message=status.message or f"Assistant service job {job_id} finished without a response.",
        )
      time.sleep(DEFAULT_SERVICE_POLL_INTERVAL_SECONDS)

    raise TimeoutError(
      f"Assistant service job {job_id} timed out after {self.timeout_seconds:.0f}s."
    )

  def _get_job_status(self, job_id: str) -> AssistantJobStatus:
    """Fetch current job status from the service."""
    with urllib.request.urlopen(f"{self.service_url}/jobs/{job_id}", timeout=10) as response:
      data = json.loads(response.read().decode("utf-8"))

    if not isinstance(data, dict):
      raise ValueError("assistant service returned a non-object job status")
    return AssistantJobStatus.from_dict(data)


class LocalModelAssistantProvider:
  """Provider using OpenAI-compatible local model endpoints."""

  def __init__(self, base_url: str | None = None, model: str | None = None):
    _, _, _, _, configured_base_url, configured_model = get_assistant_config()
    self.base_url = _normalize_openai_base_url(base_url if base_url is not None else configured_base_url)
    self.model = model if model is not None else configured_model
    self.ssl_context = _build_ssl_context()

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Generate recommendations via local model."""
    from repoquest.recommendation_generator import (
      create_recommendation_prompt,
      parse_ai_recommendations,
    )
    
    # Create recommendation request
    prompt = create_recommendation_prompt(context_pack, work_plan)
    request = AssistantRequest(
      section_id="recommendations",
      section_title="Code Recommendations",
      user_goal="Generate actionable code recommendations",
      context_summary=prompt,
      evidence_files=list(context_pack.evidence_snippets.keys()),
      capped_snippets=context_pack.evidence_snippets,
      max_tokens=2000,
    )
    
    # Get AI response
    response = self.generate(request)
    
    if response.status != "ok":
      return AIRecommendationResult(
        recommendations=[],
        provider="local",
        model=self.model or "unknown",
        context_pack=context_pack,
        warnings=[response.message or "Failed to generate recommendations"],
      )
    
    # Parse recommendations
    recommendations = parse_ai_recommendations(response.response_text, snapshot)
    
    return AIRecommendationResult(
      recommendations=recommendations,
      provider="local",
      model=self.model or "unknown",
      context_pack=context_pack,
    )

  def generate(self, request: AssistantRequest) -> AssistantResponse:
    """Generate a response using OpenAI-compatible local model API."""
    if not self.base_url:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="local",
        model=self.model or "unknown",
        message="REPOQUEST_LOCAL_MODEL_BASE_URL is not configured.",
      )

    if not self.model:
      return AssistantResponse(
        status="error",
        response_text="",
        provider="local",
        model="unknown",
        message="REPOQUEST_LOCAL_MODEL_NAME is not configured.",
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

      # Prepare OpenAI-compatible API request
      data = {
        "model": self.model,
        "messages": [
          {
            "role": "system",
            "content": system_message
          },
          {
            "role": "user",
            "content": user_message
          }
        ],
        "max_tokens": request.max_tokens,
        "temperature": 0.7,
      }

      # Make API request to OpenAI-compatible endpoint
      api_url = f"{self.base_url}/chat/completions"
      req = urllib.request.Request(
        api_url,
        data=json.dumps(data).encode('utf-8'),
        headers={
          "Content-Type": "application/json",
        },
        method="POST"
      )

      with urllib.request.urlopen(req, timeout=60, context=self.ssl_context) as response:
        result = json.loads(response.read().decode('utf-8'))

      # Extract response text from OpenAI-compatible format
      if "choices" in result and len(result["choices"]) > 0:
        choice = result["choices"][0]
        if "message" in choice and "content" in choice["message"]:
          response_text = choice["message"]["content"]
        else:
          response_text = ""
      else:
        response_text = ""

      if not response_text:
        return AssistantResponse(
          status="error",
          response_text="",
          provider="local",
          model=self.model,
          message="Empty response from local model API",
        )

      # Extract citations from response
      citations = self._extract_citations(response_text, request.evidence_files)

      return AssistantResponse(
        status="ok",
        response_text=response_text,
        citations=citations,
        provider="local",
        model=self.model,
      )

    except urllib.error.HTTPError as e:
      error_body = e.read().decode('utf-8', errors='ignore') if e.fp else ""
      if e.code == 404:
        return AssistantResponse(
          status="error",
          response_text="",
          provider="local",
          model=self.model,
          message=LOCAL_MODEL_404_MESSAGE.format(api_url=api_url),
        )
      return AssistantResponse(
        status="error",
        response_text="",
        provider="local",
        model=self.model,
        message=f"Local model API error ({e.code}): {error_body[:200]}",
      )

    except urllib.error.URLError as e:
      if _is_certificate_verification_error(e):
        return AssistantResponse(
          status="error",
          response_text="",
          provider="local",
          model=self.model,
          message=CERTIFICATE_ERROR_MESSAGE,
        )
      return AssistantResponse(
        status="error",
        response_text="",
        provider="local",
        model=self.model,
        message=f"Network error connecting to local model: {str(e)}",
      )

    except Exception as e:
      if _is_certificate_verification_error(e):
        return AssistantResponse(
          status="error",
          response_text="",
          provider="local",
          model=self.model,
          message=CERTIFICATE_ERROR_MESSAGE,
        )
      return AssistantResponse(
        status="error",
        response_text="",
        provider="local",
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


class ClaudeAssistantProvider:
  """Provider using Claude API via Anthropic Messages API."""

  def __init__(self, api_key: str | None = None, model: str | None = None):
    _, _, configured_api_key, configured_model, _, _ = get_assistant_config()
    self.api_key = api_key if api_key is not None else configured_api_key
    self.model = model if model is not None else configured_model
    self.api_url = "https://api.anthropic.com/v1/messages"
    self.api_version = "2023-06-01"
    self.ssl_context = _build_ssl_context()

  def generate_recommendations(
      self,
      snapshot,
      fingerprint,
      routes,
      component_cards,
      work_plan,
      context_pack,
  ) -> AIRecommendationResult:
    """Generate recommendations via Claude API."""
    from repoquest.recommendation_generator import (
      create_recommendation_prompt,
      parse_ai_recommendations,
    )
    
    # Create recommendation request
    prompt = create_recommendation_prompt(context_pack, work_plan)
    request = AssistantRequest(
      section_id="recommendations",
      section_title="Code Recommendations",
      user_goal="Generate actionable code recommendations",
      context_summary=prompt,
      evidence_files=list(context_pack.evidence_snippets.keys()),
      capped_snippets=context_pack.evidence_snippets,
      max_tokens=2000,
    )
    
    # Get AI response
    response = self.generate(request)
    
    if response.status != "ok":
      return AIRecommendationResult(
        recommendations=[],
        provider="claude",
        model=self.model,
        context_pack=context_pack,
        warnings=[response.message or "Failed to generate recommendations"],
      )
    
    # Parse recommendations
    recommendations = parse_ai_recommendations(response.response_text, snapshot)
    
    return AIRecommendationResult(
      recommendations=recommendations,
      provider="claude",
      model=self.model,
      context_pack=context_pack,
    )

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
  ai_enabled, provider, api_key, model, local_base_url, local_model_name = get_assistant_config()
  service_url, service_timeout = get_assistant_service_config()

  if not ai_enabled:
    return DisabledAssistantProvider()

  # If service URL is configured, use the async service
  if service_url:
    return AssistantServiceProvider(service_url=service_url, timeout_seconds=service_timeout)

  # Route to appropriate provider based on configuration
  if provider == "mock":
    return MockAssistantProvider(
      mock_response=(
        "Mock assistant response. Review the deterministic RepoQuest evidence "
        "before making code changes."
      )
    )

  if provider == "local":
    if not local_base_url or not local_model_name:
      return DisabledAssistantProvider()
    return LocalModelAssistantProvider(base_url=local_base_url, model=local_model_name)

  # Default to Claude provider
  if not api_key:
    return DisabledAssistantProvider()

  return ClaudeAssistantProvider(api_key=api_key, model=model)

# Made with Bob
