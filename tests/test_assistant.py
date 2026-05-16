"""Tests for AI assistant modules."""

import ssl
import urllib.error

import pytest
from repoquest.assistant_models import (
  AssistantCitation,
  AssistantRequest,
  AssistantResponse,
  AssistantRunResult,
)
from repoquest.assistant_provider import (
  ClaudeAssistantProvider,
  DisabledAssistantProvider,
  MockAssistantProvider,
  get_assistant_config,
  get_assistant_provider,
)
from repoquest.assistant_validation import (
  validate_assistant_response,
  format_validation_message,
)
from repoquest.assistant_context import (
  build_overview_context,
  build_component_context,
)
from repoquest.models import (
  RepositorySnapshot,
  FileInfo,
  ProjectFingerprint,
  FrameworkFinding,
  ComponentCard,
)


def test_assistant_citation():
  """Test AssistantCitation model."""
  citation = AssistantCitation(
    file_path="backend/main.py",
    line_range="10-20",
    snippet="def main():",
    relevance="Entry point"
  )
  assert citation.file_path == "backend/main.py"
  assert citation.line_range == "10-20"


def test_assistant_request():
  """Test AssistantRequest model."""
  request = AssistantRequest(
    section_id="overview",
    section_title="Repository Overview",
    user_goal="Understand project structure",
    context_summary="React + FastAPI app",
    evidence_files=["backend/main.py"],
    capped_snippets={"backend/main.py": "from fastapi import FastAPI"},
  )

  prompt = request.to_prompt()
  assert "Repository Overview" in prompt
  assert "Understand project structure" in prompt
  assert "React + FastAPI app" in prompt
  assert "backend/main.py" in prompt


def test_assistant_response():
  """Test AssistantResponse model."""
  response = AssistantResponse(
    status="ok",
    response_text="This is a FastAPI backend",
    citations=[AssistantCitation(file_path="backend/main.py")],
    provider="mock",
    model="mock-model",
  )

  assert response.is_valid
  assert response.status == "ok"
  assert len(response.citations) == 1


def test_assistant_run_result():
  """Test AssistantRunResult model with auto timestamp."""
  request = AssistantRequest(
    section_id="test",
    section_title="Test Section",
    user_goal="Test",
    context_summary="Test",
    evidence_files=[],
    capped_snippets={},
  )
  response = AssistantResponse(
    status="ok",
    response_text="Test response",
    provider="mock",
    model="mock",
  )

  result = AssistantRunResult(
    section_id="test",
    section_title="Test Section",
    request=request,
    response=response,
  )

  assert result.section_id == "test"
  assert result.is_success
  assert result.timestamp # Should be auto-generated


def test_disabled_provider():
  """Test DisabledAssistantProvider."""
  provider = DisabledAssistantProvider()
  request = AssistantRequest(
    section_id="test",
    section_title="Test",
    user_goal="Test",
    context_summary="Test",
    evidence_files=[],
    capped_snippets={},
  )

  response = provider.generate(request)
  assert response.status == "disabled"
  assert response.message and "disabled" in response.message.lower()


def test_mock_provider():
  """Test MockAssistantProvider."""
  mock_text = "This is a mock response"
  mock_citations = [AssistantCitation(file_path="test.py")]

  provider = MockAssistantProvider(
    mock_response=mock_text,
    mock_citations=mock_citations,
  )

  request = AssistantRequest(
    section_id="test",
    section_title="Test",
    user_goal="Test",
    context_summary="Test",
    evidence_files=[],
    capped_snippets={},
  )

  response = provider.generate(request)
  assert response.status == "ok"
  assert response.response_text == mock_text
  assert len(response.citations) == 1
  assert response.provider == "mock"


def test_assistant_config_loads_local_env(tmp_path, monkeypatch):
  """Test assistant config reads local.env values without python-dotenv."""
  monkeypatch.chdir(tmp_path)
  monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)
  monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
  monkeypatch.delenv("CLAUDE_MODEL", raising=False)

  (tmp_path / ".env").write_text(
    "REPOQUEST_AI_ENABLED=true\n"
    "CLAUDE_API_KEY=test-key\n"
    "CLAUDE_MODEL=test-model\n",
    encoding="utf-8",
  )

  enabled, api_key, model = get_assistant_config()

  assert enabled is True
  assert api_key == "test-key"
  assert model == "test-model"


def test_assistant_provider_uses_local_env(tmp_path, monkeypatch):
  """Test local.env enables the real provider path when a key is present."""
  monkeypatch.chdir(tmp_path)
  monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)
  monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
  monkeypatch.delenv("CLAUDE_MODEL", raising=False)

  (tmp_path / ".env").write_text(
    "REPOQUEST_AI_ENABLED=true\n"
    "CLAUDE_API_KEY=test-key\n",
    encoding="utf-8",
  )

  provider = get_assistant_provider()

  assert not isinstance(provider, DisabledAssistantProvider)


def test_claude_provider_reports_certificate_trust_error(monkeypatch):
  """Test certificate verification failures get a clear user-facing message."""
  provider = ClaudeAssistantProvider(api_key="test-key", model="test-model")

  def fake_urlopen(*args, **kwargs):
    raise urllib.error.URLError(
      ssl.SSLCertVerificationError(
        "certificate verify failed: unable to get local issuer certificate"
      )
    )

  monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

  response = provider.generate(
    AssistantRequest(
      section_id="test",
      section_title="Test",
      user_goal="Test",
      context_summary="Test",
      evidence_files=[],
      capped_snippets={},
    )
  )

  assert response.status == "error"
  assert response.message
  assert "could not verify the TLS certificate" in response.message
  assert "did not disable SSL verification" in response.message


def test_claude_provider_uses_verifying_ssl_context(monkeypatch):
  """Test Claude requests pass an SSL context without disabling verification."""
  provider = ClaudeAssistantProvider(api_key="test-key", model="test-model")
  captured = {}

  class FakeHTTPResponse:
    def __enter__(self):
      return self

    def __exit__(self, exc_type, exc, traceback):
      return False

    def read(self):
      return b'{"content":[{"text":"See backend/main.py for details."}]}'

  def fake_urlopen(req, timeout, context):
    captured["context"] = context
    return FakeHTTPResponse()

  monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

  response = provider.generate(
    AssistantRequest(
      section_id="test",
      section_title="Test",
      user_goal="Test",
      context_summary="Test",
      evidence_files=["backend/main.py"],
      capped_snippets={"backend/main.py": "from fastapi import FastAPI"},
    )
  )

  assert response.status == "ok"
  assert isinstance(captured["context"], ssl.SSLContext)
  assert captured["context"].verify_mode == ssl.CERT_REQUIRED
  assert captured["context"].check_hostname is True


def test_validation_empty_response():
  """Test validation rejects empty responses."""
  response = AssistantResponse(
    status="ok",
    response_text="",
    provider="mock",
    model="mock",
  )

  validated = validate_assistant_response(response)
  assert validated.status == "invalid"
  assert validated.message and "empty" in validated.message.lower()


def test_validation_invalid_citations():
  """Test validation rejects citations for non-existent files."""
  snapshot = RepositorySnapshot(
    source_name="test",
    files=[
      FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="entrypoint",
        text_preview="test",
        line_count=10,
      )
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  response = AssistantResponse(
    status="ok",
    response_text="Valid response",
    citations=[AssistantCitation(file_path="nonexistent.py")],
    provider="mock",
    model="mock",
  )

  validated = validate_assistant_response(response, snapshot)
  assert validated.status == "invalid"
  assert validated.message and " not in snapshot" in validated.message.lower()


def test_validation_forbidden_test_execution_claims():
  """Test validation rejects claims of test execution."""
  response = AssistantResponse(
    status="ok",
    response_text="I ran the tests and they all passed.",
    provider="mock",
    model="mock",
  )

  validated = validate_assistant_response(response)
  assert validated.status == "invalid"
  assert validated.message and "test execution" in validated.message.lower()


def test_validation_forbidden_code_execution_instructions():
  """Test validation rejects instructions to execute code."""
  response = AssistantResponse(
    status="ok",
    response_text="Now run this code to see the results.",
    provider="mock",
    model="mock",
  )

  validated = validate_assistant_response(response)
  assert validated.status == "invalid"
  assert validated.message and "execute" in validated.message.lower()


def test_validation_valid_response():
  """Test validation passes valid responses."""
  snapshot = RepositorySnapshot(
    source_name="test",
    files=[
      FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="entrypoint",
        text_preview="test",
        line_count=10,
      )
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  response = AssistantResponse(
    status="ok",
    response_text="This appears to be a FastAPI backend based on backend/main.py",
    citations=[AssistantCitation(file_path="backend/main.py")],
    provider="mock",
    model="mock",
  )

  validated = validate_assistant_response(response, snapshot)
  assert validated.status == "ok"
  assert validated.response_text == response.response_text


def test_format_validation_message():
  """Test validation message formatting."""
  disabled = AssistantResponse(status="disabled", response_text="", provider="mock", model="mock")
  assert "disabled" in format_validation_message(disabled).lower()

  error = AssistantResponse(status="error", response_text="", provider="mock", model="mock", message="API error")
  assert "error" in format_validation_message(error).lower()

  invalid = AssistantResponse(status="invalid", response_text="", provider="mock", model="mock", message="Invalid")
  assert "invalid" in format_validation_message(invalid).lower()


def test_build_overview_context():
  """Test building overview context."""
  snapshot = RepositorySnapshot(
    source_name="test-repo",
    files=[
      FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="entrypoint",
        text_preview="from fastapi import FastAPI\napp = FastAPI()",
        line_count=10,
      )
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  fingerprint = ProjectFingerprint(
    project_type="Full-stack web application",
    confidence=0.9,
    frameworks=[
      FrameworkFinding(
        name="FastAPI",
        category="backend",
        confidence=0.95,
        evidence=["backend/main.py: from fastapi import FastAPI"],
      )
    ],
    entry_points=["backend/main.py"],
    key_folders=["backend"],
    summary="A FastAPI backend application",
    warnings=[],
  )

  request = build_overview_context(snapshot, fingerprint)

  assert request.section_id == "overview"
  assert "Full-stack web application" in request.context_summary
  assert "backend/main.py" in request.evidence_files
  assert len(request.capped_snippets) > 0


def test_build_component_context():
  """Test building component context."""
  snapshot = RepositorySnapshot(
    source_name="test-repo",
    files=[
      FileInfo(
        path="backend/routes/trips.py",
        name="trips.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="backend_route",
        text_preview="@app.get('/trips')\ndef list_trips():\n  pass",
        line_count=10,
      )
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  card = ComponentCard(
    path="backend/routes/trips.py",
    title="Trip Routes",
    role="backend_route",
    why_it_matters="Handles trip API endpoints",
    connected_to=["backend/services/recommendations.py"],
    detected_items=["GET /trips"],
    suggested_test_ideas=["Test valid trip search"],
    suggested_bob_prompt="Explain backend/routes/trips.py",
  )

  request = build_component_context(card, snapshot)

  assert request.section_id == "component_backend/routes/trips.py"
  assert "backend/routes/trips.py" in request.evidence_files
  assert "Trip Routes" in request.section_title

# Made with Bob
