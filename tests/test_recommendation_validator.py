"""Tests for recommendation validation."""

import pytest

from repoquest.assistant_models import CodeRecommendation
from repoquest.models import RepositorySnapshot, FileInfo
from repoquest.recommendation_validator import (
    validate_recommendation,
    validate_recommendations,
    filter_trusted_recommendations,
    group_recommendations_by_category,
    group_recommendations_by_priority,
    sort_recommendations_by_priority,
)


@pytest.fixture
def sample_snapshot():
    """Create a sample repository snapshot for testing."""
    return RepositorySnapshot(
        source_name="test_repo",
        files=[
            FileInfo(
                path="backend/routes/trips.py",
                name="trips.py",
                suffix=".py",
                size_bytes=1000,
                language="python",
                role="backend_route",
                text_preview="",
                line_count=50,
            ),
            FileInfo(
                path="backend/tests/test_trips.py",
                name="test_trips.py",
                suffix=".py",
                size_bytes=800,
                language="python",
                role="test",
                text_preview="",
                line_count=40,
            ),
            FileInfo(
                path="frontend/src/api.ts",
                name="api.ts",
                suffix=".ts",
                size_bytes=600,
                language="typescript",
                role="api_client",
                text_preview="",
                line_count=30,
            ),
        ],
        total_files_seen=3,
        total_files_scanned=3,
        warnings=[],
    )


def test_validate_valid_recommendation(sample_snapshot):
    """Test validation of a valid recommendation."""
    rec = CodeRecommendation(
        title="Add edge-case tests",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py", "backend/tests/test_trips.py"],
        evidence=["Route file exists", "Test file exists"],
        rationale="Tests are important",
        proposed_change_summary="Add more tests",
        test_plan=["Write tests", "Run tests"],
        workflow="Test workflow",
        confidence=0.85,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.validation_status == "valid"
    assert validated.is_valid
    assert validated.is_trusted
    assert len(validated.validation_warnings) == 0


def test_validate_recommendation_with_invalid_category(sample_snapshot):
    """Test validation normalizes invalid category."""
    rec = CodeRecommendation(
        title="Test",
        category="invalid_category",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.category == "unknown"
    assert "Invalid category" in validated.validation_warnings[0]


def test_validate_recommendation_with_invalid_priority(sample_snapshot):
    """Test validation normalizes invalid priority."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="critical",
        files=["backend/routes/trips.py"],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.priority == "low"
    assert "Invalid priority" in validated.validation_warnings[0]


def test_validate_recommendation_with_invalid_confidence(sample_snapshot):
    """Test validation clamps confidence to valid range."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=1.5,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.confidence == 1.0
    assert "Confidence" in validated.validation_warnings[0]


def test_validate_recommendation_missing_title(sample_snapshot):
    """Test validation rejects recommendation without title."""
    rec = CodeRecommendation(
        title="",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.validation_status == "invalid"
    assert not validated.is_valid
    assert "Missing title" in validated.validation_warnings[0]


def test_validate_recommendation_missing_rationale(sample_snapshot):
    """Test validation rejects recommendation without rationale."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=["Evidence"],
        rationale="",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.validation_status == "invalid"
    assert "Missing rationale" in validated.validation_warnings[0]


def test_validate_recommendation_with_nonexistent_files(sample_snapshot):
    """Test validation handles nonexistent files."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py", "nonexistent/file.py"],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert "nonexistent files" in validated.validation_warnings[0]
    assert "nonexistent/file.py" not in validated.files
    assert "backend/routes/trips.py" in validated.files


def test_validate_recommendation_no_evidence(sample_snapshot):
    """Test validation downgrades recommendation without evidence."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=[],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.validation_status == "downgraded"
    assert validated.is_trusted
    assert "No evidence" in validated.validation_warnings[0]


def test_validate_recommendation_no_files(sample_snapshot):
    """Test validation downgrades recommendation without files."""
    rec = CodeRecommendation(
        title="Test",
        category="testing",
        priority="high",
        files=[],
        evidence=["Evidence"],
        rationale="Rationale",
        proposed_change_summary="Summary",
        test_plan=["Plan"],
        workflow="Workflow",
        confidence=0.8,
    )
    
    validated = validate_recommendation(rec, sample_snapshot)
    
    assert validated.validation_status == "downgraded"
    assert "No files" in validated.validation_warnings[0]


def test_validate_recommendations_list(sample_snapshot):
    """Test validation of multiple recommendations."""
    recs = [
        CodeRecommendation(
            title="Valid rec",
            category="testing",
            priority="high",
            files=["backend/routes/trips.py"],
            evidence=["Evidence"],
            rationale="Rationale",
            proposed_change_summary="Summary",
            test_plan=["Plan"],
            workflow="Workflow",
            confidence=0.8,
        ),
        CodeRecommendation(
            title="",
            category="testing",
            priority="high",
            files=["backend/routes/trips.py"],
            evidence=["Evidence"],
            rationale="Rationale",
            proposed_change_summary="Summary",
            test_plan=["Plan"],
            workflow="Workflow",
            confidence=0.8,
        ),
    ]
    
    validated = validate_recommendations(recs, sample_snapshot)
    
    assert len(validated) == 2
    assert validated[0].is_valid
    assert not validated[1].is_valid


def test_filter_trusted_recommendations():
    """Test filtering trusted recommendations."""
    recs = [
        CodeRecommendation(
            title="Valid",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
            validation_status="valid",
        ),
        CodeRecommendation(
            title="Downgraded",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
            validation_status="downgraded",
        ),
        CodeRecommendation(
            title="Invalid",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
            validation_status="invalid",
        ),
    ]
    
    trusted = filter_trusted_recommendations(recs)
    
    assert len(trusted) == 2
    assert trusted[0].title == "Valid"
    assert trusted[1].title == "Downgraded"


def test_group_recommendations_by_category():
    """Test grouping recommendations by category."""
    recs = [
        CodeRecommendation(
            title="Test 1",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
        ),
        CodeRecommendation(
            title="Test 2",
            category="testing",
            priority="medium",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.7,
        ),
        CodeRecommendation(
            title="Doc 1",
            category="documentation",
            priority="low",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.6,
        ),
    ]
    
    grouped = group_recommendations_by_category(recs)
    
    assert len(grouped) == 2
    assert len(grouped["testing"]) == 2
    assert len(grouped["documentation"]) == 1


def test_group_recommendations_by_priority():
    """Test grouping recommendations by priority."""
    recs = [
        CodeRecommendation(
            title="High 1",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
        ),
        CodeRecommendation(
            title="Medium 1",
            category="testing",
            priority="medium",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.7,
        ),
        CodeRecommendation(
            title="High 2",
            category="documentation",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.9,
        ),
    ]
    
    grouped = group_recommendations_by_priority(recs)
    
    assert len(grouped) == 2
    assert len(grouped["high"]) == 2
    assert len(grouped["medium"]) == 1


def test_sort_recommendations_by_priority():
    """Test sorting recommendations by priority and confidence."""
    recs = [
        CodeRecommendation(
            title="Low",
            category="testing",
            priority="low",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.9,
        ),
        CodeRecommendation(
            title="High 1",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.7,
        ),
        CodeRecommendation(
            title="High 2",
            category="testing",
            priority="high",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.9,
        ),
        CodeRecommendation(
            title="Medium",
            category="testing",
            priority="medium",
            files=[],
            evidence=[],
            rationale="R",
            proposed_change_summary="S",
            test_plan=[],
            workflow="W",
            confidence=0.8,
        ),
    ]
    
    sorted_recs = sort_recommendations_by_priority(recs)
    
    assert sorted_recs[0].title == "High 2"  # High priority, highest confidence
    assert sorted_recs[1].title == "High 1"  # High priority, lower confidence
    assert sorted_recs[2].title == "Medium"
    assert sorted_recs[3].title == "Low"
