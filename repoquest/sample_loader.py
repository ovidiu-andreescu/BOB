"""Sample repository loader for RepoQuest."""

from pathlib import Path

from repoquest.scanner import scan_directory
from repoquest.models import RepositorySnapshot


def get_demo_repo_path() -> Path:
    """Get the path to the bundled demo repository.
    
    Returns:
        Path to the mini_travel_planner demo repo
    """
    # Get the project root (parent of repoquest package)
    package_dir = Path(__file__).parent
    project_root = package_dir.parent
    
    demo_path = project_root / "examples" / "demo_repos" / "mini_travel_planner"
    
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo repository not found at {demo_path}")
    
    return demo_path


def load_demo_repo() -> RepositorySnapshot:
    """Load and scan the bundled demo repository.
    
    Returns:
        RepositorySnapshot of the demo repo
        
    Raises:
        FileNotFoundError: If the demo repo is not found
    """
    demo_path = get_demo_repo_path()
    return scan_directory(demo_path)

# Made with Bob