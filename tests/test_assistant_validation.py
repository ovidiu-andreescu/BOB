"""Tests for AI assistant validation and trust gates."""


from repoquest.assistant_models import (
    AssistantResponse,
    CodeRecommendation,
)
from repoquest.assistant_validation import (
    detect_secrets,
    format_doc_page_validation,
    format_recommendation_validation,
    format_validation_message,
    validate_assistant_response,
    validate_code_recommendation,
    validate_confidence,
    validate_generated_doc_page,
)
from repoquest.eval_metrics import (
    EvalMetrics,
    track_doc_page_validation,
    track_recommendation_validation,
    track_response_validation,
)
from tests.fixtures.eval_fixtures import (
    create_doc_page_missing_sources,
    create_doc_page_with_hallucinated_files,
    create_doc_page_with_secrets,
    create_empty_response,
    create_local_model_verbose_response,
    create_recommendation_low_confidence,
    create_recommendation_missing_evidence,
    create_recommendation_with_hallucinated_files,
    create_recommendation_with_secrets,
    create_response_claiming_test_execution,
    create_response_instructing_code_execution,
    create_response_missing_metadata,
    create_response_with_hallucinated_files,
    create_response_with_multiple_violations,
    create_response_with_secrets,
    create_test_snapshot,
    create_valid_doc_page,
    create_valid_recommendation,
    create_valid_response,
)


class TestSecretDetection:
    """Test secret detection patterns."""

    def test_detect_api_key(self):
        """Test detection of API keys."""
        text = "api_key = 'sk-1234567890abcdefghijklmnop'"
        secrets = detect_secrets(text)
        assert len(secrets) > 0
        assert any("key" in s.lower() for s in secrets)

    def test_detect_password(self):
        """Test detection of passwords."""
        text = "password='MySecretPass123'"
        secrets = detect_secrets(text)
        assert len(secrets) > 0
        assert any("password" in s.lower() for s in secrets)

    def test_detect_token(self):
        """Test detection of tokens."""
        text = "token: 'ghp_1234567890abcdefghijklmnopqrstuvwxyz'"
        secrets = detect_secrets(text)
        assert len(secrets) > 0

    def test_no_secrets_in_clean_text(self):
        """Test that clean text has no secrets."""
        text = "This is a normal description of the API endpoint."
        secrets = detect_secrets(text)
        assert len(secrets) == 0

    def test_detect_aws_key(self):
        """Test detection of AWS keys."""
        text = "aws_access_key='AKIAIOSFODNN7EXAMPLE'"
        secrets = detect_secrets(text)
        assert len(secrets) > 0


class TestConfidenceValidation:
    """Test confidence score validation."""

    def test_valid_confidence(self):
        """Test valid confidence scores."""
        is_valid, error = validate_confidence(0.5)
        assert is_valid
        assert error is None

    def test_confidence_zero(self):
        """Test confidence of 0.0."""
        is_valid, error = validate_confidence(0.0)
        assert is_valid
        assert error is None

    def test_confidence_one(self):
        """Test confidence of 1.0."""
        is_valid, error = validate_confidence(1.0)
        assert is_valid
        assert error is None

    def test_confidence_negative(self):
        """Test negative confidence."""
        is_valid, error = validate_confidence(-0.1)
        assert not is_valid
        assert "outside valid range" in error

    def test_confidence_above_one(self):
        """Test confidence above 1.0."""
        is_valid, error = validate_confidence(1.5)
        assert not is_valid
        assert "outside valid range" in error

    def test_confidence_not_number(self):
        """Test non-numeric confidence."""
        is_valid, error = validate_confidence("high")  # type: ignore
        assert not is_valid
        assert "must be a number" in error


class TestAssistantResponseValidation:
    """Test assistant response validation."""

    def test_valid_response_passes(self):
        """Test that a valid response passes validation."""
        response = create_valid_response()
        snapshot = create_test_snapshot()

        validated = validate_assistant_response(response, snapshot)

        assert validated.status == "ok"
        assert validated.response_text == response.response_text

    def test_empty_response_fails(self):
        """Test that empty response fails validation."""
        response = create_empty_response()

        validated = validate_assistant_response(response)

        assert validated.status == "invalid"
        assert "Empty response" in validated.message

    def test_missing_provider_metadata_fails(self):
        """Test that missing provider metadata fails validation."""
        response = create_response_missing_metadata()

        validated = validate_assistant_response(response)

        assert validated.status == "invalid"
        assert "Missing provider metadata" in validated.message or "Missing model metadata" in validated.message

    def test_hallucinated_files_fail(self):
        """Test that hallucinated file citations fail validation."""
        response = create_response_with_hallucinated_files()
        snapshot = create_test_snapshot()

        validated = validate_assistant_response(response, snapshot)

        assert validated.status == "invalid"
        assert "Cited files not in snapshot" in validated.message

    def test_test_execution_claim_fails(self):
        """Test that claiming test execution fails validation."""
        response = create_response_claiming_test_execution()

        validated = validate_assistant_response(response)

        assert validated.status == "invalid"
        assert "test execution" in validated.message.lower()

    def test_code_execution_instruction_fails(self):
        """Test that instructing code execution fails validation."""
        response = create_response_instructing_code_execution()

        validated = validate_assistant_response(response)

        assert validated.status == "invalid"
        assert "code execution" in validated.message.lower()

    def test_secrets_in_response_fail(self):
        """Test that secrets in response fail validation."""
        response = create_response_with_secrets()

        validated = validate_assistant_response(response)

        assert validated.status == "invalid"
        assert "secrets" in validated.message.lower()
        assert "[REDACTED" in validated.response_text

    def test_multiple_violations_detected(self):
        """Test that multiple violations are detected."""
        response = create_response_with_multiple_violations()
        snapshot = create_test_snapshot()

        validated = validate_assistant_response(response, snapshot)

        assert validated.status == "invalid"
        # Should catch at least one violation
        assert validated.message is not None

    def test_error_response_not_validated(self):
        """Test that error responses are not validated."""
        response = AssistantResponse(
            status="error",
            response_text="",
            provider="mock",
            model="test",
            message="Provider error",
        )

        validated = validate_assistant_response(response)

        assert validated.status == "error"
        assert validated.message == "Provider error"

    def test_disabled_response_not_validated(self):
        """Test that disabled responses are not validated."""
        response = AssistantResponse(
            status="disabled",
            response_text="",
            provider="mock",
            model="test",
            message="Assistant disabled",
        )

        validated = validate_assistant_response(response)

        assert validated.status == "disabled"

    def test_local_model_verbose_response(self):
        """Test validation of verbose local model response."""
        response = create_local_model_verbose_response()

        validated = validate_assistant_response(response)

        # Should pass basic validation even without citations
        assert validated.status == "ok"


class TestCodeRecommendationValidation:
    """Test code recommendation validation."""

    def test_valid_recommendation_passes(self):
        """Test that a valid recommendation passes validation."""
        recommendation = create_valid_recommendation()
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status == "valid"
        assert len(validated.validation_warnings) == 0

    def test_missing_evidence_downgraded(self):
        """Test that missing evidence downgrades recommendation."""
        recommendation = create_recommendation_missing_evidence()
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status in {"invalid", "downgraded"}
        assert any("evidence" in w.lower() for w in validated.validation_warnings)

    def test_hallucinated_files_invalid(self):
        """Test that hallucinated files make recommendation invalid."""
        recommendation = create_recommendation_with_hallucinated_files()
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status == "invalid"
        assert any("not in snapshot" in w for w in validated.validation_warnings)

    def test_low_confidence_downgraded(self):
        """Test that low confidence downgrades recommendation."""
        recommendation = create_recommendation_low_confidence()
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status in {"downgraded", "invalid"}
        assert any("confidence" in w.lower() for w in validated.validation_warnings)

    def test_secrets_in_recommendation_invalid(self):
        """Test that secrets make recommendation invalid."""
        recommendation = create_recommendation_with_secrets()
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status == "invalid"
        assert any("secrets" in w.lower() for w in validated.validation_warnings)

    def test_missing_required_fields(self):
        """Test that missing required fields are detected."""
        recommendation = CodeRecommendation(
            title="",  # Missing
            category="api",
            priority="high",
            files=["backend/main.py"],
            evidence=["backend/main.py"],
            rationale="",  # Missing
            proposed_change_summary="",  # Missing
            test_plan=[],
            workflow="",
            confidence=0.8,
        )
        snapshot = create_test_snapshot()

        validated = validate_code_recommendation(recommendation, snapshot)

        assert validated.validation_status in {"invalid", "downgraded"}
        assert len(validated.validation_warnings) > 0


class TestGeneratedDocPageValidation:
    """Test generated documentation page validation."""

    def test_valid_doc_page_passes(self):
        """Test that a valid doc page passes validation."""
        doc_page = create_valid_doc_page()
        snapshot = create_test_snapshot()

        validated = validate_generated_doc_page(doc_page, snapshot)

        assert len(validated.warnings) == 0

    def test_missing_sources_detected(self):
        """Test that missing source files are detected."""
        doc_page = create_doc_page_missing_sources()
        snapshot = create_test_snapshot()

        validated = validate_generated_doc_page(doc_page, snapshot)

        assert len(validated.warnings) > 0
        assert any("source" in w.lower() for w in validated.warnings)

    def test_hallucinated_files_detected(self):
        """Test that hallucinated files are detected."""
        doc_page = create_doc_page_with_hallucinated_files()
        snapshot = create_test_snapshot()

        validated = validate_generated_doc_page(doc_page, snapshot)

        assert len(validated.warnings) > 0
        assert any("not in snapshot" in w for w in validated.warnings)

    def test_secrets_in_doc_page_detected(self):
        """Test that secrets in doc page are detected."""
        doc_page = create_doc_page_with_secrets()
        snapshot = create_test_snapshot()

        validated = validate_generated_doc_page(doc_page, snapshot)

        assert len(validated.warnings) > 0
        assert any("secrets" in w.lower() for w in validated.warnings)


class TestValidationMessageFormatting:
    """Test validation message formatting."""

    def test_format_valid_response(self):
        """Test formatting of valid response."""
        response = create_valid_response()
        message = format_validation_message(response)
        assert message == ""

    def test_format_disabled_response(self):
        """Test formatting of disabled response."""
        response = AssistantResponse(
            status="disabled",
            response_text="",
            provider="mock",
            model="test",
            message="Disabled",
        )
        message = format_validation_message(response)
        assert "disabled" in message.lower()

    def test_format_error_response(self):
        """Test formatting of error response."""
        response = AssistantResponse(
            status="error",
            response_text="",
            provider="claude",
            model="claude-3-sonnet",
            message="API error",
        )
        message = format_validation_message(response)
        assert "error" in message.lower()
        assert "claude" in message.lower()

    def test_format_invalid_response(self):
        """Test formatting of invalid response."""
        response = AssistantResponse(
            status="invalid",
            response_text="",
            provider="mock",
            model="test",
            message="Validation failed: Empty response",
        )
        message = format_validation_message(response)
        assert "validation failed" in message.lower()

    def test_format_valid_recommendation(self):
        """Test formatting of valid recommendation."""
        recommendation = create_valid_recommendation()
        snapshot = create_test_snapshot()
        validated = validate_code_recommendation(recommendation, snapshot)

        message = format_recommendation_validation(validated)
        assert "validated" in message.lower()

    def test_format_invalid_recommendation(self):
        """Test formatting of invalid recommendation."""
        recommendation = create_recommendation_with_hallucinated_files()
        snapshot = create_test_snapshot()
        validated = validate_code_recommendation(recommendation, snapshot)

        message = format_recommendation_validation(validated)
        assert "invalid" in message.lower()

    def test_format_valid_doc_page(self):
        """Test formatting of valid doc page."""
        doc_page = create_valid_doc_page()
        snapshot = create_test_snapshot()
        validated = validate_generated_doc_page(doc_page, snapshot)

        message = format_doc_page_validation(validated)
        assert "validated" in message.lower()

    def test_format_invalid_doc_page(self):
        """Test formatting of invalid doc page."""
        doc_page = create_doc_page_with_hallucinated_files()
        snapshot = create_test_snapshot()
        validated = validate_generated_doc_page(doc_page, snapshot)

        message = format_doc_page_validation(validated)
        assert "invalid" in message.lower() or "warning" in message.lower()


class TestEvalMetrics:
    """Test evaluation metrics tracking."""

    def test_track_valid_response(self):
        """Test tracking of valid response."""
        metrics = EvalMetrics()
        response = create_valid_response()

        track_response_validation(response, metrics.validation)

        assert metrics.validation.total_responses == 1
        assert metrics.validation.valid_responses == 1
        assert metrics.validation.schema_validity_rate == 1.0

    def test_track_invalid_response(self):
        """Test tracking of invalid response."""
        metrics = EvalMetrics()
        response = create_empty_response()
        validated = validate_assistant_response(response)

        track_response_validation(validated, metrics.validation)

        assert metrics.validation.total_responses == 1
        assert metrics.validation.invalid_responses == 1
        assert metrics.validation.empty_response_count == 1

    def test_track_hallucinated_files(self):
        """Test tracking of hallucinated files."""
        metrics = EvalMetrics()
        response = create_response_with_hallucinated_files()
        snapshot = create_test_snapshot()
        validated = validate_assistant_response(response, snapshot)

        track_response_validation(validated, metrics.validation)

        assert metrics.validation.hallucinated_file_count == 1

    def test_track_test_execution_claim(self):
        """Test tracking of test execution claims."""
        metrics = EvalMetrics()
        response = create_response_claiming_test_execution()
        validated = validate_assistant_response(response)

        track_response_validation(validated, metrics.validation)

        assert metrics.validation.test_execution_claim_count == 1

    def test_track_secrets(self):
        """Test tracking of secret detection."""
        metrics = EvalMetrics()
        response = create_response_with_secrets()
        validated = validate_assistant_response(response)

        track_response_validation(validated, metrics.validation)

        assert metrics.validation.secret_detection_count == 1

    def test_track_valid_recommendation(self):
        """Test tracking of valid recommendation."""
        metrics = EvalMetrics()
        recommendation = create_valid_recommendation()
        snapshot = create_test_snapshot()
        validated = validate_code_recommendation(recommendation, snapshot)

        track_recommendation_validation(validated, metrics.recommendations)

        assert metrics.recommendations.total_recommendations == 1
        assert metrics.recommendations.valid_recommendations == 1

    def test_track_recommendation_missing_evidence(self):
        """Test tracking of recommendation missing evidence."""
        metrics = EvalMetrics()
        recommendation = create_recommendation_missing_evidence()
        snapshot = create_test_snapshot()
        validated = validate_code_recommendation(recommendation, snapshot)

        track_recommendation_validation(validated, metrics.recommendations)

        assert metrics.recommendations.missing_evidence_count == 1

    def test_track_valid_doc_page(self):
        """Test tracking of valid doc page."""
        metrics = EvalMetrics()
        doc_page = create_valid_doc_page()
        snapshot = create_test_snapshot()
        validated = validate_generated_doc_page(doc_page, snapshot)

        track_doc_page_validation(validated, metrics.doc_pages)

        assert metrics.doc_pages.total_pages == 1
        assert metrics.doc_pages.valid_pages == 1

    def test_metrics_serialization(self):
        """Test that metrics can be serialized to dict."""
        metrics = EvalMetrics()
        response = create_valid_response()
        track_response_validation(response, metrics.validation)

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert "validation" in metrics_dict
        assert "recommendations" in metrics_dict
        assert "doc_pages" in metrics_dict


# Made with Bob
