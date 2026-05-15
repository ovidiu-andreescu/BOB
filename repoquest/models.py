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

# Made with Bob
