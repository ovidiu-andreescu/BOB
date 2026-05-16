"""Validation for AI assistant responses with comprehensive trust gates."""

import re

from repoquest.assistant_models import (
    AssistantResponse,
    CodeRecommendation,
    GeneratedDocPage,
)
from repoquest.models import RepositorySnapshot


# Secret detection patterns
SECRET_PATTERNS = [
    (r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})", "API key"),
    (r"(?i)secret[_-]?key['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})", "Secret key"),
    (r"(?i)password['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})", "Password"),
    (r"(?i)token['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})", "Token"),
    (r"(?i)aws[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"]?([A-Z0-9]{20})", "AWS key"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI key"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub token"),
]


def detect_secrets(text: str) -> list[str]:
    """Detect potential secrets in text. Returns list of secret types found."""
    found_secrets = []
    for pattern, secret_type in SECRET_PATTERNS:
        if re.search(pattern, text):
            found_secrets.append(secret_type)
    return found_secrets


def validate_confidence(confidence: float) -> tuple[bool, str | None]:
    """
    Validate confidence score.
    
    Returns (is_valid, error_message).
    """
    if not isinstance(confidence, (int, float)):
        return False, "Confidence must be a number"
    
    if confidence < 0.0 or confidence > 1.0:
        return False, f"Confidence {confidence} outside valid range [0.0, 1.0]"
    
    return True, None


def validate_assistant_response(
    response: AssistantResponse,
    snapshot: RepositorySnapshot | None = None,
) -> AssistantResponse:
    """
    Validate an assistant response and return a modified response if validation fails.

    Checks:
    1. Response is not empty
    2. Provider and model metadata present
    3. Cited file paths exist in snapshot (if snapshot provided)
    4. Response does not claim tests were executed
    5. Response does not instruct code execution
    6. Response does not contain secrets

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

    # Check 2: Provider and model metadata
    if not response.provider or response.provider == "unknown":
        return AssistantResponse(
            status="invalid",
            response_text=response.response_text,
            citations=response.citations,
            provider=response.provider,
            model=response.model,
            message="Validation failed: Missing provider metadata",
        )

    if not response.model or response.model == "unknown":
        return AssistantResponse(
            status="invalid",
            response_text=response.response_text,
            citations=response.citations,
            provider=response.provider,
            model=response.model,
            message="Validation failed: Missing model metadata",
        )

    # Check 3: Cited paths exist in snapshot
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

    # Check 4: No claims of test execution
    forbidden_phrases = [
        "tests passed",
        "tests failed",
        "ran the tests",
        "executed the tests",
        "running the tests",
        "test execution",
        "all tests pass",
        "i ran",
        "i executed",
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

    # Check 5: No instructions to execute code
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

    # Check 6: No secrets in response
    found_secrets = detect_secrets(response.response_text)
    if found_secrets:
        return AssistantResponse(
            status="invalid",
            response_text="[REDACTED: Response contained potential secrets]",
            citations=response.citations,
            provider=response.provider,
            model=response.model,
            message=f"Validation failed: Response contains potential secrets ({', '.join(found_secrets[:2])})",
        )

    # All checks passed
    return response


def validate_code_recommendation(
    recommendation: CodeRecommendation,
    snapshot: RepositorySnapshot | None = None,
) -> CodeRecommendation:
    """
    Validate a code recommendation.
    
    Checks:
    1. Required fields are present
    2. Confidence is in valid range
    3. Files exist in snapshot (if provided)
    4. Evidence is provided
    5. No secrets in content
    
    Returns recommendation with updated validation_status and validation_warnings.
    """
    warnings = []
    
    # Check 1: Required fields
    if not recommendation.title:
        warnings.append("Missing title")
    
    if not recommendation.rationale:
        warnings.append("Missing rationale")
    
    if not recommendation.proposed_change_summary:
        warnings.append("Missing proposed change summary")
    
    # Check 2: Confidence validation
    is_valid_conf, conf_error = validate_confidence(recommendation.confidence)
    if not is_valid_conf:
        warnings.append(f"Invalid confidence: {conf_error}")
    elif recommendation.confidence < 0.3:
        warnings.append(f"Low confidence ({recommendation.confidence:.2f})")
    
    # Check 3: Files exist in snapshot
    if snapshot and recommendation.files:
        snapshot_paths = {f.path for f in snapshot.files}
        missing_files = [f for f in recommendation.files if f not in snapshot_paths]
        if missing_files:
            warnings.append(f"Referenced files not in snapshot: {', '.join(missing_files[:3])}")
    
    # Check 4: Evidence provided
    if not recommendation.evidence:
        warnings.append("No evidence provided")
    elif snapshot:
        # Check if evidence files exist
        snapshot_paths = {f.path for f in snapshot.files}
        missing_evidence = [e for e in recommendation.evidence if e not in snapshot_paths]
        if missing_evidence:
            warnings.append(f"Evidence files not in snapshot: {', '.join(missing_evidence[:3])}")
    
    # Check 5: No secrets
    combined_text = f"{recommendation.rationale} {recommendation.proposed_change_summary} {recommendation.workflow}"
    found_secrets = detect_secrets(combined_text)
    if found_secrets:
        warnings.append(f"Contains potential secrets: {', '.join(found_secrets[:2])}")
    
    # Determine validation status
    if not warnings:
        validation_status = "valid"
    elif any("not in snapshot" in w or "Missing" in w for w in warnings):
        validation_status = "invalid"
    elif any("secrets" in w.lower() for w in warnings):
        validation_status = "invalid"
    else:
        validation_status = "downgraded"
    
    return CodeRecommendation(
        title=recommendation.title,
        category=recommendation.category,
        priority=recommendation.priority,
        files=recommendation.files,
        evidence=recommendation.evidence,
        rationale=recommendation.rationale,
        proposed_change_summary=recommendation.proposed_change_summary,
        test_plan=recommendation.test_plan,
        workflow=recommendation.workflow,
        confidence=recommendation.confidence,
        validation_status=validation_status,
        validation_warnings=warnings,
    )


def validate_generated_doc_page(
    doc_page: GeneratedDocPage,
    snapshot: RepositorySnapshot | None = None,
) -> GeneratedDocPage:
    """
    Validate a generated documentation page.
    
    Checks:
    1. Required fields are present
    2. Source files exist in snapshot (if provided)
    3. Evidence files exist in snapshot (if provided)
    4. No secrets in content
    
    Returns doc page with updated warnings.
    """
    warnings = list(doc_page.warnings)
    
    # Check 1: Required fields
    if not doc_page.title:
        warnings.append("Missing title")
    
    if not doc_page.content:
        warnings.append("Missing content")
    
    if not doc_page.source_files:
        warnings.append("No source files specified")
    
    # Check 2: Source files exist
    if snapshot and doc_page.source_files:
        snapshot_paths = {f.path for f in snapshot.files}
        missing_sources = [f for f in doc_page.source_files if f not in snapshot_paths]
        if missing_sources:
            warnings.append(f"Source files not in snapshot: {', '.join(missing_sources[:3])}")
    
    # Check 3: Evidence files exist
    if snapshot and doc_page.evidence:
        snapshot_paths = {f.path for f in snapshot.files}
        missing_evidence = [e for e in doc_page.evidence if e not in snapshot_paths]
        if missing_evidence:
            warnings.append(f"Evidence files not in snapshot: {', '.join(missing_evidence[:3])}")
    
    # Check 4: No secrets
    found_secrets = detect_secrets(doc_page.content)
    if found_secrets:
        warnings.append(f"Contains potential secrets: {', '.join(found_secrets[:2])}")
    
    return GeneratedDocPage(
        title=doc_page.title,
        category=doc_page.category,
        source_files=doc_page.source_files,
        content=doc_page.content,
        evidence=doc_page.evidence,
        related_components=doc_page.related_components,
        warnings=warnings,
    )


def format_validation_message(response: AssistantResponse) -> str:
    """Format a validation message for display."""
    if response.status == "disabled":
        return "⚠️ AI Assistant is disabled. Enable it in settings to use AI features."

    if response.status == "error":
        provider_label = f" ({response.provider}/{response.model})" if response.provider != "unknown" else ""
        return f"❌ AI Assistant error{provider_label}: {response.message}"

    if response.status == "invalid":
        provider_label = f" ({response.provider}/{response.model})" if response.provider != "unknown" else ""
        return f"⚠️ Validation failed{provider_label}: {response.message}"

    return ""


def format_recommendation_validation(recommendation: CodeRecommendation) -> str:
    """Format validation status for a code recommendation."""
    if recommendation.validation_status == "valid":
        return "✅ Validated"
    
    if recommendation.validation_status == "invalid":
        warnings_text = "; ".join(recommendation.validation_warnings[:2])
        return f"❌ Invalid: {warnings_text}"
    
    if recommendation.validation_status == "downgraded":
        warnings_text = "; ".join(recommendation.validation_warnings[:2])
        return f"⚠️ Downgraded: {warnings_text}"
    
    return "⏳ Pending validation"


def format_doc_page_validation(doc_page: GeneratedDocPage) -> str:
    """Format validation status for a generated doc page."""
    if not doc_page.warnings:
        return "✅ Validated"
    
    critical_warnings = [w for w in doc_page.warnings if "not in snapshot" in w or "secrets" in w.lower()]
    if critical_warnings:
        return f"❌ Invalid: {critical_warnings[0]}"
    
    return f"⚠️ {len(doc_page.warnings)} warning(s)"


# Made with Bob
