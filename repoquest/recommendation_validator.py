"""Validation logic for AI-generated code recommendations."""

from repoquest.assistant_models import CodeRecommendation
from repoquest.models import RepositorySnapshot


VALID_CATEGORIES = {
    "testing",
    "documentation",
    "api",
    "frontend",
    "backend",
    "data_model",
    "error_handling",
    "refactor",
    "developer_experience",
    "unknown",
}

VALID_PRIORITIES = {"high", "medium", "low"}


def validate_recommendation(
    recommendation: CodeRecommendation,
    snapshot: RepositorySnapshot,
) -> CodeRecommendation:
    """
    Validate an AI-generated recommendation against repository evidence.

    Args:
        recommendation: The recommendation to validate
        snapshot: Repository snapshot for evidence checking

    Returns:
        Updated recommendation with validation status and warnings
    """
    warnings = []
    
    # Build set of valid file paths from snapshot
    valid_files = {file_info.path for file_info in snapshot.files}
    
    # Validate category
    if recommendation.category not in VALID_CATEGORIES:
        warnings.append(f"Invalid category '{recommendation.category}', normalized to 'unknown'")
        recommendation.category = "unknown"
    
    # Validate priority
    if recommendation.priority not in VALID_PRIORITIES:
        warnings.append(f"Invalid priority '{recommendation.priority}', normalized to 'low'")
        recommendation.priority = "low"
    
    # Validate confidence range
    if not (0.0 <= recommendation.confidence <= 1.0):
        warnings.append(f"Confidence {recommendation.confidence} out of range [0.0, 1.0], clamped")
        recommendation.confidence = max(0.0, min(1.0, recommendation.confidence))
    
    # Validate required fields
    if not recommendation.title:
        warnings.append("Missing title")
        recommendation.validation_status = "invalid"
        recommendation.validation_warnings = warnings
        return recommendation
    
    if not recommendation.rationale:
        warnings.append("Missing rationale")
        recommendation.validation_status = "invalid"
        recommendation.validation_warnings = warnings
        return recommendation
    
    if not recommendation.proposed_change_summary:
        warnings.append("Missing proposed change summary")
        recommendation.validation_status = "invalid"
        recommendation.validation_warnings = warnings
        return recommendation
    
    # Validate files exist in snapshot
    invalid_files = []
    for file_path in recommendation.files:
        if file_path not in valid_files:
            invalid_files.append(file_path)
    
    if invalid_files:
        warnings.append(f"Referenced {len(invalid_files)} nonexistent files: {', '.join(invalid_files[:3])}")
        # Remove invalid files
        recommendation.files = [f for f in recommendation.files if f in valid_files]
    
    # Validate evidence references
    invalid_evidence = []
    for evidence_item in recommendation.evidence:
        # Check if evidence references a file path
        if "/" in evidence_item or "\\" in evidence_item:
            # Extract potential file path
            parts = evidence_item.split()
            for part in parts:
                if "/" in part or "\\" in part:
                    # Clean up common prefixes/suffixes
                    clean_part = part.strip("'\"`:,")
                    if clean_part and clean_part not in valid_files:
                        invalid_evidence.append(clean_part)
    
    if invalid_evidence:
        warnings.append(f"Evidence references {len(invalid_evidence)} nonexistent files")
    
    # Check for evidence
    if not recommendation.evidence:
        warnings.append("No evidence provided")
        recommendation.validation_status = "downgraded"
        recommendation.validation_warnings = warnings
        return recommendation
    
    # Check for files
    if not recommendation.files:
        warnings.append("No files specified")
        recommendation.validation_status = "downgraded"
        recommendation.validation_warnings = warnings
        return recommendation
    
    # Determine final validation status
    if warnings:
        if any("Missing" in w or "nonexistent files" in w for w in warnings):
            recommendation.validation_status = "downgraded"
        else:
            recommendation.validation_status = "valid"
    else:
        recommendation.validation_status = "valid"
    
    recommendation.validation_warnings = warnings
    return recommendation


def validate_recommendations(
    recommendations: list[CodeRecommendation],
    snapshot: RepositorySnapshot,
) -> list[CodeRecommendation]:
    """
    Validate a list of recommendations.

    Args:
        recommendations: List of recommendations to validate
        snapshot: Repository snapshot for evidence checking

    Returns:
        List of validated recommendations
    """
    return [validate_recommendation(rec, snapshot) for rec in recommendations]


def filter_trusted_recommendations(
    recommendations: list[CodeRecommendation],
) -> list[CodeRecommendation]:
    """
    Filter recommendations to only those that are trusted (valid or downgraded).

    Args:
        recommendations: List of recommendations

    Returns:
        List of trusted recommendations
    """
    return [r for r in recommendations if r.is_trusted]


def group_recommendations_by_category(
    recommendations: list[CodeRecommendation],
) -> dict[str, list[CodeRecommendation]]:
    """
    Group recommendations by category.

    Args:
        recommendations: List of recommendations

    Returns:
        Dictionary mapping category to list of recommendations
    """
    grouped: dict[str, list[CodeRecommendation]] = {}
    for rec in recommendations:
        if rec.category not in grouped:
            grouped[rec.category] = []
        grouped[rec.category].append(rec)
    return grouped


def group_recommendations_by_priority(
    recommendations: list[CodeRecommendation],
) -> dict[str, list[CodeRecommendation]]:
    """
    Group recommendations by priority.

    Args:
        recommendations: List of recommendations

    Returns:
        Dictionary mapping priority to list of recommendations
    """
    grouped: dict[str, list[CodeRecommendation]] = {}
    for rec in recommendations:
        if rec.priority not in grouped:
            grouped[rec.priority] = []
        grouped[rec.priority].append(rec)
    return grouped


def sort_recommendations_by_priority(
    recommendations: list[CodeRecommendation],
) -> list[CodeRecommendation]:
    """
    Sort recommendations by priority (high -> medium -> low).

    Args:
        recommendations: List of recommendations

    Returns:
        Sorted list of recommendations
    """
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        recommendations,
        key=lambda r: (priority_order.get(r.priority, 3), -r.confidence)
    )
