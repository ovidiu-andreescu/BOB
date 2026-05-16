"""Tests for context pack builders and documentation generation."""

from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    FileInfo,
    RouteInfo,
    ComponentCard,
    TestIntelligence,
    TestInsight,
    WorkPlan,
    TaskSuggestion,
)
from repoquest.assistant_context import build_context_pack
from repoquest.doc_generator import (
    validate_doc_page,
    generate_api_routes_doc,
    generate_component_docs,
    generate_models_doc,
    generate_test_reference_doc,
    generate_all_deterministic_docs,
)
from repoquest.assistant_models import GeneratedDocPage


def test_context_pack_excludes_skipped_files():
    """Test that context pack excludes skipped files."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="good.py",
                name="good.py",
                suffix=".py",
                size_bytes=100,
                language="python",
                role="entrypoint",
                text_preview="def main(): pass",
                line_count=1,
                skipped=False,
            ),
            FileInfo(
                path="skipped.bin",
                name="skipped.bin",
                suffix=".bin",
                size_bytes=1000,
                language="unknown",
                role="unknown",
                text_preview="",
                line_count=0,
                skipped=True,
                skip_reason="binary",
            ),
        ],
        total_files_seen=2,
        total_files_scanned=1,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="test",
        confidence=0.9,
        frameworks=[],
        entry_points=["good.py"],
        key_folders=[],
        summary="Test project",
        warnings=[],
    )
    
    context_pack = build_context_pack(snapshot, fingerprint)
    
    # Should only include good.py in evidence
    assert "good.py" in context_pack.evidence_snippets
    assert "skipped.bin" not in context_pack.evidence_snippets


def test_context_pack_includes_route_evidence():
    """Test that context pack includes route evidence."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="routes.py",
                name="routes.py",
                suffix=".py",
                size_bytes=200,
                language="python",
                role="backend_route",
                text_preview="@app.get('/test')\ndef test(): pass",
                line_count=2,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="backend",
        confidence=0.9,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Test backend",
        warnings=[],
    )
    
    routes = [
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/test",
            file_path="routes.py",
            function_name="test",
        ),
    ]
    
    context_pack = build_context_pack(snapshot, fingerprint, routes=routes)
    
    assert "fastapi" in context_pack.routes_summary
    assert "GET /test" in context_pack.routes_summary
    assert "routes.py" in context_pack.evidence_snippets


def test_context_pack_includes_test_summary():
    """Test that context pack includes test intelligence summary."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="test",
        confidence=0.9,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Test project",
        warnings=[],
    )
    
    test_intelligence = TestIntelligence(
        test_insights=[
            TestInsight(
                test_file="test_app.py",
                framework="pytest",
                imports=[],
                likely_targets=["app.py"],
                covered_routes=[],
                missing_cases=[],
                suggested_tests=[],
                quality_signals={},
            ),
        ],
        missing_coverage=["uncovered.py"],
        suggested_tests=[],
        test_plan="5 tests found",
    )
    
    context_pack = build_context_pack(
        snapshot,
        fingerprint,
        test_intelligence=test_intelligence,
    )
    
    assert "Test files: 1" in context_pack.test_summary
    assert "Missing coverage: 1" in context_pack.test_summary


def test_context_pack_includes_workflow_summary():
    """Test that context pack includes workflow summary."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="test",
        confidence=0.9,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Test project",
        warnings=[],
    )
    
    work_plan = WorkPlan(
        epics=["Add authentication", "Improve error handling"],
        tasks=[
            TaskSuggestion(
                epic="Add authentication",
                priority="high",
                files=["auth.py"],
                evidence=["Need login endpoint"],
                why="Add login endpoint for user authentication",
                acceptance_criteria=["Login endpoint returns JWT token"],
                suggested_workflow="Development",
            ),
        ],
        milestones=[],
        workflows=[],
    )
    
    context_pack = build_context_pack(
        snapshot,
        fingerprint,
        work_plan=work_plan,
    )
    
    assert "Epics: 2" in context_pack.workflow_summary
    assert "Tasks: 1" in context_pack.workflow_summary
    assert "Workflows: 0" in context_pack.workflow_summary


def test_context_pack_caps_evidence_snippets():
    """Test that context pack caps evidence snippet size."""
    large_content = "x" * 2000
    
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="large.py",
                name="large.py",
                suffix=".py",
                size_bytes=2000,
                language="python",
                role="entrypoint",
                text_preview=large_content,
                line_count=100,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="test",
        confidence=0.9,
        frameworks=[],
        entry_points=["large.py"],
        key_folders=[],
        summary="Test project",
        warnings=[],
    )
    
    context_pack = build_context_pack(snapshot, fingerprint)
    
    # Should be capped to 600 chars (plus newline and truncation message)
    assert len(context_pack.evidence_snippets["large.py"]) <= 620  # 600 + "\n... (truncated)"


def test_validate_doc_page_rejects_missing_source_files():
    """Test that validation rejects doc pages with missing source files."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="exists.py",
                name="exists.py",
                suffix=".py",
                size_bytes=100,
                language="python",
                role="entrypoint",
                text_preview="",
                line_count=1,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    doc_page = GeneratedDocPage(
        title="Test Doc",
        category="test",
        source_files=["exists.py", "missing.py"],
        content="Test content",
        evidence=["exists.py"],
    )
    
    is_valid, errors = validate_doc_page(doc_page, snapshot)
    
    assert not is_valid
    assert any("missing.py" in error for error in errors)


def test_validate_doc_page_rejects_unsafe_execution_claims():
    """Test that validation rejects doc pages with unsafe execution claims."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="test.py",
                name="test.py",
                suffix=".py",
                size_bytes=100,
                language="python",
                role="test",
                text_preview="",
                line_count=1,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    doc_page = GeneratedDocPage(
        title="Test Doc",
        category="test",
        source_files=["test.py"],
        content="We ran the tests and they all passed.",
        evidence=["test.py"],
    )
    
    is_valid, errors = validate_doc_page(doc_page, snapshot)
    
    assert not is_valid
    assert any("unsafe execution claim" in error.lower() for error in errors)


def test_generate_api_routes_doc():
    """Test API routes documentation generation."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    
    routes = [
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/users",
            file_path="routes/users.py",
            function_name="list_users",
        ),
        RouteInfo(
            framework="fastapi",
            method="POST",
            path="/users",
            file_path="routes/users.py",
            function_name="create_user",
        ),
    ]
    
    doc_page = generate_api_routes_doc(routes, snapshot)
    
    assert doc_page.title == "API Routes Reference"
    assert doc_page.category == "api"
    assert "routes/users.py" in doc_page.source_files
    assert "GET /users" in doc_page.content
    assert "POST /users" in doc_page.content
    assert "static analysis" in doc_page.content.lower()


def test_generate_component_docs():
    """Test component documentation generation."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    
    component_cards = [
        ComponentCard(
            path="components/Button.tsx",
            title="Button Component",
            role="frontend_component",
            why_it_matters="Reusable button component",
            connected_to=["components/Form.tsx"],
            detected_items=["onClick handler", "disabled prop"],
            suggested_test_ideas=["Test click handler", "Test disabled state"],
            suggested_bob_prompt="Review Button component",
        ),
    ]
    
    doc_pages = generate_component_docs(component_cards, snapshot)
    
    assert len(doc_pages) == 1
    assert doc_pages[0].title == "Frontend Component Components"
    assert "Button Component" in doc_pages[0].content
    assert "components/Button.tsx" in doc_pages[0].source_files


def test_generate_models_doc():
    """Test models documentation generation."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="models/user.py",
                name="user.py",
                suffix=".py",
                size_bytes=200,
                language="python",
                role="model",
                text_preview="class User:\n    pass",
                line_count=2,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    doc_page = generate_models_doc(snapshot)
    
    assert doc_page.title == "Models & Schemas Reference"
    assert doc_page.category == "models"
    assert "models/user.py" in doc_page.source_files
    assert "user.py" in doc_page.content


def test_generate_test_reference_doc():
    """Test test reference documentation generation."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="tests/test_app.py",
                name="test_app.py",
                suffix=".py",
                size_bytes=300,
                language="python",
                role="test",
                text_preview="def test_main(): pass",
                line_count=1,
            ),
        ],
        total_files_seen=1,
        total_files_scanned=1,
        warnings=[],
    )
    
    doc_page = generate_test_reference_doc(snapshot)
    
    assert doc_page.title == "Test Reference"
    assert doc_page.category == "tests"
    assert "tests/test_app.py" in doc_page.source_files
    assert "No tests were executed" in doc_page.content


def test_generate_all_deterministic_docs():
    """Test generation of all deterministic documentation pages."""
    snapshot = RepositorySnapshot(
        source_name="test",
        files=[
            FileInfo(
                path="models/user.py",
                name="user.py",
                suffix=".py",
                size_bytes=100,
                language="python",
                role="model",
                text_preview="class User: pass",
                line_count=1,
            ),
            FileInfo(
                path="tests/test_user.py",
                name="test_user.py",
                suffix=".py",
                size_bytes=100,
                language="python",
                role="test",
                text_preview="def test_user(): pass",
                line_count=1,
            ),
        ],
        total_files_seen=2,
        total_files_scanned=2,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="backend",
        confidence=0.9,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Test backend",
        warnings=[],
    )
    
    routes = [
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/users",
            file_path="routes.py",
            function_name="list_users",
        ),
    ]
    
    component_cards = [
        ComponentCard(
            path="routes.py",
            title="User Routes",
            role="backend_route",
            why_it_matters="User API endpoints",
            connected_to=[],
            detected_items=[],
            suggested_test_ideas=[],
            suggested_bob_prompt="",
        ),
    ]
    
    doc_pages = generate_all_deterministic_docs(
        snapshot,
        fingerprint,
        routes=routes,
        component_cards=component_cards,
    )
    
    # Should generate: API routes, component docs, models, tests
    assert len(doc_pages) >= 4
    
    categories = [page.category for page in doc_pages]
    assert "api" in categories
    assert "models" in categories
    assert "tests" in categories

# Made with Bob
