"""Load bundled demo repositories."""

from pathlib import Path

from repoquest.scanner import scan_directory
from repoquest.models import RepositorySnapshot


def get_demo_repo_path() -> Path:
    """Get the path to the bundled demo repository."""
    # Get the path relative to this file
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    demo_path = project_root / "examples" / "demo_repos" / "mini_travel_planner"
    return demo_path


def load_demo_repo() -> RepositorySnapshot:
    """Load and scan the bundled demo repository."""
    demo_path = get_demo_repo_path()
    
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo repository not found at {demo_path}")
    
    return scan_directory(demo_path)

# Made with Bob
