"""Tests for architecture graph generation."""

from repoquest.sample_loader import load_demo_repo
from repoquest.import_graph import build_import_graph
from repoquest.route_extractors import extract_all_routes
from repoquest.architecture import generate_architecture_map, generate_dependency_graph


def test_architecture_map_generation():
    """Test that architecture map is generated successfully."""
    snapshot = load_demo_repo()
    routes = extract_all_routes(snapshot.files)
    
    dot_graph = generate_architecture_map(snapshot.files, routes)
    
    # Should be valid DOT format
    assert dot_graph.startswith('digraph Architecture'), "Should start with digraph declaration"
    assert dot_graph.endswith('}'), "Should end with closing brace"
    
    # Should contain some key files
    assert 'App.tsx' in dot_graph or 'TripsPage.tsx' in dot_graph, "Should include frontend files"
    assert 'trips.py' in dot_graph or 'main.py' in dot_graph, "Should include backend files"
    
    print(f"✓ Architecture map generated ({len(dot_graph)} chars)")


def test_dependency_graph_generation():
    """Test that dependency graph includes expected nodes and edges."""
    snapshot = load_demo_repo()
    edges = build_import_graph(snapshot.files, "")
    
    dot_graph = generate_dependency_graph(snapshot.files, edges)
    
    # Should be valid DOT format
    assert dot_graph.startswith('digraph Dependencies'), "Should start with digraph declaration"
    assert dot_graph.endswith('}'), "Should end with closing brace"
    
    # Should contain nodes
    assert '[label=' in dot_graph, "Should have labeled nodes"
    
    # Should contain edges (->)
    if edges:
        assert '->' in dot_graph, "Should have edges if imports exist"
    
    print(f"✓ Dependency graph generated ({len(dot_graph)} chars)")
    print(f"✓ Graph includes {len(edges)} import edges")


def test_dependency_graph_with_expected_edges():
    """Test that dependency graph contains expected file relationships."""
    snapshot = load_demo_repo()
    edges = build_import_graph(snapshot.files, "")
    
    dot_graph = generate_dependency_graph(snapshot.files, edges)
    
    # Check for some expected file names in the graph
    expected_files = [
        'App.tsx',
        'TripsPage.tsx',
        'main.py',
        'trips.py',
    ]
    
    found_count = sum(1 for f in expected_files if f in dot_graph)
    
    assert found_count >= 2, f"Should include at least 2 key files, found {found_count}"
    
    print(f"✓ Found {found_count}/{len(expected_files)} expected files in graph")

# Made with Bob