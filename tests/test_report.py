"""Tests for report generation."""

import pytest
from repoquest.models import (
    FileInfo,
    RepositorySnapshot,
    ProjectFingerprint,
    FrameworkFinding,
    RouteInfo,
    ReadingPathItem,
    ComponentCard,
    QuizQuestion,
    ImportEdge,
)
from repoquest.report import (
    generate_markdown_report,
    extract_code_snippet,
    get_test_files,
    get_doc_files,
    generate_dependency_summary,
)


@pytest.fixture
def sample_file_info():
    """Create a sample FileInfo."""
    return FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=1024,
        language="python",
        role="entrypoint",
        text_preview="from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}",
        line_count=7,
        skipped=False,
    )


@pytest.fixture
def sample_snapshot():
    """Create a sample RepositorySnapshot."""
    files = [
        FileInfo(
            path="README.md",
            name="README.md",
            suffix=".md",
            size_bytes=500,
            language="markdown",
            role="documentation",
            text_preview="# Test Project\n\nA test project for RepoQuest.",
            line_count=3,
        ),
        FileInfo(
            path="backend/main.py",
            name="main.py",
            suffix=".py",
            size_bytes=1024,
            language="python",
            role="entrypoint",
            text_preview="from fastapi import FastAPI\n\napp = FastAPI()",
            line_count=3,
        ),
        FileInfo(
            path="backend/tests/test_main.py",
            name="test_main.py",
            suffix=".py",
            size_bytes=800,
            language="python",
            role="test",
            text_preview="import pytest\n\ndef test_health():\n    pass",
            line_count=4,
        ),
        FileInfo(
            path="package.json",
            name="package.json",
            suffix=".json",
            size_bytes=300,
            language="json",
            role="config",
            text_preview='{"name": "test-project"}',
            line_count=1,
        ),
    ]
    
    return RepositorySnapshot(
        source_name="test-project",
        files=files,
        total_files_seen=4,
        total_files_scanned=4,
        warnings=[],
    )


@pytest.fixture
def sample_fingerprint():
    """Create a sample ProjectFingerprint."""
    return ProjectFingerprint(
        project_type="Backend API",
        confidence=0.85,
        frameworks=[
            FrameworkFinding(
                name="FastAPI",
                category="backend",
                confidence=0.9,
                evidence=["backend/main.py: contains 'from fastapi import FastAPI'"],
            )
        ],
        entry_points=["backend/main.py"],
        key_folders=["backend", "backend/tests"],
        summary="A FastAPI backend application.",
        warnings=[],
    )


@pytest.fixture
def sample_routes():
    """Create sample RouteInfo list."""
    return [
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/health",
            file_path="backend/main.py",
            function_name="health",
        ),
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/items",
            file_path="backend/routes/items.py",
            function_name="list_items",
        ),
    ]


@pytest.fixture
def sample_reading_path():
    """Create sample ReadingPathItem list."""
    return [
        ReadingPathItem(
            order=1,
            path="README.md",
            reason="Start with the README to understand the project purpose.",
            estimated_minutes=2,
        ),
        ReadingPathItem(
            order=2,
            path="backend/main.py",
            reason="Main entry point for the backend application.",
            estimated_minutes=5,
        ),
    ]


@pytest.fixture
def sample_component_cards():
    """Create sample ComponentCard list."""
    return [
        ComponentCard(
            path="backend/main.py",
            title="Backend Entry Point",
            role="entrypoint",
            why_it_matters="This is where the FastAPI application is initialized.",
            connected_to=["backend/routes/items.py"],
            detected_items=["@app.get('/health')"],
            suggested_test_ideas=["Test health endpoint returns 200"],
            suggested_bob_prompt="Explain backend/main.py and suggest improvements.",
        )
    ]


@pytest.fixture
def sample_quiz():
    """Create sample QuizQuestion list."""
    return [
        QuizQuestion(
            question="Which file is the backend entry point?",
            options=["README.md", "backend/main.py", "package.json", "backend/tests/test_main.py"],
            correct_answer="backend/main.py",
            explanation="backend/main.py contains the FastAPI application initialization.",
        )
    ]


@pytest.fixture
def sample_import_edges():
    """Create sample ImportEdge list."""
    return [
        ImportEdge(
            source="backend/main.py",
            target="backend/routes/items.py",
            kind="python_import",
            confidence=1.0,
        ),
        ImportEdge(
            source="frontend/src/App.tsx",
            target="frontend/src/services/api.ts",
            kind="ts_import",
            confidence=1.0,
        ),
    ]


def test_extract_code_snippet(sample_file_info):
    """Test code snippet extraction."""
    snippet = extract_code_snippet(sample_file_info, "FastAPI", max_lines=3)
    
    assert snippet is not None
    assert "FastAPI" in snippet
    assert "from fastapi import FastAPI" in snippet


def test_extract_code_snippet_not_found(sample_file_info):
    """Test code snippet extraction when pattern not found."""
    snippet = extract_code_snippet(sample_file_info, "NonExistentPattern")
    
    assert snippet is None


def test_extract_code_snippet_no_preview():
    """Test code snippet extraction with no preview."""
    file_info = FileInfo(
        path="test.py",
        name="test.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="unknown",
        text_preview="",
        line_count=0,
    )
    
    snippet = extract_code_snippet(file_info, "test")
    assert snippet is None


def test_get_test_files(sample_snapshot):
    """Test test file detection."""
    test_files = get_test_files(sample_snapshot)
    
    assert len(test_files) == 1
    assert test_files[0].path == "backend/tests/test_main.py"
    assert test_files[0].role == "test"


def test_get_doc_files(sample_snapshot):
    """Test documentation file detection."""
    doc_files = get_doc_files(sample_snapshot)
    
    assert len(doc_files) == 2
    paths = [f.path for f in doc_files]
    assert "README.md" in paths
    assert "package.json" in paths


def test_generate_dependency_summary_with_edges(sample_snapshot, sample_import_edges):
    """Test dependency summary generation."""
    summary = generate_dependency_summary(sample_snapshot, sample_import_edges)
    
    assert "frontend/src/App.tsx" in summary or "Sample dependencies" in summary
    assert "→" in summary


def test_generate_dependency_summary_no_edges(sample_snapshot):
    """Test dependency summary with no edges."""
    summary = generate_dependency_summary(sample_snapshot, [])
    
    assert summary == "No import relationships detected."


def test_generate_markdown_report_basic(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test basic Markdown report generation."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    # Check required sections
    assert "# RepoQuest Onboarding Guide" in report
    assert "## Summary" in report
    assert "## Detected Project Type" in report
    assert "## Frameworks and Evidence" in report
    assert "## Key Entry Points" in report
    assert "## Architecture Map Summary" in report
    assert "## Routes Detected" in report
    assert "## Tests Detected" in report
    assert "## 30-Minute Reading Path" in report
    assert "## Component Cards" in report
    assert "## Documentation and Config Previews" in report
    assert "## Onboarding Checklist" in report
    assert "## Quiz Questions" in report
    assert "## Suggested IBM Bob Prompts" in report
    assert "## Warnings and Limitations" in report
    
    # Check content
    assert "test-project" in report
    assert "Backend API" in report
    assert "FastAPI" in report
    assert "backend/main.py" in report
    assert "GET /health" in report
    assert "README.md" in report


def test_generate_markdown_report_with_import_edges(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
    sample_import_edges,
):
    """Test Markdown report generation with import edges."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
        import_edges=sample_import_edges,
    )
    
    assert "## Dependency Summary" in report
    assert "→" in report


def test_generate_markdown_report_includes_framework_evidence(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes framework evidence."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "FastAPI" in report
    assert "backend/main.py: contains 'from fastapi import FastAPI'" in report


def test_generate_markdown_report_includes_route_examples(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes route examples."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "GET /health" in report
    assert "health" in report
    assert "backend/main.py" in report


def test_generate_markdown_report_includes_test_section(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes test section."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "## Tests Detected" in report
    assert "backend/tests/test_main.py" in report


def test_generate_markdown_report_includes_doc_previews(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes documentation previews."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "## Documentation and Config Previews" in report
    assert "README.md" in report
    assert "package.json" in report


def test_generate_markdown_report_includes_bob_prompts(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes IBM Bob prompts."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "## Suggested IBM Bob Prompts" in report
    assert "Explain backend/main.py and suggest improvements." in report


def test_generate_markdown_report_includes_limitations(
    sample_snapshot,
    sample_fingerprint,
    sample_routes,
    sample_reading_path,
    sample_component_cards,
    sample_quiz,
):
    """Test that report includes limitations section."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=sample_routes,
        reading_path=sample_reading_path,
        component_cards=sample_component_cards,
        quiz=sample_quiz,
    )
    
    assert "## Warnings and Limitations" in report
    assert "deterministic static analysis" in report
    assert "Does not execute code" in report
    assert "Does not use runtime AI/LLMs" in report


def test_generate_markdown_report_empty_lists(sample_snapshot, sample_fingerprint):
    """Test report generation with empty lists."""
    report = generate_markdown_report(
        snapshot=sample_snapshot,
        fingerprint=sample_fingerprint,
        routes=[],
        reading_path=[],
        component_cards=[],
        quiz=[],
    )
    
    # Should still have all sections
    assert "# RepoQuest Onboarding Guide" in report
    assert "## Summary" in report
    assert "test-project" in report

# Made with Bob
