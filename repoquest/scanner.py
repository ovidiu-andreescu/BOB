"""Repository scanner for RepoQuest."""

import os
from pathlib import Path

from repoquest.config import (
    IGNORE_FOLDERS,
    SKIP_EXTENSIONS,
    LANGUAGE_MAP,
    MAX_FILES_SCANNED,
    MAX_FILE_SIZE_BYTES,
    MAX_TEXT_PREVIEW_CHARS,
)
from repoquest.models import FileInfo, RepositorySnapshot


def should_ignore_path(path: str) -> bool:
    """Check if a path should be ignored during scanning."""
    parts = Path(path).parts
    return any(part in IGNORE_FOLDERS for part in parts)


def should_skip_file(file_path: Path) -> tuple[bool, str | None]:
    """Check if a file should be skipped. Returns (should_skip, reason)."""
    suffix = file_path.suffix.lower()
    
    if suffix in SKIP_EXTENSIONS:
        return True, f"Binary file ({suffix})"
    
    try:
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            return True, f"File too large ({size} bytes)"
    except OSError:
        return True, "Cannot access file"
    
    return False, None


def extract_text_preview(file_path: Path) -> tuple[str, int]:
    """Extract text preview and line count from a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_TEXT_PREVIEW_CHARS)
            line_count = content.count("\n") + 1
            return content, line_count
    except Exception:
        return "", 0


def guess_file_role(file_path: Path) -> str:
    """Guess the role of a file based on its path and name."""
    path_str = str(file_path).lower()
    name = file_path.name.lower()
    
    # Documentation
    if name in ("readme.md", "readme.txt", "readme"):
        return "documentation"
    
    # Configuration
    if name in ("package.json", "requirements.txt", "pyproject.toml", "vite.config.ts", "vite.config.js"):
        return "config"
    
    # Entry points
    if name in ("main.py", "app.py", "index.js", "index.ts", "app.tsx", "app.jsx"):
        return "entrypoint"
    
    # Tests
    if "test" in path_str or name.startswith("test_"):
        return "test"
    
    # Frontend components
    if "component" in path_str and file_path.suffix in (".tsx", ".jsx"):
        return "frontend_component"
    
    # Frontend pages
    if "page" in path_str and file_path.suffix in (".tsx", ".jsx"):
        return "frontend_page"
    
    # API/services
    if "service" in path_str or "api" in path_str:
        if file_path.suffix in (".ts", ".js"):
            return "api_client"
        return "backend_service"
    
    # Routes
    if "route" in path_str:
        return "backend_route"
    
    # Models
    if "model" in path_str:
        return "model"
    
    return "unknown"


def scan_directory(directory: Path) -> RepositorySnapshot:
    """Scan a directory and return a repository snapshot."""
    files: list[FileInfo] = []
    warnings: list[str] = []
    total_seen = 0
    total_scanned = 0
    
    for root, dirs, filenames in os.walk(directory):
        # Remove ignored directories from traversal
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]
        
        for filename in filenames:
            total_seen += 1
            
            if total_scanned >= MAX_FILES_SCANNED:
                warnings.append(f"Reached max file limit ({MAX_FILES_SCANNED}). Some files were not scanned.")
                break
            
            file_path = Path(root) / filename
            
            if should_ignore_path(str(file_path)):
                continue
            
            should_skip, skip_reason = should_skip_file(file_path)
            
            suffix = file_path.suffix.lower()
            language = LANGUAGE_MAP.get(suffix, "Unknown")
            
            if should_skip:
                files.append(FileInfo(
                    path=str(file_path.relative_to(directory)),
                    name=filename,
                    suffix=suffix,
                    size_bytes=0,
                    language=language,
                    role="skipped",
                    text_preview="",
                    line_count=0,
                    skipped=True,
                    skip_reason=skip_reason,
                ))
                continue
            
            text_preview, line_count = extract_text_preview(file_path)
            size_bytes = file_path.stat().st_size
            role = guess_file_role(file_path)
            
            files.append(FileInfo(
                path=str(file_path.relative_to(directory)),
                name=filename,
                suffix=suffix,
                size_bytes=size_bytes,
                language=language,
                role=role,
                text_preview=text_preview,
                line_count=line_count,
                skipped=False,
                skip_reason=None,
            ))
            
            total_scanned += 1
        
        if total_scanned >= MAX_FILES_SCANNED:
            break
    
    return RepositorySnapshot(
        source_name=directory.name,
        files=files,
        total_files_seen=total_seen,
        total_files_scanned=total_scanned,
        warnings=warnings,
    )

# Made with Bob
