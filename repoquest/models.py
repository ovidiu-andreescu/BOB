"""Data models for RepoQuest."""

from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a scanned file."""
    path: str
    name: str
    suffix: str
    size_bytes: int
    language: str
    role: str
    text_preview: str
    line_count: int
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class RepositorySnapshot:
    """Snapshot of a scanned repository."""
    source_name: str
    files: list[FileInfo]
    total_files_seen: int
    total_files_scanned: int
    warnings: list[str]


@dataclass
class ImportEdge:
    """Represents an import relationship between files."""
    source: str
    target: str
    kind: str  # "python_import", "js_import", "ts_import"
    confidence: float


@dataclass
class RouteInfo:
    """Information about a detected API route."""
    framework: str  # "fastapi", "flask", "express"
    method: str  # "GET", "POST", "DELETE", etc.
    path: str  # "/trips", "/trips/{trip_id}"
    file_path: str
    function_name: str | None = None


@dataclass
class FrameworkFinding:
    """Information about a detected framework."""
    name: str
    category: str  # "frontend", "backend", "testing", "tooling"
    confidence: float  # 0.0 to 1.0
    evidence: list[str]


@dataclass
class ProjectFingerprint:
    """High-level classification of a repository."""
    project_type: str
    confidence: float  # 0.0 to 1.0
    frameworks: list[FrameworkFinding]
    entry_points: list[str]
    key_folders: list[str]
    summary: str
    warnings: list[str]


@dataclass
class ReadingPathItem:
    """An item in the suggested reading path."""
    order: int
    path: str
    reason: str
    estimated_minutes: int


@dataclass
class ComponentCard:
    """Detailed information card for an important file/component."""
    path: str
    title: str
    role: str
    why_it_matters: str
    connected_to: list[str]
    detected_items: list[str]
    suggested_test_ideas: list[str]
    suggested_bob_prompt: str


@dataclass
class QuizQuestion:
    """A quiz question for onboarding verification."""
    question: str
    options: list[str]
    correct_answer: str
    explanation: str

# Made with Bob
