"""Generate a suggested reading path for repository onboarding."""

from repoquest.models import (
    RepositorySnapshot,
    ProjectFingerprint,
    FileInfo,
    ReadingPathItem,
)
from repoquest.config import MAX_READING_PATH_ITEMS


def _calculate_file_priority(file_info: FileInfo, fingerprint: ProjectFingerprint) -> tuple[int, int]:
    """Calculate priority for a file in the reading path.
    
    Returns:
        Tuple of (category_priority, subcategory_priority) where lower is higher priority
    """
    role = file_info.role
    path_lower = file_info.path.lower()
    name_lower = file_info.name.lower()
    
    # Category priorities (lower = read first)
    # 0: Documentation
    # 1: Backend entry points
    # 2: Backend routes
    # 3: Backend services
    # 4: Backend models
    # 5: Frontend entry points
    # 6: Frontend pages
    # 7: API clients
    # 8: Frontend components
    # 9: Tests
    # 10: Config
    # 99: Other
    
    if name_lower == "readme.md":
        return (0, 0)
    
    if role == "documentation":
        return (0, 1)
    
    if role == "entrypoint":
        # Backend entry points first
        if "backend" in path_lower or name_lower in ("main.py", "app.py"):
            return (1, 0)
        # Frontend entry points
        return (5, 0)
    
    if role == "backend_route":
        return (2, 0)
    
    if role == "backend_service":
        return (3, 0)
    
    if role == "model":
        return (4, 0)
    
    if role == "frontend_page":
        return (6, 0)
    
    if role == "api_client":
        return (7, 0)
    
    if role == "frontend_component":
        # Prioritize important-sounding components
        if any(keyword in name_lower for keyword in ["search", "form", "card", "list"]):
            return (8, 0)
        return (8, 1)
    
    if role == "test":
        return (9, 0)
    
    if role == "config":
        return (10, 0)
    
    return (99, 0)


def _estimate_reading_minutes(file_info: FileInfo) -> int:
    """Estimate how many minutes to spend reading a file."""
    # Base estimate on line count and role
    lines = file_info.line_count
    
    # Documentation is quick to skim
    if file_info.role == "documentation":
        return min(3, max(1, lines // 50))
    
    # Config files are quick
    if file_info.role == "config":
        return 1
    
    # Entry points deserve more time
    if file_info.role == "entrypoint":
        return min(5, max(2, lines // 30))
    
    # Routes, services, models - moderate time
    if file_info.role in ("backend_route", "backend_service", "model"):
        return min(4, max(2, lines // 40))
    
    # Frontend files - moderate time
    if file_info.role in ("frontend_page", "frontend_component", "api_client"):
        return min(4, max(2, lines // 40))
    
    # Tests - quick skim
    if file_info.role == "test":
        return min(3, max(1, lines // 50))
    
    # Default
    return min(3, max(1, lines // 50))


def _generate_reading_reason(file_info: FileInfo, fingerprint: ProjectFingerprint) -> str:
    """Generate a reason why this file should be read."""
    role = file_info.role
    name = file_info.name
    path = file_info.path
    
    if name.lower() == "readme.md":
        return "Start here to understand the project's purpose and setup"
    
    if role == "documentation":
        return "Provides context and documentation for the project"
    
    if role == "entrypoint":
        if "backend" in path.lower() or name in ("main.py", "app.py"):
            return "Main backend entry point - shows how the API server is configured"
        if "frontend" in path.lower():
            return "Main frontend entry point - shows how the UI is initialized"
        return "Application entry point - shows how the app starts"
    
    if role == "backend_route":
        return "Defines API endpoints - this is where frontend requests enter the backend"
    
    if role == "backend_service":
        return "Contains business logic and data processing"
    
    if role == "model":
        return "Defines data structures and schemas used throughout the app"
    
    if role == "frontend_page":
        return "Main UI page - shows how users interact with the app"
    
    if role == "api_client":
        return "Handles communication between frontend and backend"
    
    if role == "frontend_component":
        return "Reusable UI component - shows how the interface is built"
    
    if role == "test":
        return "Test file - shows expected behavior and edge cases"
    
    if role == "config":
        return "Configuration file - shows project dependencies and settings"
    
    return "Important file for understanding the codebase"


def generate_reading_path(
    snapshot: RepositorySnapshot,
    fingerprint: ProjectFingerprint,
) -> list[ReadingPathItem]:
    """Generate a suggested 30-minute reading path for onboarding.
    
    Args:
        snapshot: The repository snapshot
        fingerprint: The project fingerprint
        
    Returns:
        List of ReadingPathItem objects in suggested reading order
    """
    # Filter to non-skipped files
    candidates = [f for f in snapshot.files if not f.skipped]
    
    # Sort by priority
    candidates.sort(key=lambda f: _calculate_file_priority(f, fingerprint))
    
    # Build reading path
    reading_path = []
    total_minutes = 0
    target_minutes = 30
    
    for file_info in candidates:
        if len(reading_path) >= MAX_READING_PATH_ITEMS:
            break
        
        # Stop if we've exceeded target time (but always include at least 3 items)
        if total_minutes >= target_minutes and len(reading_path) >= 3:
            break
        
        minutes = _estimate_reading_minutes(file_info)
        reason = _generate_reading_reason(file_info, fingerprint)
        
        reading_path.append(ReadingPathItem(
            order=len(reading_path) + 1,
            path=file_info.path,
            reason=reason,
            estimated_minutes=minutes,
        ))
        
        total_minutes += minutes
    
    return reading_path

# Made with Bob
