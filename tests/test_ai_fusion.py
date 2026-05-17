"""Tests for AI Fusion hybrid analysis."""

import json
from pathlib import Path

from repoquest.ai_fusion import parse_ai_fusion_response, run_ai_fusion
from repoquest.assistant_models import AssistantResponse
from repoquest.assistant_provider import DisabledAssistantProvider, MockAssistantProvider
from repoquest.models import (
    FileInfo,
    FrameworkFinding,
    ImportEdge,
    ProjectFingerprint,
    ReadingPathItem,
    RepositorySnapshot,
    RouteInfo,
)
from repoquest.quest import generate_component_cards
from repoquest.workspace_state import SourceMetadata, WorkspaceState


def make_snapshot() -> RepositorySnapshot:
    """Create a small static snapshot for fusion tests."""
    return RepositorySnapshot(
        source_name="sample",
        files=[
            FileInfo(
                path="README.md",
                name="README.md",
                suffix=".md",
                size_bytes=120,
                language="Markdown",
                role="documentation",
                text_preview="Sample app",
                line_count=4,
            ),
            FileInfo(
                path="backend/main.py",
                name="main.py",
                suffix=".py",
                size_bytes=200,
                language="Python",
                role="entrypoint",
                text_preview="from fastapi import FastAPI\napp = FastAPI()",
                line_count=8,
            ),
            FileInfo(
                path="frontend/src/App.tsx",
                name="App.tsx",
                suffix=".tsx",
                size_bytes=200,
                language="TypeScript",
                role="entrypoint",
                text_preview="import TripsPage from './pages/TripsPage'",
                line_count=8,
            ),
        ],
        total_files_seen=3,
        total_files_scanned=3,
        warnings=[],
    )


def make_fingerprint(confidence: float = 0.55) -> ProjectFingerprint:
    """Create a deterministic fingerprint for fusion tests."""
    return ProjectFingerprint(
        project_type="Unknown/mixed repo",
        confidence=confidence,
        frameworks=[
            FrameworkFinding(
                name="FastAPI",
                category="backend",
                confidence=0.9,
                evidence=["backend/main.py: Contains 'from fastapi import FastAPI'"],
            )
        ],
        entry_points=["backend/main.py", "frontend/src/App.tsx"],
        key_folders=["backend/", "frontend/"],
        summary="Classified with limited confidence",
        warnings=[],
    )


def make_routes() -> list[RouteInfo]:
    """Create route fixtures."""
    return [
        RouteInfo(
            framework="fastapi",
            method="GET",
            path="/trips",
            file_path="backend/main.py",
            function_name="list_trips",
        )
    ]


def make_reading_path() -> list[ReadingPathItem]:
    """Create reading path fixtures."""
    return [
        ReadingPathItem(
            order=1,
            path="README.md",
            reason="Start with repository context.",
            estimated_minutes=3,
        ),
        ReadingPathItem(
            order=2,
            path="backend/main.py",
            reason="Understand backend startup.",
            estimated_minutes=5,
        ),
    ]


def response(payload: dict[str, object]) -> AssistantResponse:
    """Build an ok AI response from a JSON payload."""
    return AssistantResponse(
        status="ok",
        response_text=json.dumps(payload),
        provider="mock",
        model="mock-model",
    )


def test_valid_ai_project_type_override_changes_final_interpretation():
    """A high-confidence, cited project type override is applied."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint(confidence=0.55)
    result = parse_ai_fusion_response(
        response(
            {
                "summary": "This is a web app.",
                "claims": [
                    {
                        "claim_type": "project_type",
                        "value": "Full-stack web application",
                        "confidence": 0.9,
                        "evidence": ["backend/main.py", "frontend/src/App.tsx"],
                        "rationale": "Backend and frontend entry points are both present.",
                    }
                ],
                "overrides": [
                    {
                        "target": "project_type",
                        "original_value": "Unknown/mixed repo",
                        "proposed_value": "Full-stack web application",
                        "confidence": 0.9,
                        "evidence": ["backend/main.py", "frontend/src/App.tsx"],
                        "rationale": "The repo contains clear backend and frontend entry points.",
                    }
                ],
            }
        ),
        snapshot,
        fingerprint,
    )

    assert result.mode == "ai-overridden"
    assert result.final_project_type == "Full-stack web application"
    assert result.applied_overrides[0].target == "project_type"


def test_hallucinated_file_path_rejects_override():
    """Overrides citing paths outside the snapshot are rejected."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    result = parse_ai_fusion_response(
        response(
            {
                "summary": "Suspicious path.",
                "overrides": [
                    {
                        "target": "project_type",
                        "original_value": "Unknown/mixed repo",
                        "proposed_value": "Backend API",
                        "confidence": 0.95,
                        "evidence": ["backend/missing.py", "backend/main.py"],
                        "rationale": "References a missing file.",
                    }
                ],
            }
        ),
        snapshot,
        fingerprint,
    )

    assert result.final_project_type == "Unknown/mixed repo"
    assert result.report is not None
    assert result.report.overrides[0].status == "rejected"


def test_missing_evidence_downgrades_override_to_disagreement():
    """Uncited overrides are kept as disagreements rather than applied."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    result = parse_ai_fusion_response(
        response(
            {
                "summary": "No evidence supplied.",
                "overrides": [
                    {
                        "target": "project_type",
                        "original_value": "Unknown/mixed repo",
                        "proposed_value": "Backend API",
                        "confidence": 0.95,
                        "evidence": [],
                        "rationale": "The model guessed without citations.",
                    }
                ],
            }
        ),
        snapshot,
        fingerprint,
    )

    assert result.final_project_type == "Unknown/mixed repo"
    assert result.report is not None
    assert result.report.overrides[0].status == "disagreement"


def test_ai_cannot_delete_deterministic_routes_or_imports():
    """Facts such as routes/imports are not allowed override targets."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    result = parse_ai_fusion_response(
        response(
            {
                "summary": "Attempts to change facts.",
                "overrides": [
                    {
                        "target": "routes",
                        "original_value": ["GET /trips"],
                        "proposed_value": [],
                        "confidence": 0.99,
                        "evidence": ["backend/main.py"],
                        "rationale": "Tries to delete deterministic route facts.",
                    }
                ],
            }
        ),
        snapshot,
        fingerprint,
    )

    assert result.report is not None
    assert result.report.overrides[0].status == "rejected"
    assert "Unsupported override target" in result.report.overrides[0].warnings[0]


def test_unsupported_test_execution_claim_is_rejected():
    """Validation rejects AI claims that tests passed without execution."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    result = parse_ai_fusion_response(
        AssistantResponse(
            status="invalid",
            response_text="",
            provider="mock",
            model="mock-model",
            message="Validation failed: Response claims test execution.",
        ),
        snapshot,
        fingerprint,
    )

    assert result.mode == "deterministic"
    assert result.report is not None
    assert result.report.validation_status == "invalid"


def test_mock_provider_runs_ai_fusion_after_deterministic_generation():
    """Mock AI provider returns schema-valid fusion for the pipeline."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    routes = make_routes()
    reading_path = make_reading_path()
    component_cards = generate_component_cards(snapshot, fingerprint, routes)
    result = run_ai_fusion(
        provider=MockAssistantProvider(),
        snapshot=snapshot,
        fingerprint=fingerprint,
        routes=routes,
        import_edges=[
            ImportEdge(
                source="frontend/src/App.tsx",
                target="backend/main.py",
                kind="inferred",
                confidence=0.4,
            )
        ],
        reading_path=reading_path,
        component_cards=component_cards,
    )

    assert result.is_ai_enhanced
    assert result.report is not None
    assert result.report.provider == "mock"


def test_disabled_provider_keeps_deterministic_result():
    """Disabled AI still produces a deterministic fallback result."""
    snapshot = make_snapshot()
    fingerprint = make_fingerprint()
    result = run_ai_fusion(
        provider=DisabledAssistantProvider(),
        snapshot=snapshot,
        fingerprint=fingerprint,
        routes=make_routes(),
        import_edges=[],
        reading_path=make_reading_path(),
        component_cards=[],
    )

    assert result.mode == "deterministic"
    assert result.final_project_type == fingerprint.project_type


def test_source_change_clears_fused_output():
    """Workspace source changes clear stale fusion outputs."""
    snapshot = make_snapshot()
    other_snapshot = RepositorySnapshot(
        source_name="other",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    workspace = WorkspaceState()
    workspace.source_metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.fused_analysis = parse_ai_fusion_response(
        response({"summary": "ok", "claims": [], "overrides": []}),
        snapshot,
        make_fingerprint(),
    )

    workspace.clear_analysis()
    workspace.source_metadata = SourceMetadata.from_snapshot(other_snapshot, "upload")

    assert workspace.fused_analysis is None


def test_ui_uses_ai_status_is_ready_regression():
    """The Streamlit UI should not compare the AI status object to a string."""
    app_source = Path("app/streamlit_app.py").read_text(encoding="utf-8")

    assert 'ai_status == "ready"' not in app_source
    assert "ai_status.is_ready" in app_source


def test_ai_analyzer_context_pack_call_uses_keywords():
    """The AI Analyzer should not pass work_plan into test_intelligence positionally."""
    app_source = Path("app/streamlit_app.py").read_text(encoding="utf-8")
    call_start = app_source.index("context_pack = build_context_pack(")
    call_end = app_source.index("\n              )", call_start)
    call_text = app_source[call_start:call_end]

    assert "test_intelligence=" in call_text
    assert "work_plan=work_plan" in call_text
