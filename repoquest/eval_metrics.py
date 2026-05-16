"""Lightweight evaluation metrics for AI assistant trust gates."""

from dataclasses import dataclass, field

from repoquest.assistant_models import (
    AIRecommendationResult,
    AssistantResponse,
    CodeRecommendation,
    GeneratedDocPage,
)


@dataclass
class ValidationMetrics:
    """Metrics for validation results."""

    total_responses: int = 0
    valid_responses: int = 0
    invalid_responses: int = 0
    error_responses: int = 0
    disabled_responses: int = 0

    empty_response_count: int = 0
    missing_metadata_count: int = 0
    hallucinated_file_count: int = 0
    test_execution_claim_count: int = 0
    code_execution_instruction_count: int = 0
    secret_detection_count: int = 0

    @property
    def schema_validity_rate(self) -> float:
        """Percentage of responses that passed schema validation."""
        if self.total_responses == 0:
            return 0.0
        return self.valid_responses / self.total_responses

    @property
    def error_rate(self) -> float:
        """Percentage of responses that had errors."""
        if self.total_responses == 0:
            return 0.0
        return (self.invalid_responses + self.error_responses) / self.total_responses

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "total_responses": self.total_responses,
            "valid_responses": self.valid_responses,
            "invalid_responses": self.invalid_responses,
            "error_responses": self.error_responses,
            "disabled_responses": self.disabled_responses,
            "empty_response_count": self.empty_response_count,
            "missing_metadata_count": self.missing_metadata_count,
            "hallucinated_file_count": self.hallucinated_file_count,
            "test_execution_claim_count": self.test_execution_claim_count,
            "code_execution_instruction_count": self.code_execution_instruction_count,
            "secret_detection_count": self.secret_detection_count,
            "schema_validity_rate": self.schema_validity_rate,
            "error_rate": self.error_rate,
        }


@dataclass
class RecommendationMetrics:
    """Metrics for code recommendation validation."""

    total_recommendations: int = 0
    valid_recommendations: int = 0
    invalid_recommendations: int = 0
    downgraded_recommendations: int = 0

    missing_evidence_count: int = 0
    hallucinated_file_count: int = 0
    low_confidence_count: int = 0
    secret_detection_count: int = 0

    @property
    def evidence_coverage_rate(self) -> float:
        """Percentage of recommendations with evidence."""
        if self.total_recommendations == 0:
            return 0.0
        return (
            self.total_recommendations - self.missing_evidence_count
        ) / self.total_recommendations

    @property
    def trust_rate(self) -> float:
        """Percentage of recommendations that are valid or downgraded."""
        if self.total_recommendations == 0:
            return 0.0
        return (
            self.valid_recommendations + self.downgraded_recommendations
        ) / self.total_recommendations

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "total_recommendations": self.total_recommendations,
            "valid_recommendations": self.valid_recommendations,
            "invalid_recommendations": self.invalid_recommendations,
            "downgraded_recommendations": self.downgraded_recommendations,
            "missing_evidence_count": self.missing_evidence_count,
            "hallucinated_file_count": self.hallucinated_file_count,
            "low_confidence_count": self.low_confidence_count,
            "secret_detection_count": self.secret_detection_count,
            "evidence_coverage_rate": self.evidence_coverage_rate,
            "trust_rate": self.trust_rate,
        }


@dataclass
class DocPageMetrics:
    """Metrics for generated documentation page validation."""

    total_pages: int = 0
    valid_pages: int = 0
    pages_with_warnings: int = 0

    missing_source_files_count: int = 0
    hallucinated_file_count: int = 0
    secret_detection_count: int = 0

    @property
    def validity_rate(self) -> float:
        """Percentage of pages without critical warnings."""
        if self.total_pages == 0:
            return 0.0
        return self.valid_pages / self.total_pages

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "total_pages": self.total_pages,
            "valid_pages": self.valid_pages,
            "pages_with_warnings": self.pages_with_warnings,
            "missing_source_files_count": self.missing_source_files_count,
            "hallucinated_file_count": self.hallucinated_file_count,
            "secret_detection_count": self.secret_detection_count,
            "validity_rate": self.validity_rate,
        }


@dataclass
class EvalMetrics:
    """Combined evaluation metrics for AI assistant."""

    validation: ValidationMetrics = field(default_factory=ValidationMetrics)
    recommendations: RecommendationMetrics = field(default_factory=RecommendationMetrics)
    doc_pages: DocPageMetrics = field(default_factory=DocPageMetrics)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "validation": self.validation.to_dict(),
            "recommendations": self.recommendations.to_dict(),
            "doc_pages": self.doc_pages.to_dict(),
        }


def track_response_validation(
    response: AssistantResponse, metrics: ValidationMetrics
) -> None:
    """Update metrics based on response validation."""
    metrics.total_responses += 1

    if response.status == "ok":
        metrics.valid_responses += 1
    elif response.status == "invalid":
        metrics.invalid_responses += 1

        # Track specific validation failures
        if response.message:
            msg_lower = response.message.lower()
            if "empty response" in msg_lower:
                metrics.empty_response_count += 1
            if "missing provider" in msg_lower or "missing model" in msg_lower:
                metrics.missing_metadata_count += 1
            if "cited files not in snapshot" in msg_lower:
                metrics.hallucinated_file_count += 1
            if "test execution" in msg_lower:
                metrics.test_execution_claim_count += 1
            if "code execution" in msg_lower:
                metrics.code_execution_instruction_count += 1
            if "secrets" in msg_lower:
                metrics.secret_detection_count += 1

    elif response.status == "error":
        metrics.error_responses += 1
    elif response.status == "disabled":
        metrics.disabled_responses += 1


def track_recommendation_validation(
    recommendation: CodeRecommendation, metrics: RecommendationMetrics
) -> None:
    """Update metrics based on recommendation validation."""
    metrics.total_recommendations += 1

    if recommendation.validation_status == "valid":
        metrics.valid_recommendations += 1
    elif recommendation.validation_status == "invalid":
        metrics.invalid_recommendations += 1
    elif recommendation.validation_status == "downgraded":
        metrics.downgraded_recommendations += 1

    # Track specific validation issues
    for warning in recommendation.validation_warnings:
        warning_lower = warning.lower()
        if "no evidence" in warning_lower:
            metrics.missing_evidence_count += 1
        if "not in snapshot" in warning_lower:
            metrics.hallucinated_file_count += 1
        if "low confidence" in warning_lower:
            metrics.low_confidence_count += 1
        if "secrets" in warning_lower:
            metrics.secret_detection_count += 1


def track_doc_page_validation(
    doc_page: GeneratedDocPage, metrics: DocPageMetrics
) -> None:
    """Update metrics based on doc page validation."""
    metrics.total_pages += 1

    has_critical_warnings = any(
        "not in snapshot" in w.lower() or "secrets" in w.lower()
        for w in doc_page.warnings
    )

    if not has_critical_warnings and not doc_page.warnings:
        metrics.valid_pages += 1
    elif doc_page.warnings:
        metrics.pages_with_warnings += 1

    # Track specific validation issues
    for warning in doc_page.warnings:
        warning_lower = warning.lower()
        if "source files not in snapshot" in warning_lower:
            metrics.missing_source_files_count += 1
        if "not in snapshot" in warning_lower:
            metrics.hallucinated_file_count += 1
        if "secrets" in warning_lower:
            metrics.secret_detection_count += 1


def compute_recommendation_result_metrics(
    result: AIRecommendationResult,
) -> RecommendationMetrics:
    """Compute metrics for an AI recommendation result."""
    metrics = RecommendationMetrics()

    for recommendation in result.recommendations:
        track_recommendation_validation(recommendation, metrics)

    return metrics


# Made with Bob
