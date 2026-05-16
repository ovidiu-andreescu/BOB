"""Validation for AI assistant responses."""

from repoquest.assistant_models import AssistantResponse
from repoquest.models import RepositorySnapshot


def validate_assistant_response(
  response: AssistantResponse,
  snapshot: RepositorySnapshot | None = None,
) -> AssistantResponse:
  """
  Validate an assistant response and return a modified response if validation fails.

  Checks:
  1. Response is not empty
  2. Cited file paths exist in snapshot (if snapshot provided)
  3. Response does not claim tests were executed
  4. Response does not instruct code execution

  Returns the original response if valid, or a modified response with status="invalid"
  and a validation message if invalid.
  """
  if response.status != "ok":
    # Don't validate error/disabled responses
    return response

  # Check 1: Non-empty response
  if not response.response_text or not response.response_text.strip():
    return AssistantResponse(
      status="invalid",
      response_text="",
      citations=response.citations,
      provider=response.provider,
      model=response.model,
      message="Validation failed: Empty response from AI assistant",
    )

  # Check 2: Cited paths exist in snapshot
  if snapshot and response.citations:
    snapshot_paths = {f.path for f in snapshot.files}
    invalid_citations = []

    for citation in response.citations:
      if citation.file_path not in snapshot_paths:
        invalid_citations.append(citation.file_path)

    if invalid_citations:
      return AssistantResponse(
        status="invalid",
        response_text=response.response_text,
        citations=response.citations,
        provider=response.provider,
        model=response.model,
        message=f"Validation failed: Cited files not in snapshot: {', '.join(invalid_citations[:3])}",
      )

  # Check 3: No claims of test execution
  forbidden_phrases = [
    "tests passed",
    "tests failed",
    "ran the tests",
    "executed the tests",
    "running the tests",
    "test execution",
    "all tests pass",
  ]

  response_lower = response.response_text.lower()
  found_forbidden = []

  for phrase in forbidden_phrases:
    if phrase in response_lower:
      found_forbidden.append(phrase)

  if found_forbidden:
    return AssistantResponse(
      status="invalid",
      response_text=response.response_text,
      citations=response.citations,
      provider=response.provider,
      model=response.model,
      message=f"Validation failed: Response claims test execution ('{found_forbidden[0]}'). RepoQuest performs static analysis only.",
    )

  # Check 4: No instructions to execute code
  execution_phrases = [
    "run this code",
    "execute this",
    "install dependencies",
    "npm install",
    "pip install",
    "run the script",
    "execute the script",
  ]

  found_execution = []

  for phrase in execution_phrases:
    if phrase in response_lower:
      found_execution.append(phrase)

  if found_execution:
    return AssistantResponse(
      status="invalid",
      response_text=response.response_text,
      citations=response.citations,
      provider=response.provider,
      model=response.model,
      message=f"Validation failed: Response instructs code execution ('{found_execution[0]}'). RepoQuest does not execute uploaded code.",
    )

  # All checks passed
  return response


def format_validation_message(response: AssistantResponse) -> str:
  """Format a validation message for display."""
  if response.status == "disabled":
    return "Warning: AI Assistant is disabled. Enable it in settings to use AI features."

  if response.status == "error":
    return f"AI Assistant error: {response.message}"

  if response.status == "invalid":
    return f"Warning: {response.message}"

  return ""

# Made with Bob
