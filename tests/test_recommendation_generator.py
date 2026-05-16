"""Tests for AI recommendation generation."""

import pytest

from repoquest.assistant_models import ContextPack
from repoquest.models import (
    RepositorySnapshot,
    FileInfo,
    ProjectFingerprint,
    FrameworkFinding,
    RouteInfo,
    ComponentCard,
    WorkPlan,
    TaskSuggestion,
    AgentWorkflow,
    SuggestedMilestone,
)
from repoquest.recommendation_generator import (
    generate_mock_recommendations,
    create_recommendation_prompt,
    parse_ai_recommendations,
    generate_recommendation_summary,
)


@pytest.fixture
def sample_snapshot():
    """Create a sample repository snapshot."""
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
            FileInfo(
                path="backend/models/trip.py",
                name="trip.py",
                suffix=".py",
                size_bytes=400,
                language="python",
                role="model",
                text_preview="",
                line_count=20,
            ),
        ],
        total_files_seen=4,
        total_files_scanned=4,
        warnings=[],
    )


@pytest.fixture
def sample_fingerprint():
    """Create a sample project fingerprint."""
    return ProjectFingerprint(
        project_type="Full-stack web application",
        confidence=0.85,
        frameworks=[
            FrameworkFinding(
                name="FastAPI",
                category="backend",
                confidence=0.9,
                evidence=["from fastapi import FastAPI"],
            ),
            FrameworkFinding(
                name="React",
                category="frontend",
                confidence=0.85,
                evidence=["import React"],
            ),
        ],
        entry_points=["backend/main.py", "frontend/src/App.tsx"],
        key_folders=["backend", "frontend"],
        summary="Full-stack web app with FastAPI backend and React frontend",
        warnings=[],
    )


@pytest.fixture
def sample_routes():
    """Create sample routes."""
    return [
        RouteInfo(
            framework="FastAPI",
            method="GET",
            path="/trips",
            file_path="backend/routes/trips.py",
            function_name="list_trips",
        ),
        RouteInfo(
            framework="FastAPI",
            method="POST",
            path="/trips",
            file_path="backend/routes/trips.py",
            function_name="create_trip",
        ),
        RouteInfo(
            framework="FastAPI",
            method="DELETE",
            path="/trips/{trip_id}",
            file_path="backend/routes/trips.py",
            function_name="delete_trip",
        ),
    ]


@pytest.fixture
def sample_component_cards():
    """Create sample component cards."""
    return [
        ComponentCard(
            path="backend/routes/trips.py",
            title="Trip Routes",
            role="backend_route",
            why_it_matters="Main API endpoints",
            connected_to=["backend/models/trip.py"],
            detected_items=["GET /trips", "POST /trips", "DELETE /trips/{trip_id}"],
            suggested_test_ideas=["Test edge cases"],
            suggested_bob_prompt="Analyze trip routes",
        ),
    ]


@pytest.fixture
def sample_work_plan():
    """Create a sample work plan."""
    return WorkPlan(
        epics=["Testing & Quality", "Documentation"],
        tasks=[
            TaskSuggestion(
                epic="Testing & Quality",
                priority="high",
                files=["backend/routes/trips.py"],
                evidence=["Routes detected"],
                why="Tests are important",
                acceptance_criteria=["Tests pass"],
                suggested_workflow="Add tests",
            ),
        ],
        milestones=[
            SuggestedMilestone(
                title="Testing Milestone",
                goal="Improve test coverage",
                tasks=[],
            ),
        ],
        workflows=[
            AgentWorkflow(
                title="Add tests",
                goal="Improve coverage",
                ordered_steps=["Write tests"],
                files_to_read=["backend/routes/trips.py"],
                files_to_change=["backend/tests/test_trips.py"],
                validation_steps=["Run pytest"],
                expected_output="Tests pass",
                prompt="Add tests",
            ),
        ],
    )


@pytest.fixture
def sample_context_pack():
    """Create a sample context pack."""
    return ContextPack(
        project_summary="Full-stack web app",
        frameworks=["FastAPI", "React"],
        entry_points=["backend/main.py"],
        routes_summary="3 routes detected",
        component_summary="1 component",
        test_summary="1 test file",
        workflow_summary="1 workflow",
        evidence_snippets={"backend/routes/trips.py": "def list_trips():"},
        warnings=[],
        total_files_scanned=4,
    )


def test_generate_mock_recommendations(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_component_cards,
    sample_work_plan,
    sample_context_pack,
):
    """Test mock recommendation generation."""
    result = generate_mock_recommendations(
        sample_snapshot,
        sample_fingerprint,
        sample_routes,
        sample_component_cards,
        sample_work_plan,
        sample_context_pack,
    )
    
    assert result.provider == "mock"
    assert result.model == "deterministic-v1"
    assert len(result.recommendations) > 0
    
    # Check that recommendations are validated
    for rec in result.recommendations:
        assert rec.validation_status in {"valid", "downgraded", "invalid"}
        assert rec.title
        assert rec.category
        assert rec.priority in {"high", "medium", "low"}


def test_mock_recommendations_reference_existing_files(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_component_cards,
    sample_work_plan,
    sample_context_pack,
):
    """Test that mock recommendations only reference existing files."""
    result = generate_mock_recommendations(
        sample_snapshot,
        sample_fingerprint,
        sample_routes,
        sample_component_cards,
        sample_work_plan,
        sample_context_pack,
    )
    
    valid_files = {f.path for f in sample_snapshot.files}
    
    for rec in result.trusted_recommendations:
        for file_path in rec.files:
            assert file_path in valid_files, f"Recommendation references nonexistent file: {file_path}"


def test_mock_recommendations_have_evidence(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_component_cards,
    sample_work_plan,
    sample_context_pack,
):
    """Test that mock recommendations include evidence."""
    result = generate_mock_recommendations(
        sample_snapshot,
        sample_fingerprint,
        sample_routes,
        sample_component_cards,
        sample_work_plan,
        sample_context_pack,
    )
    
    for rec in result.trusted_recommendations:
        assert len(rec.evidence) > 0, f"Recommendation '{rec.title}' has no evidence"


def test_create_recommendation_prompt(sample_context_pack, sample_work_plan):
    """Test recommendation prompt creation."""
    prompt = create_recommendation_prompt(sample_context_pack, sample_work_plan)
    
    assert "Code Recommendation Task" in prompt
    assert "Full-stack web app" in prompt
    assert "FastAPI" in prompt
    assert "JSON array" in prompt


def test_parse_ai_recommendations_valid_json(sample_snapshot):
    """Test parsing valid AI recommendation JSON."""
    response_text = """
Here are my recommendations:

```json
[
  {
    "title": "Add edge-case tests",
    "category": "testing",
    "priority": "high",
    "files": ["backend/routes/trips.py"],
    "evidence": ["Route exists"],
    "rationale": "Tests are important",
    "proposed_change_summary": "Add tests",
    "test_plan": ["Write tests"],
    "workflow": "Test workflow",
    "confidence": 0.85
  }
]
```
"""
    
    recommendations = parse_ai_recommendations(response_text, sample_snapshot)
    
    assert len(recommendations) == 1
    assert recommendations[0].title == "Add edge-case tests"
    assert recommendations[0].category == "testing"
    assert recommendations[0].priority == "high"


def test_parse_ai_recommendations_invalid_json(sample_snapshot):
    """Test parsing invalid JSON returns empty list."""
    response_text = "This is not JSON"
    
    recommendations = parse_ai_recommendations(response_text, sample_snapshot)
    
    assert len(recommendations) == 0


def test_parse_ai_recommendations_validates_files(sample_snapshot):
    """Test that parsed recommendations are validated."""
    response_text = """
```json
[
  {
    "title": "Test",
    "category": "testing",
    "priority": "high",
    "files": ["nonexistent.py"],
    "evidence": ["Evidence"],
    "rationale": "Rationale",
    "proposed_change_summary": "Summary",
    "test_plan": ["Plan"],
    "workflow": "Workflow",
    "confidence": 0.8
  }
]
```
"""
    
    recommendations = parse_ai_recommendations(response_text, sample_snapshot)
    
    assert len(recommendations) == 1
    # File should be removed during validation
    assert "nonexistent.py" not in recommendations[0].files


def test_generate_recommendation_summary(sample_context_pack):
    """Test recommendation summary generation."""
    from repoquest.assistant_models import CodeRecommendation, AIRecommendationResult
    
    result = AIRecommendationResult(
        recommendations=[
            CodeRecommendation(
                title="High priority rec",
                category="testing",
                priority="high",
                files=[],
                evidence=["Evidence"],
                rationale="Rationale",
                proposed_change_summary="Summary",
                test_plan=[],
                workflow="Workflow",
                confidence=0.9,
                validation_status="valid",
            ),
            CodeRecommendation(
                title="Medium priority rec",
                category="documentation",
                priority="medium",
                files=[],
                evidence=["Evidence"],
                rationale="Rationale",
                proposed_change_summary="Summary",
                test_plan=[],
                workflow="Workflow",
                confidence=0.7,
                validation_status="valid",
            ),
        ],
        provider="mock",
        model="test",
        context_pack=sample_context_pack,
    )
    
    summary = generate_recommendation_summary(result)
    
    assert "AI Code Recommendations" in summary
    assert "mock" in summary
    assert "High Priority" in summary
    assert "Medium Priority" in summary
    assert "High priority rec" in summary
    assert "Medium priority rec" in summary
