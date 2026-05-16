"""Tests for reading path generation."""


from repoquest.sample_loader import load_demo_repo
from repoquest.detectors import generate_fingerprint
from repoquest.reading_path import generate_reading_path
from repoquest.models import RepositorySnapshot, ProjectFingerprint


def test_reading_path_starts_with_readme():
    """Test that reading path starts with README.md for demo repo."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    assert len(reading_path) > 0
    assert reading_path[0].path.endswith("README.md")
    assert reading_path[0].order == 1


def test_reading_path_includes_backend_route():
    """Test that reading path includes a backend route file."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    # Should include backend/routes/trips.py
    route_paths = [item.path for item in reading_path if "routes" in item.path.lower()]
    assert len(route_paths) > 0


def test_reading_path_includes_frontend_file():
    """Test that reading path includes a frontend entry or page file."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    # Should include frontend files like App.tsx or pages
    frontend_paths = [
        item.path for item in reading_path 
        if "frontend" in item.path.lower() and item.path.endswith((".tsx", ".jsx"))
    ]
    assert len(frontend_paths) > 0


def test_reading_path_has_estimated_minutes():
    """Test that each reading path item has estimated minutes."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    for item in reading_path:
        assert item.estimated_minutes > 0
        assert item.estimated_minutes <= 5  # Reasonable upper bound


def test_reading_path_has_reasons():
    """Test that each reading path item has a reason."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    for item in reading_path:
        assert item.reason
        assert len(item.reason) > 10  # Should be a meaningful reason


def test_reading_path_respects_max_items():
    """Test that reading path respects MAX_READING_PATH_ITEMS limit."""
    from repoquest.config import MAX_READING_PATH_ITEMS
    
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    assert len(reading_path) <= MAX_READING_PATH_ITEMS


def test_reading_path_orders_correctly():
    """Test that reading path items are ordered correctly."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    # Check that order numbers are sequential
    for i, item in enumerate(reading_path):
        assert item.order == i + 1


def test_reading_path_prioritizes_backend_before_frontend():
    """Test that backend files generally come before frontend files."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    # Find first backend and first frontend file (excluding README)
    backend_index = None
    frontend_index = None
    
    for i, item in enumerate(reading_path):
        if "backend" in item.path.lower() and backend_index is None:
            backend_index = i
        if "frontend" in item.path.lower() and frontend_index is None:
            frontend_index = i
    
    # If both exist, backend should come first
    if backend_index is not None and frontend_index is not None:
        assert backend_index < frontend_index


def test_reading_path_skips_skipped_files():
    """Test that reading path does not include skipped files."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    # Get all paths in reading path
    reading_paths = {item.path for item in reading_path}
    
    # Check that no skipped files are in the reading path
    for file_info in snapshot.files:
        if file_info.skipped:
            assert file_info.path not in reading_paths


def test_reading_path_empty_snapshot():
    """Test reading path generation with empty snapshot."""
    snapshot = RepositorySnapshot(
        source_name="empty",
        files=[],
        total_files_seen=0,
        total_files_scanned=0,
        warnings=[],
    )
    fingerprint = ProjectFingerprint(
        project_type="Unknown",
        confidence=0.0,
        frameworks=[],
        entry_points=[],
        key_folders=[],
        summary="Empty repository",
        warnings=[],
    )
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    assert len(reading_path) == 0


def test_reading_path_total_time_reasonable():
    """Test that total reading time is reasonable (around 30 minutes)."""
    snapshot = load_demo_repo()
    fingerprint = generate_fingerprint(snapshot)
    
    reading_path = generate_reading_path(snapshot, fingerprint)
    
    total_minutes = sum(item.estimated_minutes for item in reading_path)
    
    # Should be roughly 30 minutes, give or take
    assert 15 <= total_minutes <= 45

# Made with Bob
