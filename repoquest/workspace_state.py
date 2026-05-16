"""Workspace state management for RepoQuest UI.

This module handles:
- Source metadata tracking (ID, timestamp, type, name)
- Stale state detection when source changes
- Assistant output association with source snapshots
- Workspace state persistence and clearing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import hashlib

from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    RouteInfo,
    ImportEdge,
    ReadingPathItem,
    ComponentCard,
    QuizQuestion,
    WorkPlan,
    TestIntelligence,
)
from repoquest.assistant_models import AssistantRunResult


@dataclass
class SourceMetadata:
    """Metadata about the currently analyzed source."""
    
    source_id: str  # Unique ID for this source snapshot
    source_name: str  # Display name
    source_type: str  # "demo" or "upload"
    timestamp: datetime  # When analysis was generated
    file_count: int  # Number of files scanned
    
    @classmethod
    def from_snapshot(cls, snapshot: RepositorySnapshot, source_type: str) -> "SourceMetadata":
        """Create source metadata from a repository snapshot."""
        # Generate stable ID from source name and file count
        id_input = f"{snapshot.source_name}:{snapshot.total_files_scanned}:{source_type}"
        source_id = hashlib.sha256(id_input.encode()).hexdigest()[:16]
        
        return cls(
            source_id=source_id,
            source_name=snapshot.source_name,
            source_type=source_type,
            timestamp=datetime.utcnow(),
            file_count=snapshot.total_files_scanned,
        )


@dataclass
class WorkspaceState:
    """Complete workspace state for a RepoQuest analysis session."""
    
    # Source metadata
    source_metadata: SourceMetadata | None = None
    
    # Core analysis results
    snapshot: RepositorySnapshot | None = None
    fingerprint: ProjectFingerprint | None = None
    routes: list[RouteInfo] = field(default_factory=list)
    import_edges: list[ImportEdge] = field(default_factory=list)
    
    # Generated artifacts
    arch_map: str | None = None
    dep_graph: str | None = None
    reading_path: list[ReadingPathItem] = field(default_factory=list)
    component_cards: list[ComponentCard] = field(default_factory=list)
    quiz: list[QuizQuestion] = field(default_factory=list)
    work_plan: WorkPlan | None = None
    test_intelligence: TestIntelligence | None = None
    
    # Generated documents
    generated_doc: str | None = None
    work_plan_md: str | None = None
    
    # UI state
    quiz_answers: dict[int, str] = field(default_factory=dict)
    quiz_submitted: bool = False
    quiz_current_question: int = 0
    
    # Assistant outputs (tied to source_id)
    assistant_outputs: dict[str, AssistantRunResult] = field(default_factory=dict)
    
    def is_stale(self, new_source_metadata: SourceMetadata) -> bool:
        """Check if current state is stale compared to new source."""
        if self.source_metadata is None:
            return False
        
        # Different source ID means stale
        return self.source_metadata.source_id != new_source_metadata.source_id
    
    def clear_analysis(self) -> None:
        """Clear all analysis results but keep source metadata."""
        self.snapshot = None
        self.fingerprint = None
        self.routes = []
        self.import_edges = []
        self.arch_map = None
        self.dep_graph = None
        self.reading_path = []
        self.component_cards = []
        self.quiz = []
        self.work_plan = None
        self.test_intelligence = None
        self.generated_doc = None
        self.work_plan_md = None
        self.quiz_answers = {}
        self.quiz_submitted = False
        self.quiz_current_question = 0
        self.assistant_outputs = {}
    
    def clear_all(self) -> None:
        """Clear everything including source metadata."""
        self.source_metadata = None
        self.clear_analysis()
    
    def has_analysis(self) -> bool:
        """Check if workspace has analysis results."""
        return self.snapshot is not None and self.fingerprint is not None
    
    def get_assistant_outputs_for_source(self) -> dict[str, AssistantRunResult]:
        """Get assistant outputs for current source only."""
        if self.source_metadata is None:
            return {}
        
        # Filter outputs that match current source
        return {
            key: result
            for key, result in self.assistant_outputs.items()
            if hasattr(result, 'source_id') and result.source_id == self.source_metadata.source_id
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Convert workspace state to dictionary for session state."""
        return {
            "source_metadata": self.source_metadata,
            "snapshot": self.snapshot,
            "fingerprint": self.fingerprint,
            "routes": self.routes,
            "import_edges": self.import_edges,
            "arch_map": self.arch_map,
            "dep_graph": self.dep_graph,
            "reading_path": self.reading_path,
            "component_cards": self.component_cards,
            "quiz": self.quiz,
            "work_plan": self.work_plan,
            "test_intelligence": self.test_intelligence,
            "generated_doc": self.generated_doc,
            "work_plan_md": self.work_plan_md,
            "quiz_answers": self.quiz_answers,
            "quiz_submitted": self.quiz_submitted,
            "quiz_current_question": self.quiz_current_question,
            "assistant_outputs": self.assistant_outputs,
            # Legacy compatibility
            "source_type": self.source_metadata.source_type if self.source_metadata else None,
        }
    
    @classmethod
    def from_session_state(cls, session_state: dict[str, Any]) -> "WorkspaceState":
        """Create workspace state from Streamlit session state."""
        return cls(
            source_metadata=session_state.get("source_metadata"),
            snapshot=session_state.get("snapshot"),
            fingerprint=session_state.get("fingerprint"),
            routes=session_state.get("routes", []),
            import_edges=session_state.get("import_edges", []),
            arch_map=session_state.get("arch_map"),
            dep_graph=session_state.get("dep_graph"),
            reading_path=session_state.get("reading_path", []),
            component_cards=session_state.get("component_cards", []),
            quiz=session_state.get("quiz", []),
            work_plan=session_state.get("work_plan"),
            test_intelligence=session_state.get("test_intelligence"),
            generated_doc=session_state.get("generated_doc"),
            work_plan_md=session_state.get("work_plan_md"),
            quiz_answers=session_state.get("quiz_answers", {}),
            quiz_submitted=session_state.get("quiz_submitted", False),
            quiz_current_question=session_state.get("quiz_current_question", 0),
            assistant_outputs=session_state.get("assistant_outputs", {}),
        )


def detect_source_change(
    current_metadata: SourceMetadata | None,
    new_snapshot: RepositorySnapshot,
    new_source_type: str,
) -> tuple[bool, SourceMetadata]:
    """
    Detect if source has changed and return new metadata.
    
    Returns:
        (source_changed, new_metadata)
    """
    new_metadata = SourceMetadata.from_snapshot(new_snapshot, new_source_type)
    
    if current_metadata is None:
        return (False, new_metadata)
    
    source_changed = current_metadata.source_id != new_metadata.source_id
    return (source_changed, new_metadata)


def handle_source_change(workspace: WorkspaceState, new_metadata: SourceMetadata) -> None:
    """Handle source change by clearing stale analysis."""
    if workspace.is_stale(new_metadata):
        workspace.clear_analysis()
    
    workspace.source_metadata = new_metadata


def get_workspace_export_metadata(workspace: WorkspaceState) -> dict[str, Any]:
    """Get metadata for export bundle."""
    if workspace.source_metadata is None:
        return {}
    
    return {
        "source_name": workspace.source_metadata.source_name,
        "source_type": workspace.source_metadata.source_type,
        "source_id": workspace.source_metadata.source_id,
        "analysis_timestamp": workspace.source_metadata.timestamp.isoformat(),
        "file_count": workspace.source_metadata.file_count,
        "has_ai_outputs": len(workspace.assistant_outputs) > 0,
        "ai_output_count": len(workspace.assistant_outputs),
    }


# Made with Bob
