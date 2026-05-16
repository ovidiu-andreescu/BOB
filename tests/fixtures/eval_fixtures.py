"""Eval fixtures for testing AI assistant trust gates."""

from repoquest.assistant_models import (
    AssistantCitation,
    AssistantResponse,
    CodeRecommendation,
    ContextPack,
    GeneratedDocPage,
)
from repoquest.models import FileInfo, RepositorySnapshot


def create_test_snapshot() -> RepositorySnapshot:
    """Create a test repository snapshot."""
    return RepositorySnapshot(
        source_name="test_repo",
        files=[
            FileInfo(
                path="backend/main.py",
                name="main.py",
                suffix=".py",
                size_bytes=1000,
                language="python",
                role="entrypoint",
                text_preview="from fastapi import FastAPI\napp = FastAPI()",
                line_count=50,
            ),
            FileInfo(
                path="backend/routes/trips.py",
                name="trips.py",
                suffix=".py",
                size_bytes=2000,
                language="python",
                role="backend_route",
                text_preview="@router.get('/trips')\ndef list_trips():",
                line_count=100,
            ),
            FileInfo(
                path="frontend/src/App.tsx",
                name="App.tsx",
                suffix=".tsx",
                size_bytes=1500,
                language="typescript",
                role="entrypoint",
                text_preview="import React from 'react'",
                line_count=75,
            ),
        ],
        total_files_seen=3,
        total_files_scanned=3,
        warnings=[],
    )


def create_valid_response() -> AssistantResponse:
    """Create a valid assistant response."""
    return AssistantResponse(
        status="ok",
        response_text="This is a FastAPI backend with React frontend.",
        citations=[
            AssistantCitation(
                file_path="backend/main.py",
                line_range="1-2",
                snippet="from fastapi import FastAPI",
                relevance="Main entry point",
            ),
        ],
        provider="mock",
        model="test-model-v1",
    )


def create_empty_response() -> AssistantResponse:
    """Create an empty response (should fail validation)."""
    return AssistantResponse(
        status="ok",
        response_text="",
        citations=[],
        provider="mock",
        model="test-model-v1",
    )


def create_response_missing_metadata() -> AssistantResponse:
    """Create a response with missing provider/model metadata."""
    return AssistantResponse(
        status="ok",
        response_text="This is a test response.",
        citations=[],
        provider="unknown",
        model="unknown",
    )


def create_response_with_hallucinated_files() -> AssistantResponse:
    """Create a response citing nonexistent files."""
    return AssistantResponse(
        status="ok",
        response_text="Check the database models in models/user.py",
        citations=[
            AssistantCitation(
                file_path="models/user.py",  # Does not exist in snapshot
                line_range="10-20",
                snippet="class User:",
                relevance="User model",
            ),
            AssistantCitation(
                file_path="config/settings.py",  # Does not exist
                line_range="1-5",
                snippet="DATABASE_URL = ...",
                relevance="Database config",
            ),
        ],
        provider="mock",
        model="test-model-v1",
    )


def create_response_claiming_test_execution() -> AssistantResponse:
    """Create a response claiming tests were executed."""
    return AssistantResponse(
        status="ok",
        response_text="I ran the tests and all tests passed successfully.",
        citations=[],
        provider="mock",
        model="test-model-v1",
    )


def create_response_instructing_code_execution() -> AssistantResponse:
    """Create a response instructing code execution."""
    return AssistantResponse(
        status="ok",
        response_text="To verify this, run this code: python main.py",
        citations=[],
        provider="mock",
        model="test-model-v1",
    )


def create_response_with_secrets() -> AssistantResponse:
    """Create a response containing potential secrets."""
    return AssistantResponse(
        status="ok",
        response_text="Set your API_KEY='sk-1234567890abcdefghijklmnopqrstuvwxyz' in the config.",
        citations=[],
        provider="mock",
        model="test-model-v1",
    )


def create_response_with_multiple_violations() -> AssistantResponse:
    """Create a response with multiple validation violations."""
    return AssistantResponse(
        status="ok",
        response_text="I executed the tests and they passed. Check nonexistent.py for details.",
        citations=[
            AssistantCitation(
                file_path="nonexistent.py",
                line_range="1-10",
                snippet="# code",
                relevance="Test file",
            ),
        ],
        provider="mock",
        model="test-model-v1",
    )


def create_local_model_verbose_response() -> AssistantResponse:
    """Create a verbose local-model-style response that ignores schema."""
    return AssistantResponse(
        status="ok",
        response_text="""I understand you want me to analyze this repository. 
        Let me think about this carefully. Based on my analysis of the code structure,
        I can see that this appears to be a web application. The backend uses FastAPI
        which is a modern Python framework. The frontend appears to use React.
        
        Here are my thoughts on the architecture:
        1. The backend is well-structured
        2. The frontend follows React best practices
        3. There are opportunities for improvement
        
        Would you like me to elaborate on any of these points?""",
        citations=[],  # Local models often don't provide structured citations
        provider="local",
        model="llama-3.1-8b",
    )


def create_valid_recommendation() -> CodeRecommendation:
    """Create a valid code recommendation."""
    return CodeRecommendation(
        title="Add input validation to trip search",
        category="api",
        priority="high",
        files=["backend/routes/trips.py"],
        evidence=["backend/routes/trips.py"],
        rationale="The trip search endpoint lacks input validation for required fields.",
        proposed_change_summary="Add Pydantic model for search request validation.",
        test_plan=["Test with missing destination", "Test with invalid date format"],
        workflow="1. Create SearchRequest model\n2. Update route handler\n3. Add tests",
        confidence=0.85,
    )


def create_recommendation_missing_evidence() -> CodeRecommendation:
    """Create a recommendation without evidence."""
    return CodeRecommendation(
        title="Improve error handling",
        category="error_handling",
        priority="medium",
        files=["backend/main.py"],
        evidence=[],  # No evidence
        rationale="Error handling could be improved.",
        proposed_change_summary="Add global exception handler.",
        test_plan=["Test error scenarios"],
        workflow="Add exception handler",
        confidence=0.6,
    )


def create_recommendation_with_hallucinated_files() -> CodeRecommendation:
    """Create a recommendation referencing nonexistent files."""
    return CodeRecommendation(
        title="Update database schema",
        category="data_model",
        priority="high",
        files=["models/database.py", "migrations/001_initial.sql"],  # Don't exist
        evidence=["models/database.py"],
        rationale="Database schema needs updating.",
        proposed_change_summary="Add new fields to user table.",
        test_plan=["Test migration"],
        workflow="Run migration script",
        confidence=0.75,
    )


def create_recommendation_low_confidence() -> CodeRecommendation:
    """Create a recommendation with low confidence."""
    return CodeRecommendation(
        title="Consider using GraphQL",
        category="api",
        priority="low",
        files=["backend/main.py"],
        evidence=["backend/main.py"],
        rationale="GraphQL might be beneficial.",
        proposed_change_summary="Replace REST with GraphQL.",
        test_plan=["Evaluate GraphQL libraries"],
        workflow="Research and prototype",
        confidence=0.2,  # Very low confidence
    )


def create_recommendation_with_secrets() -> CodeRecommendation:
    """Create a recommendation containing secrets."""
    return CodeRecommendation(
        title="Configure API authentication",
        category="api",
        priority="high",
        files=["backend/main.py"],
        evidence=["backend/main.py"],
        rationale="API needs authentication.",
        proposed_change_summary="Add API key authentication with key: api_key='sk-1234567890abcdefghij'",
        test_plan=["Test with valid key", "Test with invalid key"],
        workflow="Add auth middleware",
        confidence=0.8,
    )


def create_valid_doc_page() -> GeneratedDocPage:
    """Create a valid generated documentation page."""
    return GeneratedDocPage(
        title="Backend API Overview",
        category="backend",
        source_files=["backend/main.py", "backend/routes/trips.py"],
        content="# Backend API\n\nThe backend uses FastAPI...",
        evidence=["backend/main.py", "backend/routes/trips.py"],
        related_components=["frontend/src/services/api.ts"],
    )


def create_doc_page_missing_sources() -> GeneratedDocPage:
    """Create a doc page without source files."""
    return GeneratedDocPage(
        title="Architecture Overview",
        category="architecture",
        source_files=[],  # No sources
        content="# Architecture\n\nThis is the architecture...",
        evidence=[],
    )


def create_doc_page_with_hallucinated_files() -> GeneratedDocPage:
    """Create a doc page referencing nonexistent files."""
    return GeneratedDocPage(
        title="Database Layer",
        category="backend",
        source_files=["database/connection.py", "database/models.py"],  # Don't exist
        content="# Database\n\nThe database layer...",
        evidence=["database/connection.py"],
    )


def create_doc_page_with_secrets() -> GeneratedDocPage:
    """Create a doc page containing secrets."""
    return GeneratedDocPage(
        title="Configuration Guide",
        category="documentation",
        source_files=["backend/main.py"],
        content="# Configuration\n\nSet your api_key='sk-1234567890abcdefghijklmnopqrstuvwxyz' in the environment.",
        evidence=["backend/main.py"],
    )


def create_test_context_pack() -> ContextPack:
    """Create a test context pack."""
    return ContextPack(
        project_summary="Full-stack web app with React + FastAPI",
        frameworks=["React", "FastAPI", "Vite"],
        entry_points=["backend/main.py", "frontend/src/App.tsx"],
        routes_summary="3 API routes detected",
        component_summary="5 React components",
        test_summary="10 backend tests",
        workflow_summary="Standard web app workflow",
        evidence_snippets={
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "frontend/src/App.tsx": "import React from 'react'",
        },
        warnings=[],
        total_files_scanned=3,
    )


# Made with Bob
