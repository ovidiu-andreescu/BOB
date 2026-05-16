"""Tests for workspace state management."""

from datetime import datetime

from repoquest.workspace_state import (
    WorkspaceState,
    SourceMetadata,
    detect_source_change,
    handle_source_change,
    get_workspace_export_metadata,
)
from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
)
from repoquest.assistant_models import (
    AssistantRunResult,
    AssistantRequest,
    AssistantResponse,
)


def test_source_metadata_from_snapshot():
    """Test creating source metadata from a snapshot."""
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    
    assert metadata.source_name == "test-repo"
    assert metadata.source_type == "demo"
    assert metadata.file_count == 8
    assert len(metadata.source_id) == 16  # SHA256 hash truncated to 16 chars
    assert isinstance(metadata.timestamp, datetime)


def test_source_metadata_stable_id():
    """Test that same snapshot produces same source_id."""
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata1 = SourceMetadata.from_snapshot(snapshot, "demo")
    metadata2 = SourceMetadata.from_snapshot(snapshot, "demo")
    
    assert metadata1.source_id == metadata2.source_id


def test_source_metadata_different_for_different_sources():
    """Test that different snapshots produce different source_ids."""
    snapshot1 = RepositorySnapshot(
        source_name="test-repo-1",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    snapshot2 = RepositorySnapshot(
        source_name="test-repo-2",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata1 = SourceMetadata.from_snapshot(snapshot1, "demo")
    metadata2 = SourceMetadata.from_snapshot(snapshot2, "demo")
    
    assert metadata1.source_id != metadata2.source_id


def test_workspace_state_initialization():
    """Test workspace state initializes with empty values."""
    workspace = WorkspaceState()
    
    assert workspace.source_metadata is None
    assert workspace.snapshot is None
    assert workspace.fingerprint is None
    assert workspace.routes == []
    assert workspace.import_edges == []
    assert workspace.assistant_outputs == {}
    assert not workspace.has_analysis()


def test_workspace_state_has_analysis():
    """Test has_analysis returns True when snapshot and fingerprint exist."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    fingerprint = ProjectFingerprint(
        project_type="Test Project",
        confidence=0.9,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Test summary",
        warnings=[],
    )
    
    workspace.snapshot = snapshot
    workspace.fingerprint = fingerprint
    
    assert workspace.has_analysis()


def test_workspace_state_is_stale():
    """Test stale detection when source changes."""
    workspace = WorkspaceState()
    
    snapshot1 = RepositorySnapshot(
        source_name="test-repo-1",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    snapshot2 = RepositorySnapshot(
        source_name="test-repo-2",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata1 = SourceMetadata.from_snapshot(snapshot1, "demo")
    metadata2 = SourceMetadata.from_snapshot(snapshot2, "demo")
    
    workspace.source_metadata = metadata1
    
    assert workspace.is_stale(metadata2)
    assert not workspace.is_stale(metadata1)


def test_workspace_state_clear_analysis():
    """Test clearing analysis preserves source metadata."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    workspace.snapshot = snapshot
    workspace.quiz_answers = {0: "answer"}
    workspace.assistant_outputs = {"test": "output"}
    
    workspace.clear_analysis()
    
    assert workspace.source_metadata == metadata  # Preserved
    assert workspace.snapshot is None
    assert workspace.quiz_answers == {}
    assert workspace.assistant_outputs == {}


def test_workspace_state_clear_all():
    """Test clearing everything including source metadata."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    workspace.snapshot = snapshot
    
    workspace.clear_all()
    
    assert workspace.source_metadata is None
    assert workspace.snapshot is None


def test_detect_source_change_no_previous():
    """Test source change detection with no previous source."""
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    changed, new_metadata = detect_source_change(None, snapshot, "demo")
    
    assert not changed  # No previous source, so not a "change"
    assert new_metadata.source_name == "test-repo"


def test_detect_source_change_same_source():
    """Test source change detection with same source."""
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    current_metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    changed, new_metadata = detect_source_change(current_metadata, snapshot, "demo")
    
    assert not changed
    assert new_metadata.source_id == current_metadata.source_id


def test_detect_source_change_different_source():
    """Test source change detection with different source."""
    snapshot1 = RepositorySnapshot(
        source_name="test-repo-1",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    snapshot2 = RepositorySnapshot(
        source_name="test-repo-2",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    current_metadata = SourceMetadata.from_snapshot(snapshot1, "demo")
    changed, new_metadata = detect_source_change(current_metadata, snapshot2, "demo")
    
    assert changed
    assert new_metadata.source_id != current_metadata.source_id


def test_handle_source_change_clears_stale():
    """Test that handle_source_change clears stale analysis."""
    workspace = WorkspaceState()
    
    snapshot1 = RepositorySnapshot(
        source_name="test-repo-1",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    snapshot2 = RepositorySnapshot(
        source_name="test-repo-2",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata1 = SourceMetadata.from_snapshot(snapshot1, "demo")
    metadata2 = SourceMetadata.from_snapshot(snapshot2, "demo")
    
    workspace.source_metadata = metadata1
    workspace.snapshot = snapshot1
    workspace.quiz_answers = {0: "answer"}
    
    handle_source_change(workspace, metadata2)
    
    assert workspace.source_metadata == metadata2
    assert workspace.snapshot is None  # Cleared
    assert workspace.quiz_answers == {}  # Cleared


def test_get_workspace_export_metadata():
    """Test export metadata generation."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    workspace.assistant_outputs = {"test": "output"}
    
    export_meta = get_workspace_export_metadata(workspace)
    
    assert export_meta["source_name"] == "test-repo"
    assert export_meta["source_type"] == "demo"
    assert export_meta["source_id"] == metadata.source_id
    assert export_meta["file_count"] == 8
    assert export_meta["has_ai_outputs"] is True
    assert export_meta["ai_output_count"] == 1


def test_get_workspace_export_metadata_no_source():
    """Test export metadata with no source."""
    workspace = WorkspaceState()
    
    export_meta = get_workspace_export_metadata(workspace)
    
    assert export_meta == {}


def test_workspace_state_to_dict():
    """Test workspace state serialization."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    workspace.snapshot = snapshot
    
    state_dict = workspace.to_dict()
    
    assert state_dict["source_metadata"] == metadata
    assert state_dict["snapshot"] == snapshot
    assert state_dict["source_type"] == "demo"  # Legacy compatibility


def test_workspace_state_from_session_state():
    """Test workspace state deserialization."""
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    
    session_state = {
        "source_metadata": metadata,
        "snapshot": snapshot,
        "quiz_answers": {0: "answer"},
    }
    
    workspace = WorkspaceState.from_session_state(session_state)
    
    assert workspace.source_metadata == metadata
    assert workspace.snapshot == snapshot
    assert workspace.quiz_answers == {0: "answer"}


def test_assistant_outputs_tied_to_source():
    """Test that assistant outputs are tied to source_id."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    
    # Create assistant result with source_id
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    response = AssistantResponse(
        status="ok",
        response_text="Test response",
    )
    
    result = AssistantRunResult(
        section_id="test",
        section_title="Test",
        request=request,
        response=response,
        source_id=metadata.source_id,
    )
    
    workspace.assistant_outputs["test"] = result
    
    # Get outputs for current source
    outputs = workspace.get_assistant_outputs_for_source()
    
    assert "test" in outputs
    assert outputs["test"].source_id == metadata.source_id


def test_assistant_outputs_filtered_by_source():
    """Test that assistant outputs are filtered by source_id."""
    workspace = WorkspaceState()
    
    snapshot = RepositorySnapshot(
        source_name="test-repo",
        files=[],
        total_files_seen=10,
        total_files_scanned=8,
        warnings=[],
    )
    
    metadata = SourceMetadata.from_snapshot(snapshot, "demo")
    workspace.source_metadata = metadata
    
    # Create assistant result with correct source_id
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    response = AssistantResponse(
        status="ok",
        response_text="Test response",
    )
    
    result1 = AssistantRunResult(
        section_id="test1",
        section_title="Test 1",
        request=request,
        response=response,
        source_id=metadata.source_id,
    )
    
    result2 = AssistantRunResult(
        section_id="test2",
        section_title="Test 2",
        request=request,
        response=response,
        source_id="different_source_id",
    )
    
    workspace.assistant_outputs["test1"] = result1
    workspace.assistant_outputs["test2"] = result2
    
    # Get outputs for current source
    outputs = workspace.get_assistant_outputs_for_source()
    
    assert "test1" in outputs
    assert "test2" not in outputs  # Filtered out


# Made with Bob
