"""Repository scanner for RepoQuest."""

import os
import zipfile
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
from repoquest.zip_safety import (
    validate_zip_file,
    is_safe_zip_path,
    safe_read_zip_entry,
    ZIPSafetyError,
)


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


def should_skip_zip_entry(entry_name: str, entry_size: int) -> tuple[bool, str | None]:
    """Check if a ZIP entry should be skipped. Returns (should_skip, reason)."""
    # Check if it's a directory
    if entry_name.endswith("/"):
        return True, "Directory entry"
    
    # Check extension
    suffix = Path(entry_name).suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return True, f"Binary file ({suffix})"
    
    # Check size
    if entry_size > MAX_FILE_SIZE_BYTES:
        return True, f"File too large ({entry_size} bytes)"
    
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


def extract_text_preview_from_bytes(content_bytes: bytes) -> tuple[str, int]:
    """Extract text preview and line count from bytes."""
    try:
        content = content_bytes[:MAX_TEXT_PREVIEW_CHARS].decode("utf-8", errors="replace")
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


def scan_zip(zip_path: Path) -> RepositorySnapshot:
    """Scan a ZIP file and return a repository snapshot.
    
    Args:
        zip_path: Path to the ZIP file
        
    Returns:
        RepositorySnapshot with scanned files and warnings
        
    Raises:
        ZIPSafetyError: If the ZIP fails safety validation
    """
    # Validate ZIP safety first
    validate_zip_file(zip_path)
    
    files: list[FileInfo] = []
    warnings: list[str] = []
    total_seen = 0
    total_scanned = 0
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for entry in zf.namelist():
                total_seen += 1
                
                if total_scanned >= MAX_FILES_SCANNED:
                    warnings.append(f"Reached max file limit ({MAX_FILES_SCANNED}). Some files were not scanned.")
                    break
                
                # Check path safety
                is_safe, safety_reason = is_safe_zip_path(entry)
                if not is_safe:
                    warnings.append(f"Skipped unsafe path '{entry}': {safety_reason}")
                    continue
                
                # Check if path should be ignored
                if should_ignore_path(entry):
                    continue
                
                # Get entry info
                try:
                    info = zf.getinfo(entry)
                except KeyError:
                    warnings.append(f"Cannot access ZIP entry '{entry}'")
                    continue
                
                # Check if should skip
                should_skip, skip_reason = should_skip_zip_entry(entry, info.file_size)
                
                entry_path = Path(entry)
                suffix = entry_path.suffix.lower()
                language = LANGUAGE_MAP.get(suffix, "Unknown")
                
                if should_skip:
                    files.append(FileInfo(
                        path=entry,
                        name=entry_path.name,
                        suffix=suffix,
                        size_bytes=info.file_size,
                        language=language,
                        role="skipped",
                        text_preview="",
                        line_count=0,
                        skipped=True,
                        skip_reason=skip_reason,
                    ))
                    continue
                
                # Read and process file content
                try:
                    content_bytes = safe_read_zip_entry(zf, entry, MAX_FILE_SIZE_BYTES)
                    text_preview, line_count = extract_text_preview_from_bytes(content_bytes)
                    role = guess_file_role(entry_path)
                    
                    files.append(FileInfo(
                        path=entry,
                        name=entry_path.name,
                        suffix=suffix,
                        size_bytes=info.file_size,
                        language=language,
                        role=role,
                        text_preview=text_preview,
                        line_count=line_count,
                        skipped=False,
                        skip_reason=None,
                    ))
                    
                    total_scanned += 1
                except ZIPSafetyError as e:
                    warnings.append(f"Cannot read '{entry}': {e}")
                    continue
    
    except zipfile.BadZipFile as e:
        raise ZIPSafetyError(f"Corrupted ZIP file: {e}")
    except Exception as e:
        if isinstance(e, ZIPSafetyError):
            raise
        raise ZIPSafetyError(f"ZIP scanning failed: {e}")
    
    return RepositorySnapshot(
        source_name=zip_path.name,
        files=files,
        total_files_seen=total_seen,
        total_files_scanned=total_scanned,
        warnings=warnings,
    )

# Made with Bob