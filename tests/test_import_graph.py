"""Tests for import graph parsing."""

from repoquest.sample_loader import load_demo_repo
from repoquest.import_graph import build_import_graph


def test_demo_repo_import_graph():
    """Test that import graph includes expected edges from demo repo."""
    # Load demo repo
    snapshot = load_demo_repo()
    
    # Build import graph
    edges = build_import_graph(snapshot.files, "")
    
    # Convert to set of (source, target) tuples for easier checking
    edge_pairs = {(e.source, e.target) for e in edges}
    
    # Expected frontend edges
    expected_frontend = [
        ("frontend/src/main.tsx", "frontend/src/App.tsx"),
        ("frontend/src/App.tsx", "frontend/src/pages/TripsPage.tsx"),
        ("frontend/src/pages/TripsPage.tsx", "frontend/src/components/TripCard.tsx"),
        ("frontend/src/pages/TripsPage.tsx", "frontend/src/components/SearchForm.tsx"),
        ("frontend/src/pages/TripsPage.tsx", "frontend/src/services/api.ts"),
    ]
    
    # Expected backend edges
    expected_backend = [
        ("backend/main.py", "backend/routes/trips.py"),
        ("backend/routes/trips.py", "backend/services/recommendations.py"),
        ("backend/routes/trips.py", "backend/models/trip.py"),
        ("backend/tests/test_trips.py", "backend/main.py"),
    ]
    
    # Check frontend edges
    for source, target in expected_frontend:
        assert (source, target) in edge_pairs, f"Missing frontend edge: {source} -> {target}"
    
    # Check backend edges
    for source, target in expected_backend:
        assert (source, target) in edge_pairs, f"Missing backend edge: {source} -> {target}"
    
    # Verify we have both Python and JS/TS imports
    python_edges = [e for e in edges if e.kind == "python_import"]
    ts_edges = [e for e in edges if e.kind == "ts_import"]
    
    assert len(python_edges) > 0, "Should have Python imports"
    assert len(ts_edges) > 0, "Should have TypeScript imports"
    
    print(f"✓ Found {len(edges)} total import edges")
    print(f"✓ Found {len(python_edges)} Python imports")
    print(f"✓ Found {len(ts_edges)} TypeScript imports")
    print("✓ All expected edges present")


def test_import_graph_excludes_external_packages():
    """Test that external packages are excluded from the graph."""
    snapshot = load_demo_repo()
    edges = build_import_graph(snapshot.files, "")
    
    # Check that no edges point to external packages
    external_packages = ["react", "fastapi", "pydantic", "uvicorn"]
    
    for edge in edges:
        for pkg in external_packages:
            assert pkg not in edge.target.lower(), f"Should not include external package: {pkg}"
    
    print("✓ No external packages in graph")

# Made with Bob
